import socket
import struct
from threading import Lock

SOCKET_TYPES = {
    "udp": socket.SOCK_DGRAM,
    "tcp": socket.SOCK_STREAM
}


class SocketWrap:
    def __init__(self, host, port, socket_type, greeting=None):
        self.socket = socket.socket(socket.AF_INET, SOCKET_TYPES[socket_type])
        self.sock_file = None
        self._is_connected = False
        self.socket_type = socket_type
        self.host = host
        self.port = port
        self.greeting = greeting
        self._lock = Lock()

    def is_connected(self):
        if self.socket_type == "tcp":
            return self._is_connected
        return True

    def _send_greeting(self):
        for data in self.greeting:
            if type(data) is int:
                self.sock_file.write(struct.pack('<L', data))
            elif type(data) is str:
                self.sock_file.write(data.encode("utf-8"))
            elif type(data) is bytes:
                self.sock_file.write(data)
            else:
                print("Don't know how to send data with type:", type(data))
        self.sock_file.flush()

    def connect(self):
        with self._lock:
            if not self.is_connected():
                self.socket = socket.socket(socket.AF_INET, SOCKET_TYPES[self.socket_type])
                self.socket.settimeout(5)
                try:
                    self.socket.connect((self.host, self.port))
                    self.sock_file = self.socket.makefile("wb")
                    if self.greeting:
                        self._send_greeting()
                    self._is_connected = True
                    return True
                except Exception as e:
                    print("Error on connection:", e)
                    self._is_connected = False
                    return False
            return True

    def close(self):
        if self.is_connected() and self.socket_type == "tcp":
            self.sock_file.close()
            self.socket.close()

    def write(self, data):
        with self._lock:
            try:
                if self.is_connected():
                    if self.socket_type == "tcp":
                        self.sock_file.write(data)
                        self.sock_file.flush()
                    else:
                        while len(data) > 1024:
                            to_send = data[:1024]
                            self.socket.sendto(to_send, (self.host, self.port))
                            data = data[1024:]
                        self.socket.sendto(data, (self.host, self.port))
            except Exception as e:
                print("Error occured, socket disconnected.", e)
                self._is_connected = False
                return False
        return True
