from time import time
from threading import Thread, Event
from trigger_responses.trigger_response_store import TriggerResponseStore
from utils.consts import GLOBALS, TRIGGER_COOLDOWN_TIME


class BaseTriggerResponse:
    def __init__(self, use_detrigger=False, cooldown_period=GLOBALS[TRIGGER_COOLDOWN_TIME]):
        self.trigger_name = "base"
        self.trigger_count = 0
        self.trigger_event = Event()
        self.detrigger_event = Event()
        self.use_detrigger = use_detrigger
        self.cooldown_period = cooldown_period
        self.last_trigger_time = 0
        self.listening = False
        self.trigger_listener = None
        self.is_running = False
        self.recent_triggers = set()
        self.trigger_args = {}
        self.ready = True

    def start_listening_for_trigger(self):
        """launches thread to listen for trigger.
        """
        if not self.ready:
            print("Trigger Response '%s' is not ready. Not starting." %
                  self.trigger_name)
            return

        self._initialize_trigger_response()
        self.listening = True
        self.trigger_listener = Thread(target=self._listen_for_trigger)
        self.trigger_listener.start()

    def stop_listening_for_trigger(self, wait=True):
        """stops listening to trigger.

        Keyword Arguments:
            wait {bool} -- wether to wait for trigger 
            listening thread to quit this method (default: {True})
        """

        self.listening = False
        self.trigger_event.set()
        if self.trigger_listener and wait:
            self.trigger_listener.join()

        self._cleanup_trigger_response()

    def detrigger(self):
        if self.use_detrigger and self.is_running:
            self.trigger_event.clear()
            self.detrigger_event.set()
            self.is_running = False

    def trigger(self, trigger_name, trigger_args={}):
        if not self.ready:
            print("Trigger Response '%s' is not ready. Not triggering." %
                  self.trigger_name)
            return

        self.recent_triggers.add(trigger_name)
        self.trigger_args.update(trigger_args)

        if not self.is_running:
            self.detrigger_event.clear()
            self.trigger_event.set()
            self.is_running = True

    def _initialize_trigger_response(self):
        pass

    def _cleanup_trigger_response(self):
        pass

    def _trigger_response(self, trigger_args=None):
        """
        Needs to be overriden by actual trigger response
        """
        pass

    def _listen_for_trigger(self):
        while self.listening and self.trigger_event.wait():
            self.trigger_event.clear()
            # don't spam the trigger
            if not time() - self.last_trigger_time < self.cooldown_period:
                self.last_trigger_time = time()
                try:
                    self._trigger_response(self.trigger_args)
                except Exception as e:
                    print("error on trigger response %s:" %
                          self.trigger_name, e)
            self.trigger_args = {}
            self.recent_triggers = set()
            self.is_running = False
