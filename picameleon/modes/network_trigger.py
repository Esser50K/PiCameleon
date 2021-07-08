import os
import redis
import socket
from time import sleep
from threading import Thread
from .base import BaseMode

DEFAULT_REDIS_ADDR = "redis_streaming"
DEFAULT_REDIS_PORT = 6379
DEFAULT_LISTEN_ADDR = "0.0.0.0"
DEFAULT_LISTEN_PORT = 5556
DEFAULT_DETRIGGER_DELAY = 5
TRIGGER_ID = int(os.getenv("TRIGGER_ID", 0))
NODE_ADDR = os.getenv("NODE_ADDR", "")


class NetowrkTriggerMode(BaseMode):
    def __init__(self, config, trigger_responses):
        super().__init__(config, trigger_responses)
        self.name = "network_trigger"
        self.trigger_id = config["trigger_id"] if "trigger_id" in config else TRIGGER_ID
        self.listen_addr = config["listen_addr"] if "listen_addr" in config else DEFAULT_LISTEN_ADDR
        self.listen_port = config["listen_port"] if "listen_port" in config else DEFAULT_LISTEN_PORT
        self.detrigger_delay = config["detrigger_delay"] if "detrigger_delay" in config else DEFAULT_DETRIGGER_DELAY
        self.enable_redis_discovery = config["redis"] if "redis" in config else False
        self.redis_port = config["redis_port"] if "redis_port" in config else DEFAULT_REDIS_PORT
        if "redis_addr" in config:
            self.redis_addr = config["redis_addr"]
        else:
            print("Warning: address of redis server not specified. Defaulting to 'redis_streaming'")
            self.redis_addr = DEFAULT_REDIS_ADDR
        self.is_listening = False
        self.is_triggered = False
        self.redis = None
        self.redis_announcer = None
        self.server_socket = None

    def pre_routine(self):
        # Initialize server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
                self.redis.set("recorder.%d" % (self.trigger_id),
                            "recorder.%d:%d" % (self.trigger_id, self.listen_port))
                if NODE_ADDR:
                    self.redis.set("recorder.node.%d" % (self.trigger_id),
                                "%s:%d" % (NODE_ADDR, self.listen_port))
            except Exception as e:
                print("Exception occurred setting address on redis:", e)
            finally:
                sleep(10)

    def _trigger(self):
        self.trigger_all()
        sleep(self.detrigger_delay)
        self.detrigger_all()
        self.is_triggered = False

    def trigger(self):
        Thread(target=self._trigger, daemon=True).start()
        
    def routine(self):
        try:
            conn, _ = self.server_socket.accept()
            if not self.is_triggered:
                self.is_triggered = True
                self.trigger()
            conn.close()
        except Exception as e:
            print("Error in network trigger routine:", e)

    def _cleanup(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((self.listen_addr, self.listen_port))
            except socket.error:
                pass

        self.server_socket.close()
        self.is_listening = False
        if self.redis_announcer:
            self.redis_announcer.join()
            self.redis_announcer = None

