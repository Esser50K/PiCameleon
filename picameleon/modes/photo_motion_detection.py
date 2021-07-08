"""
The Photo Motion Detection mode.

It just quickly takes pictures and compares them with the previous ones

When motion is detected it will use the configured trigger response.
"""

import picamerax.array
from .base import BaseMode
from utils.single_picamera import SinglePiCamera
from streamers.streamer import Streamer

WIDTH = 224  # Default Width
HEIGHT = 160  # Default Height
# How Much pixel changes (really depends a lot on exposure_mode and awb_mode, this value seems to be good for default)
THRESHOLD = 100
SENSITIVITY = 50  # How many pixels change
MIN_CERTAINTY = 3  # How often the conditions must apply in a row
MOTION_DETECTOR_DETRIGGER = 5  # Number of pics without motion to detrigger


class PhotoMotionDetection(BaseMode):
    def __init__(self, config: dict, trigger_responses):
        super().__init__(config, trigger_responses)
        self.name = "photo_motion_detection"

        # Motion Detection Parameters
        if "resize" not in config.keys():
            config["resize"] = (WIDTH, HEIGHT)

        self.threshold = config["threshold"] if "threshold" in config else THRESHOLD
        self.sensitivity = config["sensitivity"] if "sensitivity" in config else SENSITIVITY
        self.min_certainty = config["min_certainty"] if "min_certainty" in config else MIN_CERTAINTY
        self.pic_buffer = picamerax.array.PiRGBArray(SinglePiCamera(), size=(config["resize"][0], config["resize"][1]))
        self.prev_pic = None
        self.current_certainty = 0
        self.motion_detected = False
        self.iterations_without_motion = 0

    def get_rgb_pic(self):
        self.pic_buffer.truncate(0)
        Streamer.take_picture(self.pic_buffer, format='rgb', capture_options=self.config)
        return self.pic_buffer.array

    def pre_routine(self):
        # Get first pic to compare to
        self.prev_pic = self.get_rgb_pic()

    def routine(self):
        if self._detect_motion():
            self.motion_detected = True
            self.trigger_all()
            self.iterations_without_motion = 0
        elif self.motion_detected:
            self.iterations_without_motion += 1
            if self.iterations_without_motion >= MOTION_DETECTOR_DETRIGGER:
                self.iterations_without_motion = 0
                self.detrigger_all()
                self.motion_detected = False

    def _detect_motion(self):
        # Take new pic
        new_pic = self.get_rgb_pic()

        # Simple Motion Detection Algorithm
        diff_count = 0
        found_motion_this_pic = False
        for w in range(0, self.config["resize"][0]):
            if found_motion_this_pic:
                break
            for h in range(0, self.config["resize"][1]):
                # get the diff of the pixel. Conversion to int
                # is required to avoid unsigned short overflow.
                diff_r = abs(int(self.prev_pic[h][w][0]) - int(new_pic[h][w][0]))
                diff_g = abs(int(self.prev_pic[h][w][1]) - int(new_pic[h][w][1]))
                diff_b = abs(int(self.prev_pic[h][w][2]) - int(new_pic[h][w][2]))
                total_diff = diff_r + diff_g + diff_b
                if total_diff > self.threshold:
                    diff_count += 1
                    if diff_count > self.sensitivity:
                        self.current_certainty += 1
                        found_motion_this_pic = True
                        break

        if self.current_certainty > self.min_certainty:
            self.current_certainty = 0
            return True

        if diff_count < self.sensitivity and self.current_certainty > 0:
            self.current_certainty -= 1
        self.prev_pic = new_pic
        return False

    def _cleanup(self):
        self.detrigger_all()
