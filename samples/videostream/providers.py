"""Implementations of nile interfaces."""

from threading import Lock
from typing import List
from typing import Optional

import cv2
import numpy as np
from nile.interfaces import Consumer
from nile.interfaces import Device
from nile.interfaces import Transformer


class HttpVideoCaptureDevice(Device[bytes]):
    """Wrapper around OpenCV to stream camera feeds."""

    def __init__(self, cam_name: str, camera_endpoint: str) -> None:
        self.cam_name = cam_name
        self.camera_endpoint = camera_endpoint
        self.capture = None  # type: Optional[cv2.VideoCapture]

    def device_id(self) -> str:
        """URL of camera feed."""
        return self.cam_name

    def start(self) -> None:
        """Start streaming."""
        self.capture = cv2.VideoCapture(self.camera_endpoint)

    def read(self, _timeout: int) -> Optional[np.ndarray]:
        """Read data frame with timeout."""
        if not self.capture:
            raise Exception('capture device not initialized')
        ret, img = self.capture.read()
        return None if not ret else img

    def stop(self) -> None:
        """Stop streaming data."""
        if not self.capture:
            raise Exception('capture device not initialized')
        self.capture.release()

    def is_active(self) -> bool:
        """True if active, False otherwise."""
        return self.capture is not None and self.capture.isOpened()

    def more(self) -> bool:
        """True if data is available to be read, false otherwise."""
        return True


class FrameToGrayscaleTransformer(Transformer[np.ndarray, np.ndarray]):
    """Transformers camera frame to .jpg."""

    def __init__(self) -> None:
        self.lock = Lock()

    def transformer_id(self) -> str:
        """Since all instances are the same, the ID can be same for all instances."""
        return FrameToGrayscaleTransformer.__name__

    def transform(self, image: np.ndarray) -> np.ndarray:
        """Transform image to JPG format."""
        with self.lock:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


class CarCounterConsumer(Consumer[np.ndarray]):
    """Applies car count over a grayscale imgae."""

    def __init__(self) -> None:
        self.car_detect_model = cv2.CascadeClassifier('/samples/cars.xml')
        self.lock = Lock()

    def consumer_id(self) -> str:
        """Since all instances are the same, the ID can be same for all instances."""
        return CarCounterConsumer.__name__

    def batch_size(self) -> int:
        """Batch size for object detection. This model relies on a processing 5 frames at a time."""
        return 5

    def consume(self, device_id: str, data: List[np.ndarray]) -> None:
        """Run object detection on image."""
        counts = []
        for image in data:
            try:
                with self.lock:
                    counts.append(len(self.car_detect_model.detectMultiScale(image, 1.1, 1)))
            except Exception:
                pass

        car_count = int(sum(counts) / len(counts)) if counts else '?'
        print("| {} | {} | {} |".format(device_id.center(20), '# Cars'.center(20), str(car_count).center(20)))


class BrightnessMeasureConsumer(Consumer[np.ndarray]):
    """Measure image brightness."""

    def consumer_id(self) -> str:
        """Since all instances are the same, the ID can be same for all instances."""
        return BrightnessMeasureConsumer.__name__

    def consume(self, device_id: str, data: List[np.ndarray]) -> None:
        """Measure average brightness of frame, measured as a value between 0% and 100%."""
        brigtness = int(100 * np.mean(data) / 255)
        print("| {} | {} | {} |".format(
            device_id.center(20), 'Avg Brigtness'.center(20), (str(brigtness) + '%').center(20)))

    def batch_size(self) -> int:
        """Measure avg brigtness over 10 frames."""
        return 10
