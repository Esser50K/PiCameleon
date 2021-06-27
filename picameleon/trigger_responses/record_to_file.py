import os
from time import sleep, time
from datetime import datetime
from utils.single_picamera import SinglePiCamera
from streamers.streamer import Streamer, ROOT_PATH
from .base import BaseTriggerResponse
from picamerax import PiCameraCircularIO
from threading import Thread


FILE_BUFFER = 1048576


class RecordToFile(BaseTriggerResponse):
    def __init__(self, format, destination_path,
                 record_time_before_trigger, record_time_after_trigger,
                 recording_options={}, use_detrigger=True, file_buffer=FILE_BUFFER):
        super().__init__(use_detrigger=use_detrigger)
        self.format = format
        self.recording_options = recording_options
        self.seconds_before = int(record_time_before_trigger)
        self.seconds_after = int(record_time_after_trigger)
        self.destination_path = destination_path
        self.file_buffer = file_buffer
        self.before_buffer = None
        self.streamer = None
        self.is_triggered = False

    def _initialize_trigger_response(self):
        self.streamer = Streamer(
            self.format, split_frames=False, recording_options=self.recording_options)
        self.before_buffer = PiCameraCircularIO(
            SinglePiCamera(), seconds=self.seconds_before, splitter_port=self.streamer.port)
        self.streamer.output = self.before_buffer
        self.streamer.start()

    def _trigger_response(self, trigger_args=None):
        # Mutliple modes can use this trigger response.
        # Don't record for more than 1 trigger response
        if not self.is_triggered:
            self.is_triggered = True
            if not os.path.exists(self.destination_path):
                os.makedirs(self.destination_path)

            now = datetime.now()
            path = "{d}/{t}.{f}".format(d=self.destination_path,
                                        t=now.strftime("%Y-%m-%d_%H-%M"), f=self.format)
            outputfile = open(path, mode="wb", buffering=self.file_buffer)
            self.before_buffer.copy_to(outputfile, seconds=self.seconds_before)
            self.streamer.split_recording(outputfile)

            # Wait until triggered to stop
            if self.use_detrigger:
                self.detrigger_event.wait()
                self.detrigger_event.clear()

            # Still record X seconds after detrigger
            self.streamer.wait_recording(self.seconds_after)
            self.before_buffer.clear()
            self.streamer.split_recording(self.before_buffer)
            outputfile.close()
            self.is_triggered = False

    def _cleanup_trigger_response(self):
        self.streamer.stop()
        self.before_buffer.clear()
