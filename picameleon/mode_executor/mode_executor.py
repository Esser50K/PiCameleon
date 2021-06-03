"""
BaseModeExecutor Class
"""

import json
from croniter import croniter
from datetime import datetime


class ModeExecutor:
    def __init__(self, modename, mode):
        self.modename = modename
        self.mode = mode

    def start(self, finish_time=None):
        if finish_time is not None:
            finish_time = croniter(finish_time, datetime.now()).get_next(datetime)

        if not self.mode.is_running:
            if self.mode.initialize():
                self.mode.start(finish_time)
            else:
                raise Exception("Unable to initialize %s mode" % self.modename)
        elif finish_time:
            self.mode.update_finish_time(finish_time)

    def stop(self, wait=True):
        self.mode.shutdown(wait)
