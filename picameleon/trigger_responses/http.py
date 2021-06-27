import os
import tempfile
import requests
from time import sleep, time
from datetime import datetime
from streamers.streamer import ROOT_PATH, Streamer
from utils.single_picamera import SinglePiCamera
from .base import BaseTriggerResponse
from threading import Thread
from concurrent.futures import ThreadPoolExecutor

HTTP_TRIGGER_RESPONSE_NAME = "http"


class HTTP(BaseTriggerResponse):
    def __init__(self, http_service_urls=None, **capture_options):
        if http_service_urls is None:
            http_service_urls = {}

        super().__init__(use_detrigger=True)
        self.trigger_name = HTTP_TRIGGER_RESPONSE_NAME
        self.capture_options = capture_options
        # the key is the url the value is a boolean if a picture should be sent with the request
        self.http_service_urls = http_service_urls

    def _detriggered(self):
        return self.detrigger_event.wait(0.1)

    def _open_and_send(self, url, image_path):
        files = {"file": open(image_path, "rb")}
        result = requests.post(url, files=files)
        files["file"].close()
        return result

    def _trigger_response(self, trigger_args={}):
        tmp_dir = tempfile.TemporaryDirectory()
        image_path = tmp_dir.name + '/http_' + str(int(time())) + '.jpg'
        try:
            Streamer.take_picture(image_path, format='jpeg', **self.capture_options)
            for url, send_photo in self.http_service_urls.items():
                result = self._open_and_send(
                    url, image_path) if send_photo else requests.post(url)

                if result.status_code != 200:
                    print("http request %s was not successful:" %
                          url, result.text)
        finally:
            tmp_dir.cleanup()
