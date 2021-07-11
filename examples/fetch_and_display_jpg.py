import cv2
import sys
import numpy as np
from picameleon import Client
from threading import Event


class OpenCVDecoder:
    def __init__(self):
        self.current_frame = None
        self._event = Event()

    def write(self, frame):
        self.current_frame = cv2.imdecode(np.frombuffer(frame, np.uint8), cv2.IMREAD_UNCHANGED)
        self._event.set()
        return True

    def show(self):
        while self._event.wait():
            cv2.imshow("frame", self.current_frame)
            cv2.waitKey(1)
            self._event.clear()


address = "localhost"
if len(sys.argv) > 1:
    address = sys.argv[1]

decoder = OpenCVDecoder()
stream_id = "stream1"
output_id = "output1"
client = Client(address)
client.fetch_stream(stream_id, "mjpeg", bitrate=1700000)
client.write_stream_into(stream_id, output_id, decoder)

try:
    while True:
        decoder.show()
except KeyboardInterrupt:
    pass
except Exception as e:
    print("error fetching frames:", e)
finally:
    client.shutdown()
