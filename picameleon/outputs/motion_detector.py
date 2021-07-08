"""
The Motion Detection class.
"""

import numpy
from threading import Event
from utils.consts import GLOBALS, MOTION_DETECTOR_THRESHOLD, MOTION_DETECTOR_SENSITIVITY

OUTPUT_ID = "motion_detector"


class MotionDetector:
    def __init__(self, threshold=GLOBALS[MOTION_DETECTOR_THRESHOLD], sensitivity=GLOBALS[MOTION_DETECTOR_SENSITIVITY]):
        self.threshold = threshold
        self.sensitivity = sensitivity
        self.motion_detected = Event()
        self.save = True
        self.motion_vectors_list = []
        self.start = 0

    # Jsonify numpy arrays
    # https://stackoverflow.com/questions/26646362/numpy-array-is-not-json-serializable
    def analyze(self, motion_vectors):
        self.motion_detected.clear()
        motion_vectors = numpy.sqrt(
            numpy.square(motion_vectors['x'].astype(numpy.float)) +
            numpy.square(motion_vectors['y'].astype(numpy.float))
        ).clip(0, 255).astype(numpy.uint8)
        if (motion_vectors >= self.threshold).sum() > self.sensitivity:
            self.motion_detected.set()

    def calibrate(self, no_motion_seconds=5, max_resets=5):
        reset_count = 0
        while self.motion_detected.wait(no_motion_seconds):
            reset_count += 1
            if reset_count > max_resets:
                return False
        return True

    def wait_for_motion(self, timeout=None):
        return self.motion_detected.wait(timeout)
