import struct
import socket
from typing import Dict, Any
from json import dumps
from dataclasses import dataclass
from threading import Thread, Event, Lock
from ..outputs import WriterOutputHolder

DEFAULT_FRAME_FETCH_CHUNK_SIZE = 4096
DEFAULT_STREAM_SERVER_PORT = 5555
DEFAULT_TRIGGER_SERVER_PORT = 5556


@dataclass()
class StreamInfo:
    event: Event
    thread: Thread
    running: bool
    port: int = 0


class Client:
    def __init__(self, address):
        self.address = address
        self.current_streams: Dict[str, StreamInfo] = {}
        self.current_frames: Dict[str, bytes] = {}
        self.output_holders: Dict[str, WriterOutputHolder] = {}
        self.__lock = Lock()

    def get_next_frame(self, stream_id, timeout=None):
        if stream_id not in self.current_frames.keys() or stream_id not in self.current_streams.keys():
            raise Exception("no frames to fetch under stream with id %s" % stream_id)

        if self.current_streams[stream_id].event.wait(timeout):
            return self.current_frames[stream_id]

    def stop_stream(self, stream_id: str):
        with self.__lock:
            if stream_id in self.current_streams.keys():
                self.current_streams[stream_id].running = False
                if self.__is_receiver(stream_id):
                    self.__stop_receiver(stream_id)
                if stream_id in self.output_holders.keys():
                    self.output_holders[stream_id].stop()
                    self.output_holders[stream_id].shutdown()
                    del self.output_holders[stream_id]
                self.current_streams[stream_id].thread.join()
                del self.current_streams[stream_id]
                del self.current_frames[stream_id]

    def __is_receiver(self, stream_id: str):
        return self.current_streams[stream_id].port != 0

    def __stop_receiver(self, stream_id: str):
        if stream_id in self.current_streams.keys():
            self.current_streams[stream_id].running = False
            try:
                sock = socket.socket()
                sock.connect(('0.0.0.0', self.current_streams[stream_id].port))
            except socket.error:
                pass

    def serve_stream_receiver(self, stream_id: str, port: int):
        with self.__lock:
            event = Event()
            thread = Thread(target=self.__read_stream, args=(stream_id, port))
            self.current_streams[stream_id] = StreamInfo(event, thread, True, port)
            self.current_frames[stream_id] = b''
            thread.start()

    def __read_stream(self, stream_id: str, port: int):
        server_socket = socket.socket()
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(0)
        connection = server_socket.accept()[0]
        server_socket.close()

        try:
            while self.current_streams[stream_id].running:
                frame_size = struct.unpack('<L', connection.recv(4))[0]
                if frame_size == 0:
                    break

                frame = b''
                while len(frame) != frame_size:
                    frame += connection.recv(frame_size - len(frame))
                self.current_frames[stream_id] = frame
                if stream_id in self.output_holders.keys():
                    self.output_holders[stream_id].write(frame)
                self.current_streams[stream_id].event.set()
        except Exception as e:
            print("error reading stream:", e)
        finally:
            connection.close()
            self.current_streams[stream_id].event.set()
            with self.__lock:
                del self.current_streams[stream_id]
                del self.current_frames[stream_id]

    def fetch_stream(self,
                     stream_id: str,
                     stream_format: str,
                     port=DEFAULT_STREAM_SERVER_PORT,
                     resize: list = None,
                     bitrate: int = None,
                     frame_size=DEFAULT_FRAME_FETCH_CHUNK_SIZE,
                     size_prepended=True) -> None:
        with self.__lock:
            if stream_id in self.current_streams.keys():
                raise Exception("stream with id %s is still active" % stream_id)

            event = Event()
            thread = Thread(target=self.__fetch_stream,
                            args=(stream_id, stream_format, port, resize, bitrate, frame_size, size_prepended))
            self.current_streams[stream_id] = StreamInfo(event, thread, True)
            self.current_frames[stream_id] = b''
            thread.start()

    def write_stream_into(self, stream_id, output_id, output):
        with self.__lock:
            if stream_id not in self.current_streams.keys():
                raise Exception("stream with id %s is not active" % stream_id)

            if stream_id not in self.output_holders.keys():
                self.output_holders[stream_id] = WriterOutputHolder()
                self.output_holders[stream_id].start()

            output = parse_output(output)
            self.output_holders[stream_id].add_output(output_id, output)

    def remove_output_from_stream(self, stream_id, output_id):
        with self.__lock:
            if stream_id not in self.output_holders.keys():
                return

            self.output_holders[stream_id].remove_output(output_id)
            if len(self.output_holders[stream_id].outputs) == 0:
                self.output_holders[stream_id].stop()
                self.output_holders[stream_id].shutdown()

    def __fetch_stream(self,
                       stream_id: str,
                       stream_format: str,
                       port=DEFAULT_STREAM_SERVER_PORT,
                       resize: tuple = None,
                       bitrate: int = None,
                       frame_size=DEFAULT_FRAME_FETCH_CHUNK_SIZE,
                       size_prepended=True) -> None:
        sock = socket.socket()
        sock.settimeout(1)
        try:
            sock.connect((self.address, port))
        except Exception as e:
            print("failed to connect to picameleon to fetch stream at %s:%s: %s" % (self.address, port, e))
            sock.close()
            self.current_streams[stream_id].event.set()
            with self.__lock:
                del self.current_streams[stream_id]
                del self.current_frames[stream_id]

        try:
            stream_request = {"format": stream_format}
            if bitrate:
                stream_request["bitrate"] = bitrate
            if resize:
                stream_request["resize"] = resize

            stream_request = dumps(stream_request).encode("utf-8")
            request_size = len(stream_request)
            sock.send(struct.pack('<L', request_size))
            sock.sendall(stream_request)

            while self.current_streams[stream_id].running:
                self.current_streams[stream_id].event.clear()
                if size_prepended:
                    frame_size = struct.unpack('<L', sock.recv(4))[0]
                    if frame_size == 0:
                        break

                frame = b''
                while len(frame) != frame_size:
                    frame += sock.recv(frame_size - len(frame))

                self.current_frames[stream_id] = frame
                if stream_id in self.output_holders.keys():
                    self.output_holders[stream_id].write(frame)
                self.current_streams[stream_id].event.set()
        except Exception as e:
            print("failed to read frame from picameleon stream at %s:%s: %s" % (self.address, port, e))
        finally:
            sock.close()
            self.current_streams[stream_id].event.set()

    def trigger(self, port=DEFAULT_TRIGGER_SERVER_PORT):
        sock = socket.socket()
        sock.connect((self.address, port))
        sock.close()

    def shutdown(self):
        for stream_id in list(self.current_streams.keys()):
            self.stop_stream(stream_id)


def parse_output(output: Any):
    if type(output) is str:
        return open(output, "w")

    if getattr(output, "write", None):
        return output

    raise Exception("%s object is not recognized as writable" % output)
