import unittest
from time import sleep

from nile.controllers import DeviceController
from nile.controllers import DeviceStreamError

from .commons import DummyConsumer
from .commons import DummyDevice
from .commons import DummyTransformer


class TestDeviceController(unittest.TestCase):
    def setUp(self):
        self.consumer_1 = DummyConsumer('consumer:1', 1)
        self.consumer_2 = DummyConsumer('consumer:2', 2)
        self.device = DummyDevice('device:1')

        self.controller = DeviceController(
            self.device,
            DummyTransformer('transformer:1'),
            [self.consumer_1, self.consumer_2],
            1
        )

    def tearDown(self):
        try:
            self.controller.stop_streaming()
        except DeviceStreamError:
            pass

    def test_start_actually_starts_device(self):
        self.controller.start_streaming()
        self.assertTrue(self.device.is_active())

    def test_stop_actually_stops_device(self):
        self.controller.start_streaming()
        self.controller.stop_streaming()
        self.assertFalse(self.device.is_active())

    def test_stop_fails_if_never_started(self):
        with self.assertRaises(DeviceStreamError):
            self.controller.stop_streaming()

    def test_stop_fails_if_already_stopped(self):
        self.controller.start_streaming()
        self.controller.stop_streaming()
        with self.assertRaises(DeviceStreamError):
            self.controller.stop_streaming()

    def test_start_fails_if_already_started(self):
        self.controller.start_streaming()
        with self.assertRaises(DeviceStreamError):
            self.controller.start_streaming()

    def test_is_active_delegates_to_device(self):
        self.device.should_be_active = False
        self.assertFalse(self.controller.is_active)

        self.device.should_be_active = True
        self.assertTrue(self.controller.is_active)

    def test_timeout_handled(self):
        self.device.should_timeout = True
        self.controller.start_streaming()
        sleep(1)

        # no exception is considered a pass
        self.assertTrue(self.device.read_called > 0)

    def test_data_delegated_to_device_with_correct_batch_size(self):
        self.controller.start_streaming()
        sleep(1)

        self.assertTrue(self.consumer_1.batches)
        for batch in self.consumer_1.batches:
            self.assertEqual('device:1', batch[0])
            self.assertEqual(1, len(batch[1]))

        self.assertTrue(self.consumer_2.batches)
        for batch in self.consumer_2.batches:
            self.assertEqual('device:1', batch[0])
            self.assertEqual(2, len(batch[1]))

    # the following block of test verify that the __hash__ and __eq__ functions
    # are implemented in a way that does not rely on the default Python object
    # implementation.
    #
    # this is important for this codebase because it allows different instances
    # of device controller to be compared in a logical way so that it becomes easy
    # to detect changes in configuration with simple set arithmetic
    def test_eq_and_hash_for_same_configuration(self):
        self.assertEqual(1, len(set([
            DeviceController(
                DummyDevice('device:1'),
                DummyTransformer('transformer:1'),
                [DummyConsumer('consumer:1', 1)],
                1
            ), DeviceController(
                DummyDevice('device:1'),
                DummyTransformer('transformer:1'),
                [DummyConsumer('consumer:1', 1)],
                1
            )
        ])))

    def test_eq_and_hash_for_different_device(self):
        self.assertEqual(2, len(set([
            DeviceController(
                DummyDevice('device:1'),
                DummyTransformer('transformer:1'),
                [DummyConsumer('consumer:1', 1)],
                1
            ), DeviceController(
                DummyDevice('device:2'),
                DummyTransformer('transformer:1'),
                [DummyConsumer('consumer:1', 1)],
                1
            )
        ])))

    def test_eq_and_hash_for_different_transformer(self):
        self.assertEqual(2, len(set([
            DeviceController(
                DummyDevice('device:1'),
                DummyTransformer('transformer:1'),
                [DummyConsumer('consumer:1', 1)],
                1
            ), DeviceController(
                DummyDevice('device:1'),
                DummyTransformer('transformer:2'),
                [DummyConsumer('consumer:1', 1)],
                1
            )
        ])))

    def test_eq_and_hash_for_different_consumer(self):
        self.assertEqual(2, len(set([
            DeviceController(
                DummyDevice('device:1'),
                DummyTransformer('transformer:1'),
                [DummyConsumer('consumer:1', 1)],
                1
            ), DeviceController(
                DummyDevice('device:1'),
                DummyTransformer('transformer:1'),
                [DummyConsumer('consumer:2', 1)],
                1
            )
        ])))

    def test_eq_and_hash_for_different_throttle_time(self):
        self.assertEqual(2, len(set([
            DeviceController(
                DummyDevice('device:1'),
                DummyTransformer('transformer:1'),
                [DummyConsumer('consumer:1', 1)],
                1
            ), DeviceController(
                DummyDevice('device:1'),
                DummyTransformer('transformer:1'),
                [DummyConsumer('consumer:1', 1)],
                2
            )
        ])))
