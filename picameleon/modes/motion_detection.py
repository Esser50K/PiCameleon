"""
The Motion Detection mode.

It uses the SplitFrameStreamer with the mjpeg format to
continuously capture and compare images.

When motion is detected it will use the configured trigger response.
"""

from .base import BaseMode
from outputs.motion_detector import MotionDetector, OUTPUT_ID
from utils.single_picamera import SinglePiCamera
from streamers.streamer import Streamer


class MotionDetectionMode(BaseMode):
    def __init__(self, config, trigger_responses):
        super().__init__(config, trigger_responses)
        self.name = "motion_detection"
        self.recording_options = config["recording_options"] if "recording_options" in config else {}

        self.streamer = Streamer("h264", recording_options=self.recording_options)
        # TODO: Add Motion Detector Configs
        if self.streamer.motion_output.has_output(OUTPUT_ID):
            self.motion_detector = self.streamer.motion_output.get_output(OUTPUT_ID)
        else:
            self.motion_detector = MotionDetector()
            self.streamer.motion_output.add_output(OUTPUT_ID, self.motion_detector)

    def pre_routine(self):
        self.motion_detector.calibrate()

    def routine(self):
        # Wait until motion is detected
        if self.motion_detector.wait_for_motion(5):
            self.trigger_all()
            # Wait until motion is no longer detected
            while not self.motion_detector.calibrate(no_motion_seconds=5):
                pass
            self.detrigger_all()

    def _cleanup(self):
        self.streamer.motion_output.remove_output(OUTPUT_ID)
