"""
This is the OutputHolder class.

This class helps streamers reuse camera ports for the same format and size combination
by passing the captured content through the various output analyzers
"""

from .output_holder import OutputHolder
from utils.single_picamera import SinglePiCamera
from picamerax.array import PiMotionAnalysis


class MotionOutputHolder(OutputHolder, PiMotionAnalysis):
    def __init__(self, outputs={}, size=None):
        OutputHolder.__init__(self, outputs)
        PiMotionAnalysis.__init__(self, SinglePiCamera(), size=size)

    def analyze(self, motion_vectors):
        futures = []
        with self.output_lock:
            for _, output in self.outputs.items():
                futures.append(self.pool.submit(output.analyze, motion_vectors))
            for future in futures:
                future.result()