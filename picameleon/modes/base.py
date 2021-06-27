"""
Base Mode Class.
"""
from threading import Thread
from datetime import datetime


class BaseMode:
    def __init__(self, config, trigger_responses=None):
        self.name = "base"
        self.config = config
        self.finish_time = None
        self.trigger_responses = [] if trigger_responses is None else trigger_responses
        self.is_running = False
        self.runner_thread = None
        self.streamer = None  # Subclass must have a Streamer object here
        self.ready = True

    def update_finish_time(self, finish_time):
        if self.finish_time < finish_time:
            self.finish_time = finish_time

    def initialize(self):
        if not self.ready:
            print("Mode '%s' is not ready. Not initializing." % self.name)
            return

        for trigger_response in self.trigger_responses:
            trigger_response.start_listening_for_trigger()
        return True

    def shutdown(self, wait=True):
        self.is_running = False
        self.finish_time = datetime.now()
        for trigger_response in self.trigger_responses:
            trigger_response.stop_listening_for_trigger(wait)

        self._cleanup()
        if self.runner_thread:
            self.runner_thread.join()

        if self.streamer and not self.streamer.output.has_outputs():
            self.streamer.stop()

    def trigger_all(self):
        for trigger_response in self.trigger_responses:
            trigger_response.trigger(self.name)

    def detrigger_all(self):
        for trigger_response in self.trigger_responses:
            trigger_response.detrigger()

    def start(self, finish_time=None):
        self.finish_time = finish_time
        self.is_running = True
        self.runner_thread = Thread(target=self.run)
        self.runner_thread.start()

    def _check_stop(self):
        if self.finish_time is None:
            return True

        return self.finish_time > datetime.now()

    def run(self):
        if not self.ready:
            print("Mode '%s' is not ready. Not running." % self.name)
            return

        if self.streamer:
            self.streamer.start()

        self.pre_routine()
        while self._check_stop():
            try:
                self.routine()
            except Exception as e:
                print("Caught exception in routine of %s:\n%s" %
                      (type(self).__name__, str(e)))

    def pre_routine(self):
        pass

    def routine(self):
        """
        Write code run in routine
        """
        pass

    def _cleanup(self):
        pass
