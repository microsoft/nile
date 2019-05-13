import unittest

from nile.controllers import ConsumerDelegate

from .commons import DummyConsumer


class TestConsumerDelegate(unittest.TestCase):
    def setUp(self):
        self.batch_of_1 = DummyConsumer('consumer:1', 1)
        self.batch_of_2 = DummyConsumer('consumer:2', 2)
        self.batch_of_3 = DummyConsumer('consumer:3', 3)

        self.delegate = ConsumerDelegate('device:1', (
            self.batch_of_1,
            self.batch_of_2,
            self.batch_of_3
        ))

    def test_batch_size_obeyed(self):
        for i in range(10):
            self.delegate.enqueue(str(i))

        self.assertEqual(
            self.batch_of_1.batches,
            [
                ('device:1', ["0"]),
                ('device:1', ["1"]),
                ('device:1', ["2"]),
                ('device:1', ["3"]),
                ('device:1', ["4"]),
                ('device:1', ["5"]),
                ('device:1', ["6"]),
                ('device:1', ["7"]),
                ('device:1', ["8"]),
                ('device:1', ["9"])])

        self.assertEqual(
            self.batch_of_2.batches,
            [
                ('device:1', ["0", "1"]),
                ('device:1', ["2", "3"]),
                ('device:1', ["4", "5"]),
                ('device:1', ["6", "7"]),
                ('device:1', ["8", "9"])
            ])

        self.assertEqual(
            self.batch_of_3.batches,
            [
                ('device:1', ["0", "1", "2"]),
                ('device:1', ["3", "4", "5"]),
                ('device:1', ["6", "7", "8"])
            ])
