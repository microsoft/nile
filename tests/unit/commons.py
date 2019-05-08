from typing import List
from typing import Optional
from typing import Tuple

from nile.interfaces import Consumer
from nile.interfaces import Device
from nile.interfaces import Transformer


class DummyConsumer(Consumer[str]):
    """Simple consumer that collects workloads into a set for later inspection."""

    def __init__(self, consumer_id: str, batch_size: int) -> None:
        self._consumer_id = consumer_id
        self._batch_size = batch_size
        self.batches = []  # type: List[Tuple[str, List[str]]]

    def consumer_id(self) -> str:
        return self._consumer_id

    def consume(self, device_id: str, data: List[str]):
        self.batches.append((device_id, data))

    def batch_size(self) -> int:
        return self._batch_size


class DummyDevice(Device[int]):
    """Simple device that produces integers of increasing magnitude."""

    def __init__(self, device_id) -> None:
        self.index = 0
        self.read_called = 0
        self._device_id = device_id

        # to be used by test classes to control timeout/is_active behavior
        self.should_be_active = False
        self.should_timeout = False

    def device_id(self) -> str:
        return self._device_id

    def read(self, _timeout: int) -> Optional[int]:
        self.read_called += 1
        if self.should_timeout:
            raise Exception('Timeout!')
        if not self.is_active():
            raise Exception('Not Active!')

        self.index += 1
        return self.index

    def start(self) -> None:
        if self.is_active():
            raise Exception('Already active!')
        self.should_be_active = True

    def stop(self) -> None:
        if not self.is_active():
            raise Exception('Not active!')
        self.should_be_active = False

    def more(self) -> bool:
        return True

    def is_active(self) -> bool:
        return self.should_be_active


class DummyTransformer(Transformer[int, str]):
    """Simple transformer that converts int to str."""

    def __init__(self, transformer_id) -> None:
        self._transformer_id = transformer_id

    def transformer_id(self) -> str:
        return self._transformer_id

    def transform(self, data: int) -> str:
        return str(data)
