import sys
sys.path.append("/picameleon")
from .mocks.mock_socket import MockSocket
from modes.network_serving import NetworkServingMode
import json
import unittest
import struct
from unittest.mock import Mock, call, patch

mode = None
mode_config = {
    "redis": True,
    "redis_addr": "localhost"
}


class TestNetworkTriggerMode(unittest.TestCase):
    def tearDown(self):
        if mode:
            mode._cleanup()

    @patch("redis.Redis")
    @patch("socket.socket")
    def test_preroutine(self, mocked_redis, mocked_socket):
        global mode
        mode = NetworkServingMode(mode_config, {})
        mode.pre_routine()
        self.assertIsNotNone(mode.server_socket)
        mode.server_socket.assert_has_calls(
            [call.bind(("0.0.0.0", 5555)), call.listen()])
        self.assertIsNotNone(mode.redis)
        self.assertIsNotNone(mode.redis_announcer)

    @patch("redis.Redis")
    @patch("socket.socket")
    def test_routine(self, mocked_redis, mocked_socket):
        global mode
        mode = NetworkServingMode(mode_config, {})
        mode.pre_routine()
        client_address = "localhost:1234"
        request = json.dumps({"format": "h264", "bitrate": 1_000_000})
        mode.server_socket.accept = Mock(return_value=(MockSocket(
            [struct.pack("<L", len(request)), request]), client_address))
        mode.routine()
        self.assertEqual(len(mode.socket_map), 1)
        self.assertTrue(client_address in mode.socket_map.keys())
        self.assertTrue(client_address in mode.socket_to_stream.keys())
        self.assertTrue(
            mode.streamer_map["h264_1000000"].output.has_output(client_address))
        mode.socket_map[client_address].close()
        self.assertEqual(len(mode.socket_map), 0)

    @patch("redis.Redis")
    @patch("socket.socket")
    def test_cleanup(self, mocked_redis, mocked_socket):
        global mode
        mode = NetworkServingMode(mode_config, {})
        mode.pre_routine()
        client_socket_mock = Mock()
        mode.socket_map = {
            "localhost:1234": client_socket_mock,
            "localhost:1235": client_socket_mock
        }
        mode._cleanup()
        mode.server_socket.assert_has_calls([call.close()])
        client_socket_mock.assert_has_calls([call.close()])
        self.assertIsNone(mode.redis_announcer)


if __name__ == '__main__':
    unittest.main()
