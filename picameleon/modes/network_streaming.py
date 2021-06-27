import json
from time import sleep
from .base import BaseMode
from outputs.server_socket_wrap import SocketWrap, SOCKET_TYPES
from streamers.streamer import Streamer

DEFAULT_FORMAT = "h264"


class NetworkStreamingMode(BaseMode):
    def __init__(self, config, trigger_responses):
        super().__init__(config, trigger_responses)
        self.name = "network_streaming"
        self.format = config["format"] if "format" in config else DEFAULT_FORMAT
        self.socket_map = {}
        self.has_hostsfile = False
        if "hosts" in config:
            self.hosts = config["hosts"]
        elif "hostsfile" in config:
            self.has_hostsfile = True
            self.hostsfile = config["hostsfile"] + (".%s" % self.format)
            self.hosts = self._read_hosts_file(retry=True)
        else:
            print("Error: No 'hosts' nor 'hostsfile' in config.")
            self.ready = False
            return

        prepend_size = config["prepend_size"] if "prepend_size" in config else False
        recording_options = config["recording_options"] if "recording_options" in config else {}
        self.streamer = Streamer(self.format, prepend_size=prepend_size, recording_options=recording_options)

    def _read_hosts_file(self, retry=False, retries=5, timeout=2):
        retry_count = 0
        while retry_count <= retries:
            try:
                with open(self.hostsfile, "r") as hostsfile:
                    return json.loads(hostsfile.read())
            except:
                if not retry:
                    return {}
                retry_count += 1
                sleep(timeout)
        return {}

    def update_socket_map(self):
        new_hosts_map = self._read_hosts_file()
        current_hosts = self.hosts.keys()
        new_hosts = new_hosts_map.keys()
        hosts_to_add = new_hosts - current_hosts
        hosts_to_delete = current_hosts - new_hosts

        for host in hosts_to_add:
            host_def = new_hosts_map[host]
            self._parse_and_add_host(host, host_def)

        for host in hosts_to_delete:
            self._remove_host(host)

        self.hosts = new_hosts_map

    def _parse_and_add_host(self, host, host_def):
        port = int(host_def["port"])
        protocol = host_def["protocol"]
        greeting = host_def["greeting"] if "greeting" in host_def.keys() else None
        if protocol not in SOCKET_TYPES:
            print("Protocol '%s' is not supported. Choose udp or tcp.")

        sock = SocketWrap(host, port, protocol, greeting)
        self.socket_map[host] = sock

    def _remove_host(self, host):
        if self.streamer.output.has_output(host):
            self.streamer.output.remove_output(host)

        if host in self.socket_map:
            self.socket_map[host].close()
            del self.socket_map[host]

    def pre_routine(self):
        for host, host_def in self.hosts.items():
            self._parse_and_add_host(host, host_def)

    def routine(self):
        # Update according to hostsfile in case it exists
        if self.has_hostsfile:
            self.update_socket_map()

        # Reconnection Routine
        for host, sock in self.socket_map.items():
            if not sock.is_connected():
                print("%s is not connected. Trying to reconnect." % host)
                if sock.connect():
                    if not self.streamer.output.has_output(host):
                        self.streamer.output.add_output(host, sock)
                else:
                    if self.streamer.output.has_output(host):
                        self.streamer.output.remove_output(host)
        sleep(2)

    def _cleanup(self):
        for host, sock in self.socket_map.items():
            if self.streamer.output.has_output(host):
                self.streamer.output.remove_output(host)
            sock.close()
        self.hosts_map = {}
        self.socket_map = {}
