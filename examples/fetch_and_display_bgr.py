import cv2
import sys
import numpy as np
from picameleon import Client

address = "localhost"
if len(sys.argv) > 1:
    address = sys.argv[1]

stream_id = "stream1"
client = Client(address)
client.fetch_stream(stream_id, "bgr", resize=(320, 240))

try:
    while True:
        frame = client.get_next_frame(stream_id)
        if frame is None:
            break
        decoded = np.frombuffer(frame, np.uint8).reshape((240, 320, 3))
        cv2.imshow("frame", decoded)
        cv2.waitKey(1)
except Exception as e:
    print("error fetching frames:", e)
finally:
    client.shutdown()
