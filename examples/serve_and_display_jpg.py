import cv2
import sys
import numpy as np
from picameleon import Client

address = "localhost"
if len(sys.argv) > 1:
    address = sys.argv[1]

stream_id = "stream1"
client = Client(address)
client.serve_stream_receiver(stream_id, 12345)

try:
    while True:
        frame = client.get_next_frame(stream_id)
        if frame is None:
            break
        decoded = cv2.imdecode(np.frombuffer(frame, np.uint8), cv2.IMREAD_UNCHANGED)
        cv2.imshow("frame", decoded)
        cv2.waitKey(1)
except KeyboardInterrupt:
    pass
except Exception as e:
    print("error fetching frames:", e)
finally:
    client.shutdown()
