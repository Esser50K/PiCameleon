import sys
from picameleon import Client

address = "localhost"
if len(sys.argv) > 1:
    address = sys.argv[1]

stream_id = "stream1"
client = Client(address)
client.trigger()  # triggers picameleon running the network_trigger mode on the default port
client.shutdown()
