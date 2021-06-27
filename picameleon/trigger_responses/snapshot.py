import io
from time import sleep
from datetime import datetime
from streamers.streamer import ROOT_PATH, Streamer
from utils.single_picamera import SinglePiCamera
from .base import BaseTriggerResponse


class Snapshot(BaseTriggerResponse):
    def __init__(self, port, format, destination_path,
                 use_detrigger=False, **capture_options):
        super().__init__(use_detrigger=use_detrigger)
        self.format = format
        self.capture_options = capture_options
        self.destination_path = destination_path if destination_path.startswith(
            "/") else ROOT_PATH + destination_path
        self.camera = SinglePiCamera()

    def _trigger_response(self, trigger_args={}):
        now = datetime.now()
        Streamer.take_picture(self.destination_path + now.strftime("%Y-%m-%d_%H-%M-%S") + "." + self.format,
                              format=self.format, **self.capture_options)
