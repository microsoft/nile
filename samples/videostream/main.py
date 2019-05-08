"""Leverage nile package to analyze audio feeds from webcams."""
from time import sleep

from providers import BrightnessMeasureConsumer
from providers import CarCounterConsumer
from providers import FrameToGrayscaleTransformer
from providers import HttpVideoCaptureDevice
from nile.controllers import DeviceController
from nile.controllers import DeviceFleetManager

# http://www.opentopia.com/webcam/12229
TENNASEE_WEBCAM = ('Tennasee Road', 'http://traf3.murfreesborotn.gov/axis-cgi/mjpg/video.cgi')

# http://www.opentopia.com/webcam/1745
BOWDOIN_WEBCAM = ('Bowdoin Campus', 'http://webcam1.bowdoin.edu:4200/axis-cgi/mjpg/video.cgi')


def run():
    """
    Demo will instantiate a new fleet controller which will orchestrate the following:
        - Orchesrate device implementations for each video stream
        - Pass video frames through a greyscale conversion
        - For road camera - detect cars and measure brigtness
        - For campus camera - measure brightness
    """
    # this wraps a machine learning model for counting cars
    car_count_consumer = CarCounterConsumer()

    # this measures average brigtness
    brightness_measure_consumer = BrightnessMeasureConsumer()

    # this will handle greyscale conversion
    image_converter = FrameToGrayscaleTransformer()

    # street crossing camera
    road_cam = HttpVideoCaptureDevice(TENNASEE_WEBCAM[0], TENNASEE_WEBCAM[1])

    # college quad camera
    campus_cam = HttpVideoCaptureDevice(BOWDOIN_WEBCAM[0], BOWDOIN_WEBCAM[1])

    # run vehical count and brightness measure consumers for the street cam
    road_cam_controller = DeviceController(
        device=road_cam,
        transformer=image_converter,
        consumers=(car_count_consumer, brightness_measure_consumer),
        throttle_time_ms=-1)

    # run brightness measure consumer for the campus cam
    campus_cam_controller = DeviceController(
        device=campus_cam,
        transformer=image_converter,
        consumers=(brightness_measure_consumer,),
        throttle_time_ms=-1)

    # this controlls the fleet of webcam devices
    fleet_controller = DeviceFleetManager()

    # this delegates controller management to the fleet controller
    fleet_controller.set_controllers({road_cam_controller, campus_cam_controller})
    sleep(30)

    # close devices and clean up all resources
    fleet_controller.shutdown()

if __name__ == '__main__':
    run()
