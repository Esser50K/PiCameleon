import sys
sys.path.append("/picameleon")
sys.path.append("../picameleon")
from client.client import Client
import unittest
from unittest.mock import MagicMock, patch, call
from struct import pack
from time import sleep

client: Client = None


def mocked_recv(bufsize):
    if bufsize == 4:
        return pack('<L', 512)

    return b'\x00'*bufsize


class TestClient(unittest.TestCase):
    def tearDown(self):
        if client:
            client.shutdown()

    @patch("socket.socket")
    def test_fetch_stream(self, mocked_socket: MagicMock):
        global client
        # given
        mocked_socket.return_value = MagicMock()
        mocked_socket.return_value.recv = mocked_recv
        client = Client("localhost")

        # when
        client.fetch_stream("stream1", "h264")
        frame = client.get_next_frame("stream1")

        # then
        self.assertEqual(frame, b'\x00'*512)
        self.assertEqual(1, len(client.current_streams))
        self.assertEqual(1, len(client.current_frames))
        self.assertEqual(0, len(client.output_holders))
        self.assertTrue("stream1" in client.current_streams.keys())
        mocked_socket.assert_has_calls([call().settimeout(1),
                                        call().connect(('localhost', 5555)),
                                        call().send(b'\x12\x00\x00\x00'),  # len of the greeting packed
                                        call().sendall(b'{"format": "h264"}')],
                                       any_order=True)

        client.stop_stream("stream1")
        self.assertEqual(0, len(client.current_streams))
        self.assertEqual(0, len(client.current_frames))
        mocked_socket.assert_has_calls([call.close()],
                                       any_order=True)

    @patch("socket.socket")
    def test_fetch_stream_into(self, mocked_socket: MagicMock):
        global client
        # given
        mocked_output = MagicMock()
        mocked_socket.return_value = MagicMock()
        mocked_socket.return_value.recv = mocked_recv
        client = Client("localhost")

        # when
        client.fetch_stream("stream1", "h264")
        client.write_stream_into("stream1", "output1", mocked_output)
        frame = client.get_next_frame("stream1")  # just waiting until frame really got written

        # then
        self.assertEqual(1, len(client.current_streams))
        self.assertEqual(1, len(client.current_frames))
        self.assertEqual(1, len(client.output_holders))
        self.assertEqual(1, len(client.output_holders["stream1"].outputs))
        self.assertTrue("stream1" in client.current_streams.keys())
        sleep(.05)
        mocked_output.write.assert_has_calls([call.write(frame)])

        client.stop_stream("stream1")
        self.assertEqual(0, len(client.current_streams))
        self.assertEqual(0, len(client.current_frames))
        mocked_socket.assert_has_calls([call.close()],
                                       any_order=True)

    @patch("socket.socket")
    def test_stream_receiver(self, mocked_socket: MagicMock):
        global client
        # given
        mocked_connection = MagicMock()
        mocked_socket.return_value = MagicMock()
        mocked_socket.return_value.accept = MagicMock(return_value=(mocked_connection, "localhost"))
        mocked_connection.recv = mocked_recv
        client = Client("localhost")

        # when
        client.serve_stream_receiver("stream1", 5555)
        frame = client.get_next_frame("stream1")

        # then
        self.assertEqual(frame, b'\x00'*512)
        self.assertEqual(1, len(client.current_streams))
        self.assertEqual(1, len(client.current_frames))
        self.assertEqual(0, len(client.output_holders))
        client.stop_stream("stream1")
        self.assertEqual(0, len(client.current_streams))
        self.assertEqual(0, len(client.current_frames))


if __name__ == '__main__':
    unittest.main()
