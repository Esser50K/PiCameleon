import os
import json
import redis
import socket
import struct
from time import sleep
from threading import Thread, Lock
from .base import BaseMode
from streamers.streamer import Streamer
from outputs.client_socket_wrap import ClientSocketWrap
from typing import Tuple
from queue import Queue

DEFAULT_MAX_STREAMS = 2
DEFAULT_REDIS_ADDR = "redis_streaming"
DEFAULT_REDIS_PORT = 6379
DEFAULT_LISTEN_ADDR = "0.0.0.0"
DEFAULT_LISTEN_PORT = 5555
STREAM_ID = int(os.getenv("STREAMER_ID", 0))
NODE_ADDR = os.getenv("NODE_ADDR", "")


class NetworkServingMode(BaseMode):
    def __init__(self, config, trigger_responses):
        super().__init__(config, trigger_responses)
        self.name = "network_serving"
        self.stream_id = config["stream_id"] if "stream_id" in config else STREAM_ID
        self.listen_addr = config["listen_addr"] if "listen_addr" in config else DEFAULT_LISTEN_ADDR
        self.listen_port = config["listen_port"] if "listen_port" in config else DEFAULT_LISTEN_PORT
        self.max_streams = config["max_streams"] if "max_streams" in config else DEFAULT_MAX_STREAMS
        self.enable_redis_discovery = config["redis"] if "redis" in config else False
        self.redis_port = config["redis_port"] if "redis_port" in config else DEFAULT_REDIS_PORT
        if "redis_addr" in config:
            self.redis_addr = config["redis_addr"]
        else:
            print("Warning: address of redis server not specified. Defaulting to 'redis_streaming'")
            self.redis_addr = DEFAULT_REDIS_ADDR
        self.is_listening = False
        self.redis = None
        self.redis_announcer = None
        self.server_socket = None
        self.socket_map = {}
        self.socket_to_stream = {}
        self.streamer_map = {}
        self._lock = Lock()
        self._unregister_queue = Queue()

        # Streamer init options
        self.prepend_size = config["prepend_size"] if "prepend_size" in config else False
        self.recording_options = config["recording_options"] if "recording_options" in config else {}

    def pre_routine(self):
        # Initialize server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.listen_addr, self.listen_port))
        self.server_socket.listen()
        self.is_listening = True
        
        # Register at redis
        if self.enable_redis_discovery:
            self.redis_announcer = Thread(target=self.announce_to_redis)
            self.redis_announcer.start()

    def announce_to_redis(self):
        if not NODE_ADDR:
            print("warning: NODE_ADDR not set, streamer won't be reachable from outside")

        self.redis = redis.Redis(self.redis_addr, self.redis_port)
        while self.is_listening:
            try:
                self.redis.set("streamer.%d" % self.stream_id,
                               "streamer.%d:%d" % (self.stream_id, self.listen_port))
                if NODE_ADDR:
                    self.redis.set("streamer.node.%d" % self.stream_id,
                                   "%s:%d" % (NODE_ADDR, self.listen_port))
            except Exception as e:
                print("Exception occured setting address on redis:", e)
            finally:
                sleep(10)

    def cleanup_output(self, output_id):
        with self._lock:
            del self.socket_map[output_id]
            if output_id in self.socket_to_stream:
                streamer_id = self.socket_to_stream[output_id]
                # at this point the output hasn't been removed yet because the callback didn't return, so the number of outputs should be 1
                if streamer_id in self.streamer_map and len(self.streamer_map[streamer_id].output.outputs) == 1:
                    self.streamer_map[streamer_id].stop()
                    del self.streamer_map[streamer_id]
                del self.socket_to_stream[output_id]

    def parse_request(self, conn: socket) -> Tuple[str, str]:
        conn.settimeout(5)
        input_length = struct.unpack('<L', conn.recv(4))[0]
        request = json.loads(conn.recv(input_length))
        return request["format"], request["bitrate"]

    def can_serve_client(self, conn: socket, vformat: str, bitrate: str) -> bool:
        if streamer_key(vformat, bitrate) not in self.streamer_map:
            if len(self.streamer_map) >= self.max_streams:
                return False

            try:
                self.streamer_map[streamer_key(vformat, bitrate)] = Streamer(vformat,
                                                                                  prepend_size=self.prepend_size,
                                                                                  recording_options={
                                                                                      **self.recording_options,
                                                                                      "bitrate": translate_bitrate(bitrate)
                                                                                      })
            except Exception as e:
                print("unable to serve client probably because no more video ports are available:", e)
                return False
        return True

    def routine(self):
        conn, client_address = self.server_socket.accept()
        vformat, bitrate = "", 1_000_000
        try:
            vformat, bitrate = self.parse_request(conn)
            with self._lock:
                if not self.can_serve_client(conn, vformat, bitrate):
                    conn.sendall(struct.pack('<L', 0))
                    conn.close()
                    return

                client_socket = ClientSocketWrap(conn, client_address, self.cleanup_output)
                self.socket_map[client_address] = client_socket
                self.socket_to_stream[client_address] = streamer_key(vformat, bitrate)

                streamer = self.streamer_map[streamer_key(vformat, bitrate)]
                if len(self.socket_map) >= 1 and not streamer.is_running:
                    streamer.start()

                streamer.output.add_output(client_address, client_socket)
        except Exception as e:
            print("Error in network serving routine:", e)
            if client_address in self.socket_map.keys():
                self.socket_map[client_address].close()
                del self.socket_map[client_address]
            else:
                conn.close()

            if client_address in self.socket_to_stream.keys():
                del self.socket_to_stream[client_address]

            if streamer_key(vformat, bitrate) in self.streamer_map.keys():
                streamer.stop()
                del self.streamer_map[streamer_key(vformat, bitrate)]

    def _cleanup(self):
        sockets_to_clean = [s for s in self.socket_map.values()]
        for sock in sockets_to_clean:
            sock.close()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((self.listen_addr, self.listen_port))
            except:
                pass

        self.socket_map = {}
        self.socket_to_stream = {}
        self.server_socket.close()
        self.is_listening = False
        if self.redis_announcer:
            self.redis_announcer.join()
            self.redis_announcer = None


def streamer_key(vformat: str, bitrate: str) -> str:
    return "%s_%s" % (vformat, bitrate)


def translate_bitrate(bitrate: str) -> int:
    if bitrate == "vhigh":
        return 18_000_000
    elif bitrate == "high":
        return 6_000_000
    elif bitrate == "low":
        return 2_000_000
    elif bitrate == "vlow":
        return 500_000

    return 1_000_000
