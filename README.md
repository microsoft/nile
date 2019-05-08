# nile

- [nile](#nile)
  - [About](#about)
  - [Installation](#installation)
  - [Samples](#samples)
  - [Basic Usage](#basic-usage)
  - [Advanced usage](#advanced-usage)
  - [Contributing](#contributing)

## About

[![Build Status](https://travis-ci.org/microsoft/nile.svg?branch=master)](https://travis-ci.org/microsoft/nile/)
[![codecov](https://codecov.io/gh/microsoft/nile/branch/master/graph/badge.svg)](https://codecov.io/gh/microsoft/nile)
[![PyPI version](https://badge.fury.io/py/nile.svg)](https://badge.fury.io/py/nile)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/nile.svg)](https://pypi.org/project/nile/)
[![PyPI - License](https://img.shields.io/pypi/l/nile.svg)](https://pypi.org/project/nile/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/nile.svg)](https://pypi.org/project/nile/)

`nile` is a library that aims to simplify building applications that leverage real time data collected from one or more sensors or media devices. `nile` simplifies this process by implementing the boiler plate code that orchestrates configurations composed of these key abstractions:

- Device abstraction that yields data
- Functional layer to transform data
- Processing layer that applies logic to transformation output

`nile` will handle all device orchestration including wiring up the correct device, transformer and processing layers, managing device lifecycle and cleaning up unused resources.

## Installation

`nile` currently supports Python versions `3.4`, `3.5`, `3.6` and `3.7`. It can be installed by running `pip install nile`.

## Samples

A dockerized sample is included with this repository. In this sample `nile` orchestrates streaming from multiple webcam devices pipes the feeds to a camera-specific set of consumers which print output in a table format to `stdout`. More specifically, the following configurations are used:

- Intersection Webcam
  - Frames converted to grayscale
  - Output piped to ML model that counts vehicals
  - Output piped to brightness detection
- College Campus Webcam
  - Frames converted to grayscale
  - Output piped to brightness detection

The sample can be run locally by running the following commands:

```bash
# clone the repo
git clone https://github.com/microsoft/nile.git
# enter the nile directory
cd nile/
# ensure Docker is running
docker --version
# build the project
docker build . -t nile
# run the samples
docker run nile
```

## Basic Usage

In order to use `nile` you must implement three abstractions ([documentation here](./nile/interfaces.py)):

- `Device`: Represents a data stream adapter to a physical media device. For example you may build separate devices to stream audio from microphone and HTTP endpoints.
- `Transformer`: Transform source data. For example, you may transform an MPEG audio stream into PCM/WAV format.
- `Consumer`: Represents a consumer of the transformed device data. There may be many of these per device. For example, in an audio-streaming application you may build separate consumers to (1) analyze audio wave frequencies, (2) analyze audio wave amplitudes and (3) archive audio onto a cloud-provided storage endpoint.

The samples directory contains real-world implementations that target live webcam video analysis. [Examples can be found here](./samples/videostream/providers.py).

Once you have these you can orchestrate them using `nile`:

```python
from time import sleep
from nile.controllers import DeviceController, DeviceFleetManager
# import your implementations here...

# the controller manages the configuration for a single device
device_controller = DeviceController(
    YourCustomDevice(),
    YourCustomTransformer(),
    (YourCustomDeviceConsumer(),),
    throttle_time_ms=-1     # a positive value specifies the polling delay on the device
)

# the fleet manager handles configurations for multiple devices
fleet_manager = DeviceFleetManager()
fleet_manager.set_controllers({device_controller})

# process for 20 seconds
sleep(20)

# this closes all devices under management and cleans any resources for those devices
fleet_controller.shutdown()
```

## Advanced usage

`nile` supports non-trivial configurations as well and can update in real-time to configuration updates. Here is a more complex orchestration that leverages these features. The source code for the providers can be found [here](./samples/videostream/providers.py):

```python
# example runs brigtness detection on video frames for 20 seconds, and then adds a car count consumer
# to one of the video feeds.
from time import sleep
from nile.controllers import DeviceController, DeviceFleetManager
from providers import BrightnessMeasureConsumer, CarCounterConsumer, FrameToGrayscaleTransformer, HttpVideoCaptureDevice


# ML model to count cars
car_count_consumer = CarCounterConsumer()

# Measure avg. brightness
brightness_measure_consumer = BrightnessMeasureConsumer()

# Convert img to grayscale
image_converter = FrameToGrayscaleTransformer()

road_cam = HttpVideoCaptureDevice('Tennasee Road', 'http://traf3.murfreesborotn.gov/axis-cgi/mjpg/video.cgi')
campus_cam = HttpVideoCaptureDevice('Bowdoin Campus', 'http://webcam1.bowdoin.edu:4200/axis-cgi/mjpg/video.cgi')
fleet_controller = DeviceFleetManager()

# start with both feeds running through brightness measuring
fleet_controller.set_controllers({
    DeviceController(
        device=road_cam,
        transformer=image_converter,
        consumers=(brightness_measure_consumer,),
        throttle_time_ms=-1),
    DeviceController(
        device=campus_cam,
        transformer=image_converter,
        consumers=(brightness_measure_consumer,),
        throttle_time_ms=-1)
})

# process for 20 seconds
sleep(20)

# add car count detection on road cam
fleet_controller.set_controllers({
    DeviceController(
        device=road_cam,
        transformer=image_converter,
        consumers=(brightness_measure_consumer, car_count_consumer),
        throttle_time_ms=-1),
    DeviceController(
        device=campus_cam,
        transformer=image_converter,
        consumers=(brightness_measure_consumer,),
        throttle_time_ms=-1)
})

# process for 20 seconds
sleep(20)

# close devices and clean up all resources
fleet_controller.shutdown()
```

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.microsoft.com.

When you submit a pull request, a CLA-bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., label, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

For additional guidance, refer to the project-specific [contributing guidelines](./.github/CONTRIBUTING.md) as well as the [pull request template](./.github/PULL_REQUEST_TEMPLATE.md)
