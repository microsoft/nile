"""Controllers for managing data streams."""

import logging
import sys
from threading import Lock
from threading import Thread
from time import sleep
from time import time
from typing import Any
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

from .interfaces import Consumer
from .interfaces import Device
from .interfaces import I
from .interfaces import O
from .interfaces import T
from .interfaces import Transformer

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)

if not LOG.handlers:
    LOG.addHandler(logging.StreamHandler(sys.stdout))


class DeviceStreamError(Exception):
    """Indicates a streaming related error has occurred."""


class ConsumerDelegate(Generic[T]):
    """Responsible for batching data elements and submitting workloads to consumers."""

    def __init__(self, device_id: str, consumers: Tuple[Consumer[T], ...]) -> None:
        self.device_id = device_id
        self.consumers = consumers
        self.consumer_batches = {consumer: [] for consumer in consumers}  # type: Dict[Consumer[T], List[T]]

    def enqueue(self, data: T) -> None:
        """Enqueue work items for consumers. If any consumer work queue is full, the work will be dispatched."""

        for consumer, work_queue in self.consumer_batches.items():
            work_queue.append(data)
            if len(work_queue) == consumer.batch_size():
                self._submit_to_consumer(consumer)
                work_queue.clear()

    def _submit_to_consumer(self, consumer: Consumer) -> None:
        """Submit a copy of the data to the consumer."""
        work_queue = self.consumer_batches[consumer][:]
        consumer_id = consumer.consumer_id()

        try:
            LOG.debug('submitting batch of size %d to consumer %s', len(work_queue), consumer_id)
            consumer.consume(self.device_id, work_queue)
        except Exception:
            LOG.exception('error processing workload in consumer %s', consumer_id)


class DeviceController(Generic[I, O]):
    """
    Controller class that orchestrates the streaming daemon thread which manages a
    conurrent queue of data frames sourced from the configured dataStream.
    """
    def __init__(
            self,
            device: Device[I],
            transformer: Transformer[I, O],
            consumers: Tuple[Consumer[O], ...],
            throttle_time_ms: int) -> None:
        self.device = device
        self.transformer = transformer
        self.delegate = ConsumerDelegate(device.device_id(), consumers)
        self.throttle_time_ms = throttle_time_ms
        self.background_thread = None  # type: Optional[Thread]
        self.lock = Lock()
        self.data_frame_counter = 0

    def __hash__(self) -> int:
        """
        Returns object hash. __hash__ and __eq__ are used to determine whether or not two DeviceController instances
        are logically equivelant. Equivelant in this case means that all of the underlying dependencies (instance IDs,
        throttle rate, etc...) are the same. Instances that meet this criteria can be considered functionally
        equivelant.
        """
        return hash(self.get_data_for_hash_and_eq())

    def __eq__(self, other: Any) -> bool:
        """Refer to __hash__ documentation."""
        return isinstance(other, DeviceController) and hash(self) == hash(other)

    def get_data_for_hash_and_eq(self) -> Tuple[str, ...]:
        """
        Collection of IDs and other data that are what determine whether or not this controller is equal to another.

        The order of the IDs returned is as follows:
            - device ID
            - transformer ID
            - throttle time
            - consumer IDs
        """
        ids = []  # type: List[str]
        ids.append(self.transformer.transformer_id())
        ids.append(self.device.device_id())
        ids.append(str(self.throttle_time_ms))

        for consumer in self.delegate.consumers:
            ids.append(consumer.consumer_id())

        return tuple(ids)

    @property
    def is_active(self) -> bool:
        """Probe underlying media device to see if it is active."""
        return self.device.is_active()

    def start_streaming(self) -> None:
        """
        Starts the worker thread that's responsible for collecting the video frames
        from the configured camera
        """
        with self.lock:
            if self.is_active:
                raise DeviceStreamError('cannot start an already started device')

            if self.background_thread is not None:
                raise DeviceStreamError('cannot start device with an already active background thread')

            self.device.start()
            self.background_thread = Thread(target=self._run)
            self.background_thread.daemon = True
            self.background_thread.start()

    def stop_streaming(self) -> None:
        """Stops and releases the video stream."""
        executed_stop_command = False
        with self.lock:
            if not self.is_active:
                raise DeviceStreamError('cannot stop an already stopped device')

            if self.background_thread is None:
                raise DeviceStreamError('cannot stop device if background thread is not initialized')

            self.device.stop()
            executed_stop_command = True

        # stop outside of lock to prevent a deadlock
        if executed_stop_command:
            self.background_thread.join()
            self.background_thread = None

    def _run(self) -> None:
        """
        Background processing method responsible for collecting data from the underlying device
        and handing off to underlying processing layers.

        In the case the device is disconnected, the underlying data source will be stopped and released.
        """
        while True:
            if self.throttle_time_ms > 0:
                sleep(self.throttle_time_ms / 1000)

            input_data = None
            with self.lock:
                if not self.is_active:
                    LOG.info('Exiting _run() because the device has been closed')
                    return

                if not self.device.more():
                    continue

                try:
                    start = time()
                    input_data = self.device.read(self.throttle_time_ms)
                    LOG.debug('data capture completed in %dms', time() - start)
                except Exception:
                    LOG.exception('error invoking read() on device')
                    continue

            if input_data is not None:
                try:
                    start = time()
                    output_data = self.transformer.transform(input_data)
                    LOG.debug('data transformation completed in %dms', time() - start)
                except Exception:
                    LOG.exception('error invoking transform() with data %s', input_data)
                    continue

                try:
                    start = time()
                    self.delegate.enqueue(output_data)
                    LOG.debug('data handling completed in %dms', time() - start)
                except Exception:
                    LOG.exception('error invoking transform() with data %s', input_data)
                    continue


class DeviceFleetManager():
    """Orchestrate a fleet of DeviceController objects."""

    def __init__(self):
        self.controllers = set()  # type: Set[DeviceController]
        self.lock = Lock()

    def set_controllers(self, controllers: Set[DeviceController]) -> None:
        """
        Update the managed controllers to a new set.

        Any new controllers will be auto-started. Any controllers currently under management that
        are not called out in the new set will be auto-stopped and removed from management.

        Note: if a controller is added that refers to an existing device under management BUT
        the underlying consumers have changed, this method will cause the device stream to be
        stopped and restarted.
        """
        with self.lock:
            to_remove = self.controllers - controllers
            to_add = controllers - self.controllers

            # note: order of these calls is important, as if a device is configured with a different
            # controller then it is important to remove the old controller before adding a new controller
            # in order to ensure that the device ends up in a streaming state.
            self._handle_removing_old_controllers(to_remove)
            self._handle_adding_new_controllers(to_add)

    def shutdown(self) -> None:
        """Stop streaming and managing all devices."""
        self.set_controllers(set())

    def _handle_adding_new_controllers(self, controllers: Set[DeviceController]) -> None:
        for controller in controllers:
            if not controller.is_active:
                controller.start_streaming()
            self.controllers.add(controller)

    def _handle_removing_old_controllers(self, controllers: Set[DeviceController]) -> None:
        for controller in controllers:
            if controller.is_active:
                controller.stop_streaming()
            self.controllers.remove(controller)
