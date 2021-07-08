import sys
sys.path.append("/picameleon")
from modes.network_streaming import NetworkStreamingMode
import unittest
from unittest.mock import Mock

mock_streamer = Mock()
mock_trigger_responses = [Mock() for _ in range(5)]

hosts_and_hostsfile_config = {
    "hosts": {
        "localhost": {}
    },
    "hostsfile": "some_file.json"
}

hostsfile_only_config = {
    "hostsfile": "some_file.json"
}

hostsfile_config = {
    "hosts": {
        "otherhost": {}
    }
}


def hosts_config_generator(hosts):
    host_config = {}
    for host in hosts:
        host_config[host] = {
            "port": 12345,
            "protocol": "tcp",
            "greeting": [0, 1, 0]
        }
    return host_config


# Just used to mock some functions that would need access to files
class MockNetworkStreamingMode(NetworkStreamingMode):
    def __init__(self, config, trigger_responses, return_value=None):
        self._return_value = return_value
        super().__init__(config, trigger_responses)

    def _read_hosts_file(self, retry=False, retries=5, timeout=2):
        return self._return_value


class TestNetworkStreamingMode(unittest.TestCase):

    def setUp(self):
        pass

    def test_sets_host_instead_of_hostfile(self):
        mode = MockNetworkStreamingMode(
            hosts_and_hostsfile_config, {}, return_value=hostsfile_config["hosts"])
        self.assertEqual(mode.hosts, hosts_and_hostsfile_config["hosts"])

    def test_sets_host_from_hostfile(self):
        mode = MockNetworkStreamingMode(
            hostsfile_only_config, {}, return_value=hostsfile_config["hosts"])
        self.assertEqual(mode.hosts, hostsfile_config["hosts"])

    def test_sets_mode_readiness_to_false_when_missing_hosts(self):
        mode = MockNetworkStreamingMode({}, {})
        self.assertFalse(mode.ready)

    def test_update_socket_map(self):
        first_hosts = hosts_config_generator(["1.1.1.1", "1.1.1.2"])
        hostsfile_config = hosts_config_generator(["1.1.1.3", "1.1.1.4"])
        mode = MockNetworkStreamingMode(
            hostsfile_only_config, {}, return_value=hostsfile_config)
        mode.hosts = first_hosts
        mode.update_socket_map()
        self.assertEqual(mode.hosts, hostsfile_config)
        self.assertEqual(mode.socket_map.keys(), mode.hosts.keys())

    def test_routine(self):
        socket_wrap1 = Mock()
        socket_wrap1.is_connected.return_value = False
        socket_wrap1.connect.return_value = True
        socket_wrap2 = Mock()
        socket_wrap2.is_connected.return_value = False
        socket_wrap2.connect.return_value = False
        config = {
            "hosts": {}
        }
        mode = MockNetworkStreamingMode(config, {})
        mode.socket_map = {
            "1.1.1.1": socket_wrap1,
            "1.1.1.2": socket_wrap2
        }
        mode.streamer.output.outputs = {"1.1.1.2": socket_wrap2}
        mode.routine()
        self.assertEqual(mode.streamer.output.outputs,
                         {"1.1.1.1": socket_wrap1})


if __name__ == '__main__':
    unittest.main()
