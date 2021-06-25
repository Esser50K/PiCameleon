import sys
sys.path.append("/picameleon")
from datetime import datetime
from modes.base import BaseMode
from time import sleep, time
import unittest
from unittest.mock import Mock, call

mock_streamer = Mock()
mock_trigger_responses = [Mock() for _ in range(5)]


class TestBaseMode(unittest.TestCase):

    def setUp(self):
        mock_streamer.reset_mock()
        map(lambda x: x.reset_mock, mock_trigger_responses)

    def test_update_finish_time(self):
        """update_finish_time should only update if finish_time is greater than
        """
        mode = BaseMode({}, mock_trigger_responses)
        finish_time = time()
        finish_date = datetime.fromtimestamp(finish_time)
        mode.finish_time = finish_date
        mode.update_finish_time(datetime.fromtimestamp(finish_time + 1))
        self.assertEqual(datetime.fromtimestamp(
            finish_time + 1), mode.finish_time)
        mode.update_finish_time(datetime.fromtimestamp(finish_time - 1))
        self.assertEqual(datetime.fromtimestamp(
            finish_time + 1), mode.finish_time)

    def test_initialize(self):
        mode = BaseMode({}, mock_trigger_responses)
        mode.initialize()
        for mock in mock_trigger_responses:
            mock.assert_has_calls([call.start_listening_for_trigger()])

    def test_start(self):
        mode = BaseMode({}, mock_trigger_responses)
        mode.pre_routine = Mock()
        mode.routine = Mock()
        mode.streamer = mock_streamer
        finish_time = time() + 0.2
        finish_date = datetime.fromtimestamp(finish_time)
        mode.start(finish_date)
        self.assertEqual(finish_date, mode.finish_time)
        self.assertTrue(mode.is_running)
        self.assertIsNotNone(mode.runner_thread)
        self.assertTrue(mode.runner_thread.is_alive())
        mock_streamer.assert_has_calls([call.start()])
        mode.routine.assert_any_call()
        mode.pre_routine.assert_called_once()
        mode.runner_thread.join()

    def test_check_stop(self):
        mode = BaseMode({}, mock_trigger_responses)
        self.assertTrue(mode._check_stop())
        mode.finish_time = datetime.fromtimestamp(time() + .1)
        self.assertTrue(mode._check_stop())
        sleep(.1)
        self.assertFalse(mode._check_stop())

    def test_trigger_all(self):
        mode = BaseMode({}, mock_trigger_responses)
        mode.trigger_all()
        for mock in mock_trigger_responses:
            mock.assert_has_calls([call.trigger("base")])
    """
    def test_retrigger(self):
        mode = BaseMode({}, mock_trigger_responses)
        mock_retrigger = Mock()
        mode.trigger_all(mock_retrigger)
        for mock in mock_trigger_responses:
            mock.assert_has_calls([call.trigger(mock_retrigger)])
        mock_retrigger.assert_called(call._trigger_response())
    """

    def test_detrigger_all(self):
        mode = BaseMode({}, mock_trigger_responses)
        mode.detrigger_all()
        for mock in mock_trigger_responses:
            mock.assert_has_calls([call.detrigger()])

    def test_shutdown(self):
        mode = BaseMode({}, mock_trigger_responses)
        mode._cleanup = Mock()
        mode.runner_thread = Mock()
        mode.streamer = Mock()
        mode.streamer.output = Mock()
        mode.streamer.output.has_outputs = Mock(return_value=False)
        mode.shutdown()
        self.assertFalse(mode.is_running)
        self.assertGreater(datetime.now(), mode.finish_time)
        for mock in mock_trigger_responses:
            mock.assert_has_calls([call.stop_listening_for_trigger(True)])
        mode.runner_thread.assert_has_calls([call.join()])
        mode._cleanup.assert_called_once()
        mode.streamer.output.assert_has_calls([call.has_outputs()])
        mode.streamer.assert_has_calls([call.stop()])


if __name__ == '__main__':
    unittest.main()
