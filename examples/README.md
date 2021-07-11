# Examples

In this folder you'll find a picameleon configuration
to get your instance running with certain capabilitites.

These are then used in the examples by the client.

## fetch_and_display_bgr

The [exmaple](fetch_and_display_bgr.py) shows how to request resized frames from picameleon in the bgr format.
The fetched images can then be displayed with opencv.

## fetch_and_display_jpg

The result of this [example](fetch_and_display_jpg.py) is quite similar to the one of`fetch_and_display_bgr`.
However, in this one it is shown how to attach custom outputs to the stream being fetched.

## trigger_video_capture

This [example](trigger_video_capture.py) simply triggers the picameleon instance
running the `network_trigger` mode. The (config)[picameleon_config.json] shows
that the trigger will start a video recording (the results stays on the picameleon instance).

## serve_and_display_jpg

The  [serve_and_display_jpg](serve_and_display_jpg.py) example shows how to use the server function of the client
(confusing I know..). Basically, PiCameleon can be configured to run in `netowrk_streaming` mode in which it tries to actively
connect to a client to serve a stream. If you're not running the client on the raspberryPi running PiCameleon then make sure to
change the host in the [config file](picameleon_config.json) under the `netowrk_streaming` section.