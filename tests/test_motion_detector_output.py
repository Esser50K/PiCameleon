import sys
sys.path.append("/picameleon")
from outputs.motion_detector import MotionDetector
from threading import Thread
import numpy
import unittest

THRESHOLD = 8  # Magnitude of motion vector
SENSITIVITY = 10  # Number of motion vectors
DEFAULT_TIMEOUT = 1
motion_detector = MotionDetector(THRESHOLD, SENSITIVITY)
motion_vectors = numpy.load("tests/test_data/motion_vectors.npy")
no_motion_vectors = numpy.load("tests/test_data/no_motion_vectors.npy")


class TestMotionDetectorOutput(unittest.TestCase):

    def setUp(self):
        motion_detector.motion_detected.clear()

    def asynchronous_motion_detection(self, motion_vectors):
        def motion_vectors_through_analyze(motion_vectors):
            for motion_vector in motion_vectors:
                motion_detector.analyze(motion_vector)
        t = Thread(target=motion_vectors_through_analyze,
                   args=(motion_vectors,))
        t.start()
        return t

    def test_analyze_detect_motion(self):
        """Checks if the analyze method detects motion correctly
        """
        job = self.asynchronous_motion_detection(motion_vectors)
        self.assertTrue(motion_detector.wait_for_motion(DEFAULT_TIMEOUT))
        job.join()

    def test_analyze_not_detect_motion(self):
        """Checks if no motion is detected
        """
        job = self.asynchronous_motion_detection(no_motion_vectors)
        self.assertFalse(motion_detector.wait_for_motion(DEFAULT_TIMEOUT))
        job.join()

    def test_calibration_fails(self):
        """Checks if calibration fails when motion is detected
        """
        job = self.asynchronous_motion_detection(motion_vectors)
        self.assertFalse(motion_detector.calibrate(
            no_motion_seconds=DEFAULT_TIMEOUT, max_resets=1))
        job.join()

    def test_calibration_succeeds(self):
        """Checks if calibration fails when motion is detected
        """
        job = self.asynchronous_motion_detection(no_motion_vectors)
        self.assertTrue(motion_detector.calibrate(
            no_motion_seconds=DEFAULT_TIMEOUT, max_resets=1))
        job.join()


if __name__ == '__main__':
    unittest.main()
