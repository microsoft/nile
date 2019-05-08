import unittest
from typing import List
from typing import Tuple
from unittest.mock import MagicMock

from nile.controllers import DeviceController
from nile.controllers import DeviceFleetManager

from .commons import DummyConsumer
from .commons import DummyDevice
from .commons import DummyTransformer


class TestDeviceFleetManager(unittest.TestCase):
    def setUp(self):
        self.device_1 = DummyDevice('device:1')
        self.device_2 = DummyDevice('device:2')
        self.fleet_manager = DeviceFleetManager()

    def tearDown(self):
        self.fleet_manager.set_controllers(set())

    def test_set_controllers_initial(self):
        controllers = set()
        controllers.add(self._mk_controller(self.device_1, [('consumer:1', 1)]))

        self.fleet_manager.set_controllers(controllers)
        self.assertTrue(self.device_1.is_active())
        self.assertEqual(controllers, self.fleet_manager.controllers)

    def test_set_controllers_handles_remove(self):
        controllers = set()
        controllers.add(self._mk_controller(self.device_1, [('consumer:1', 1)]))

        self.fleet_manager.set_controllers(controllers)
        self.fleet_manager.set_controllers(set())
        self.assertFalse(self.device_1.is_active())
        self.assertEqual(set(), self.fleet_manager.controllers)

    def test_set_controller_with_different_device(self):
        # different devices should result in change in consumers
        controllers_1 = set()
        controllers_2 = set()

        controllers_1.add(self._mk_controller(self.device_1, [('consumer:1', 1)]))
        controllers_2.add(self._mk_controller(self.device_2, [('consumer:1', 1)]))

        self.fleet_manager.set_controllers(controllers_1)
        self.fleet_manager.set_controllers(controllers_2)

        self.assertFalse(self.device_1.is_active())
        self.assertTrue(self.device_2.is_active())
        self.assertEqual(controllers_2, self.fleet_manager.controllers)

    def test_set_controllers_with_same_device_but_diff_consumers(self):
        # different consumers should result in change in consumers
        controllers_1 = set()
        controllers_2 = set()

        controllers_1.add(self._mk_controller(self.device_1, [('consumer:1', 1)]))
        controllers_2.add(self._mk_controller(self.device_1, [('consumer:2', 2)]))

        self.fleet_manager.set_controllers(controllers_1)
        self.fleet_manager.set_controllers(controllers_2)

        self.assertTrue(self.device_1.is_active())
        self.assertEqual(controllers_2, self.fleet_manager.controllers)

    def test_set_controllers_obeys_controller_hash_and_eq(self):
        controller_1 = MagicMock()
        controller_1.__eq__.return_value = True
        controller_1.__hash__.return_value = 123

        controller_2 = MagicMock()
        controller_2.__eq__.return_value = True
        controller_2.__hash__.return_value = 123

        self.fleet_manager.set_controllers(set([controller_1]))
        self.fleet_manager.set_controllers(set([controller_2]))

        self.assertEqual(1, len(self.fleet_manager.controllers))

        # verify that the ID of the object under fleet management is the first one. this
        # proves that controller_1 did not get replaced with the logically equivelant
        # controller_2
        controller_under_management = next(iter(self.fleet_manager.controllers))
        self.assertEqual(id(controller_1), id(controller_under_management))

    def _mk_controller(self, device: DummyDevice, consumer_configs: List[Tuple[str, int]]) -> DeviceController:
        consumers = tuple(
            DummyConsumer(consumer_id, batch_size)
            for (consumer_id, batch_size) in consumer_configs
        )
        return DeviceController(device, DummyTransformer('transformer:1'), consumers, 1)
