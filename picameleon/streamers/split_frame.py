import io
import struct
from threading import Thread, Event
from .base import BaseStreamer

SPLITTER_STRINGS = {
    "mjpeg": b'\xff\xd8',
    "h264": b'\x00\x00\x00\x01'
}


class SplitFrameStreamer(BaseStreamer):
    def __init__(self, port, format, prepend_size=False, options=None):
        if options is None:
            options = {}

        super().__init__(port, format, options)
        self.event = Event()
        self.prepend_size = prepend_size
        self.stream = io.BytesIO()
        self.last_frame = None
        self.streamer_thread = None
        self.splitter_string = SPLITTER_STRINGS[format] if format in SPLITTER_STRINGS.keys() else None

    def _setup_streamer(self):
        self.sub_output = self
        if self.output:
            self.streamer_thread = Thread(target=self.stream_frames)
            self.streamer_thread.start()

    def get_last_frame(self):
        return self.last_frame

    def get_next_frame(self, timeout=None):
        if self.event.wait(timeout):
            return self.last_frame

    def stream_frames(self):
        while self.is_running:
            try:
                frame = self.get_next_frame(timeout=1)
                if frame is None:
                    continue

                self.event.clear()
                if self.prepend_size:
                    frame = struct.pack('<L', len(frame)) + frame
                self.output.write(frame)
            except Exception as e:
                print("Error writing next frame:", e)

    def can_write(self, buf):
        # check if buffer starts with splitter string if it exists
        # if it doesn't exist then just check the stream is not empty
        return ((self.splitter_string is not None and \
                buf.startswith(self.splitter_string)) or \
               (self.splitter_string is None)) and \
               self.stream.tell() > 0


    def write(self, buf):
        if self.can_write(buf):
            self.stream.seek(0)
            self.last_frame = self.stream.read()
            self.event.set()
            self.stream.seek(0)
            self.stream.truncate()

        self.stream.write(buf)

    def _teardown_streamer(self):
        if self.streamer_thread:
            self.streamer_thread.join()
            self.streamer_thread = None
