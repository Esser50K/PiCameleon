import sys
sys.path.append("/picameleon")
from mode_executor.mode_executor import ModeExecutor
from datetime import datetime
import unittest
from unittest.mock import Mock, call

mode = Mock()


def datetime_minutes(now=None):
    if not now:
        now = datetime.now()

    return datetime(now.year,
                    now.month,
                    now.day,
                    now.hour,
                    min(59, now.minute + 1))


class TestModeExecutor(unittest.TestCase):

    def setUp(self):
        mode.reset_mock()

    def test_start_mode_not_running(self):
        """tests the start method when mode is not running
        """
        mode.is_running = False
        mode.initialize = Mock(return_value=True)
        mexec = ModeExecutor("test", mode)
        mexec.start("* * * * *")
        mode.assert_has_calls([call.initialize(),
                               call.start(datetime_minutes())])

    def test_start_mode_is_running(self):
        """tests the start method when mode is running
        """
        mode.is_running = True
        mexec = ModeExecutor("test", mode)
        mexec.start("* * * * *")
        mode.assert_has_calls([call.update_finish_time(datetime_minutes())])

    def test_start_mode_init_error(self):
        """tests the start method when mode fails to initialize
        """
        mode.is_running = False
        mode.initialize = Mock(return_value=False)
        mexec = ModeExecutor("test", mode)
        self.assertRaises(Exception, mexec.start, "* * * * *")

    def test_stop(self):
        """tests stop method
        """
        mexec = ModeExecutor("test", mode)

        # With wait defaulting to True
        mexec.stop()
        mode.assert_has_calls([call.shutdown(True)])

        # With wait set to False
        mexec.stop(False)
        mode.assert_has_calls([call.shutdown(False)])


if __name__ == '__main__':
    unittest.main()
