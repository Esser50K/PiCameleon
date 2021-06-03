class TriggerResponseStore:
    __instance = None
    trigger_responses = None

    def __new__(cls):
        if TriggerResponseStore.__instance is None:
            TriggerResponseStore.__instance = object.__new__(cls)
            TriggerResponseStore.__instance.trigger_responses = {}
        return TriggerResponseStore.__instance

    def add_trigger_response(self, name, trigger_response):
        self.trigger_responses[name] = trigger_response

    def get_trigger_response(self, name):
        return self.trigger_responses[name] \
            if name in self.trigger_responses.keys() else None
