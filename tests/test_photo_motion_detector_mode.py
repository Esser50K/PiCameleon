import sys
sys.path.append("/picameleon")
from unittest.mock import Mock
from modes.photo_motion_detection import PhotoMotionDetection
import numpy
import unittest

WIDTH = 224  # Default Width
HEIGHT = 160  # Default Height
# How Much pixel changes (really depends a lot on exposure_mode and awb_mode, this value seems to be good for default)
THRESHOLD = 100
SENSITIVITY = 50  # How many pixels change
MIN_CERTAINTY = 3  # How often the conditions must apply in a row
MOTION_DETECTOR_DETRIGGER = 5  # Number of pics without motion to detrigger
photo_motion_detector = None
base_pic = numpy.load("tests/test_data/base_pic.rgb.npy")
motion_pic = numpy.load("tests/test_data/motion_pic.rgb.npy")


def get_always_same_pic():
    return base_pic


get_base = False


def get_alternate_pics():
    global get_base
    ret = base_pic if get_base else motion_pic
    get_base = not get_base
    return ret


class TestMotionDetectorOutput(unittest.TestCase):

    def setUp(self):
        global photo_motion_detector
        photo_motion_detector = PhotoMotionDetection({}, {})
        photo_motion_detector.detrigger_all = Mock()
        photo_motion_detector.iterations_without_motion = 0
        photo_motion_detector.current_iteration = 0
        photo_motion_detector.current_certainty = 0
        photo_motion_detector.min_certainty = MIN_CERTAINTY
        photo_motion_detector.motion_detected = False
        photo_motion_detector.prev_pic = base_pic

    def test_not_detect_motion(self):
        """Checks if the motion detection algorithm works by
           not finding motion when always passing same config
        """
        photo_motion_detector.get_rgb_pic = get_always_same_pic
        for _ in range(10):
            photo_motion_detector.routine()
            self.assertEqual(photo_motion_detector.current_certainty, 0)
            self.assertFalse(photo_motion_detector.motion_detected)

    def test_detect_motion_and_detrigger(self):
        """Checks if the motion detection algorithm works by
           not finding motion when always passing same config
        """
        photo_motion_detector.get_rgb_pic = get_alternate_pics
        for i in range(MIN_CERTAINTY):
            photo_motion_detector.routine()
            self.assertEqual(photo_motion_detector.current_certainty, i + 1)
            self.assertFalse(photo_motion_detector.motion_detected)

        # Run routine 1 more time to detect motion
        photo_motion_detector.routine()
        self.assertEqual(photo_motion_detector.current_certainty, 0)
        self.assertTrue(photo_motion_detector.motion_detected)

        # Now don't detect until detriggered
        photo_motion_detector.prev_pic = base_pic
        photo_motion_detector.get_rgb_pic = get_always_same_pic
        for i in range(1, MOTION_DETECTOR_DETRIGGER):
            photo_motion_detector.routine()
            self.assertEqual(
                photo_motion_detector.iterations_without_motion, i)
            self.assertTrue(photo_motion_detector.motion_detected)

        # Run routine 1 more time to detrigger motion detection
        photo_motion_detector.routine()
        self.assertEqual(photo_motion_detector.iterations_without_motion, 0)
        self.assertFalse(photo_motion_detector.motion_detected)
        self.assertTrue(photo_motion_detector.detrigger_all.called)


if __name__ == '__main__':
    unittest.main()
