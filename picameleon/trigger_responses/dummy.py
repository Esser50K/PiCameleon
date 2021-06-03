import io
from time import sleep
from datetime import datetime
from streamers.streamer import ROOT_PATH
from utils.single_picamera import SinglePiCamera
from .base import BaseTriggerResponse


class Dummy(BaseTriggerResponse):
    def __init__(self, use_detrigger=False, **recording_options):
        super().__init__(use_detrigger=use_detrigger)

    def _trigger_response(self, trigger_args={}):
        print("dummy trigger reponse was triggered with:\n", trigger_args)
