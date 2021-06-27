"""
Generic Streamer Class that returns one of the implementations of base_streamer.
It also works as a multi-singleton class as it will only create new Streamer instances if they have a new output format or resolution
Different outputs can be appended to the same streamer instance.

If the formats "h264" or "mjpeg" are set then it will return a SplitFrameStreamer which streams a frame at a time.
All other formats return an instance of BaseStreamer which produces raw streams.
"""
import os
from .base import BaseStreamer
from .split_frame import SplitFrameStreamer
from utils.single_picamera import SinglePiCamera
from threading import Lock

ROOT_PATH = '{0}/../'.format(os.path.dirname(os.path.abspath(__file__)))
SPLIT_FRAME_FORMATS = ("mjpeg", "h264")


def get_streamer_instance(port, format, prepend_size, split_frames, recording_options):
    if split_frames:
        return SplitFrameStreamer(port, format, prepend_size, options=recording_options)
    else:
        return BaseStreamer(port, format, options=recording_options)


def ordered_dict_hash(dictionary):
    ordered_keys = sorted(dictionary.keys())
    to_hash = ""
    for key in ordered_keys:
        to_hash += str(key) + str(dictionary[key])
    return hash(to_hash)


class Streamer:
    _lock = Lock()
    _capture_lock = Lock()
    _available_ports = [0, 1, 2, 3]
    _picture_port = None
    _streamers = {}
    _portmap = {}
    _pic_holder = {}

    def __new__(cls, format,
                id_output=(None, None),
                id_motion_output=(None, None),
                prepend_size=False,
                split_frames=True,
                recording_options=None):
        with cls._lock:
            if recording_options is None:
                recording_options = {"resize": SinglePiCamera().resolution}
            elif "resize" not in recording_options.keys():
                recording_options = {"resize": SinglePiCamera().resolution, **recording_options}

            resolution = recording_options["resize"]
            res_str = "_".join(map(str, resolution))
            port_key = "%s_%s_%s_%s" % (format, res_str, str(split_frames), ordered_dict_hash(recording_options))
            outID, output = id_output[0], id_output[1]
            moutID, motion_output = id_motion_output[0], id_motion_output[1]
            if port_key in cls._streamers.keys():
                streamer = cls._streamers[port_key]
                if output:
                    streamer.output.add_output(outID, output)
                if motion_output:
                    streamer.motion_output.add_output(moutID, motion_output)
                return streamer

            # Try cleaning up streamers and recovering ports
            elif len(cls._available_ports) == 0:
                raise Exception("No more camera ports available for new streamer")

            port = cls._available_ports.pop(0)
            new_streamer = get_streamer_instance(
                port, format, prepend_size, split_frames, recording_options)
            if output and outID:
                new_streamer.output.add_output(outID, output)
            if motion_output and moutID:
                new_streamer.motion_output.add_output(moutID, motion_output)

            cls._streamers[port_key] = new_streamer
            cls._portmap[port] = port_key
            new_streamer._callback = cls._return_port_availability
            return new_streamer

    @classmethod
    def shutdown_streamers(cls):
        keys = [key for key in cls._streamers.keys()]
        for streamerId in keys:
            cls._streamers[streamerId].stop()
            cls._streamers[streamerId].shutdown()


    @classmethod
    def get_available_ports(cls):
        with cls._lock:
            return cls._available_ports

    @classmethod
    def _get_picture_port(cls):
        """Picture ports can be reused between components as they don't need
        constant hold on it as video recorders do.
        """
        with cls._lock:
            if cls._picture_port is not None:
                return cls._picture_port

            if len(cls._available_ports) > 0:
                cls._picture_port = cls._available_ports.pop(0)

            return cls._picture_port

    @classmethod
    def _return_port_availability(cls, port):
        with cls._lock:
            if port in cls._portmap:
                port_key = cls._portmap[port]
                del cls._portmap[port]
                del cls._streamers[port_key]
                cls._available_ports.append(port)
            elif port == cls._picture_port:
                cls._available_ports.append(port)
                cls._picture_port = None

    @classmethod
    def take_picture(cls, output, format="jpeg", **capture_options):
        """Picture ports can be reused between components that have the same
        requirements as they don't need constant hold on it as video recorders do.
        """
        with cls._capture_lock:
            port = cls._get_picture_port()
            if port is not None:
                SinglePiCamera().capture(output,
                                         splitter_port=port,
                                         format=format,
                                         use_video_port=True,
                                         **capture_options)
                cls._return_port_availability(port)
