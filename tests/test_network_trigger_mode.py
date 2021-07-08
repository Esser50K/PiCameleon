import sys
sys.path.append("/picameleon")
from .mocks.mock_socket import MockSocket
from modes.network_trigger import NetowrkTriggerMode
import json
import unittest
import struct
from unittest.mock import Mock, call, patch

mode = None
mode_config = {
    "redis": True,
    "redis_addr": "localhost"
}


class TestNetworkServingMode(unittest.TestCase):
    def tearDown(self):
        global mode
        if mode:
            mode._cleanup()

    @patch("redis.Redis")
    @patch("socket.socket")
    def test_preroutine(self, mocked_redis, mocked_socket):
        global mode
        mode = NetowrkTriggerMode(mode_config, {})
        mode.pre_routine()
        self.assertIsNotNone(mode.server_socket)
        mode.server_socket.assert_has_calls(
            [call.bind(("0.0.0.0", 5556)), call.listen()])
        self.assertIsNotNone(mode.redis)
        self.assertIsNotNone(mode.redis_announcer)

    @patch("redis.Redis")
    @patch("socket.socket")
    def test_routine(self, mocked_redis, mocked_socket):
        global mode
        mode = NetowrkTriggerMode(mode_config, {})
        mode.trigger = Mock()
        mode.pre_routine()
        client_address = "localhost:1234"
        request = json.dumps({"format": "h264", "bitrate": "vhigh"})
        mock_request = MockSocket([struct.pack("<L", len(request)), request])
        mode.server_socket.accept = Mock(
            return_value=(mock_request, client_address))
        mode.routine()
        self.assertTrue(mode.is_triggered)
        mode.trigger.assert_called_once()

        # should only trigger once until it is detriggered
        mode.routine()
        mode.trigger.assert_called_once()

        mode.is_triggered = False
        mode.routine()
        self.assertEqual(mode.trigger.call_count, 2)

    @patch("redis.Redis")
    @patch("socket.socket")
    def test_cleanup(self, mocked_redis, mocked_socket):
        global mode
        mode = NetowrkTriggerMode(mode_config, {})
        mode.pre_routine()
        mode._cleanup()
        mode.server_socket.assert_has_calls([call.close()])
        self.assertIsNone(mode.redis_announcer)


if __name__ == '__main__':
    unittest.main()
