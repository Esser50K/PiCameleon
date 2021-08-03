[<img src="picameleon.png" width="500"/>](picameleon.png)

# PiCameleon

Is a daemon program meant to provide the RaspberryPi Camera as a service while running according to a configuration.

## Motivation

The RaspberryPi Camera can only be used by one process at a time. This can be very limiting when you need a camera feed from the camera to be used by many other programs or want to take pictures while some other program is using it.

However the camera has 4 ports that can be used simultaneously by the same process, this feature is exposed by the [picamera](https://github.com/waveform80/picamera) library.

The feature is leveraged in this project to allow communication with the camera that would be difficult without it such as:
- requesting multiple streams at multiple qualities
- send video streams to multiple clients for processing
- requesting videos to be recorded or pictures to be taken while streaming
- detect motion continuosly and trigger camera features like snapshot and recording to file or even sending pictures to other services over http

## Quick Usage Walkthrough

The program runs according to a configuration.

The configuration is separated into 3 sections: `camera_initialization_options`, `modes` and `trigger_responses`

The `camera_initialization_options` is where you can specify the arguments to be passed to the `PiCamera` object from the picamera library, these are passed directly to the contructor.

The `modes` is where you can specify the operation modes in which the camera should run. These `modes` can be found in the [modes](picameleon/modes) folder.
One can run the same mode with multiple configurations. The modes also run according to a certain schedule defined by a start and stop cron condition. These `schedules` can be found in the [schedules](picameleon/schedules) folder, but you can also write your own. The `modes` also have their own parameters that you can specify in the `modes_config` section for each instance.

Some modes (such as the [motion_detection](picameleon/modes/motion_detection.py)) can trigger. This means an action can be configured in response to it. The responses can be found in the [trigger_responses](picameleon/trigger_responses) folder. These have their own configuration section as they can have their own parameters. Some examples from these are [record_to_file](picameleon/trigger_responses/record_to_file.py), [snapshot](picameleon/trigger_responses/snapshot.py) and also triggering external services over [http](picameleon/trigger_responses/http.py).

Example configurations can be found in the [configs](picameleon/configs) folder.

## Build

Build the container locally (takes a while but should be accelerated through piwheels):

```
docker build -t picameleon:latest .
```

in case you are building it for the raspberrypi zero you need to specify the correct Dockerfile:

```
docker build -t picameleon:latest -f Dockerfile.zero .
```


## Deployment

Launching the daemon in a Docker container is supported and also recommended. There are two Dockerfiles which only differ in their base image to support the RaspberryPi Zero and all the other versions of the Pi.

For the container to be able to access the camera however it has to run with these special flags: `--privileged -v /opt/vc:/opt/vc --env LD_LIBRARY_PATH=/opt/vc/lib`.

Full Example:

```
docker run -d --name picameleon --privileged -v /opt/vc:/opt/vc --env LD_LIBRARY_PATH=/opt/vc/lib -e CONFIG_FILE=stream_server_config.json picameleon:latest
```

## Client Installation

PiCameleon includes a client package that can be installed on pretty much any system with:

```
pip3 install picameleon
```

Examples on how to use it can be found in the [examples](examples) folder.

Feel free to make suggestions on how to improve the API and submit feature requests.