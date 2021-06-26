import sys
sys.path.append("/picameleon")
from unittest.mock import patch
import unittest
import filecmp
import time
import os
from streamers.base import BaseStreamer
from streamers.split_frame import SplitFrameStreamer
from streamers.streamer import Streamer


class TestStreamer(unittest.TestCase):

    def test_multiple_output_write(self):
        """Tests if writing to multiple outputs produces 3 equally sized files
        """

        output1 = open("out1.h264", "wb")
        output2 = open("out2.h264", "wb")
        output3 = open("out3.h264", "wb")

        streamer1 = Streamer("h264", id_output=("1", output1))
        streamer2 = Streamer("h264", id_output=("2", output2))
        streamer3 = Streamer("h264", id_output=("3", output3))

        self.assertIs(streamer1, streamer2)
        self.assertIs(streamer2, streamer3)
        self.assertEqual(len(streamer1.output.outputs), 3)
        self.assertEqual(len(Streamer.get_available_ports()), 3)

        streamer1.start()
        streamer1.wait_recording(1)
        streamer1.stop()
        time.sleep(0.5)

        output1.close()
        output2.close()
        output3.close()

        self.assertEqual(os.stat("out1.h264").st_size,
                         os.stat("out2.h264").st_size)
        self.assertEqual(os.stat("out2.h264").st_size,
                         os.stat("out3.h264").st_size)
        self.assertEqual(filecmp.cmp("out1.h264", "out2.h264"), True)
        self.assertEqual(filecmp.cmp("out2.h264", "out3.h264"), True)

        os.remove("out1.h264")
        os.remove("out2.h264")
        os.remove("out3.h264")

    def test_multi_streamer_singleton(self):
        streamer1 = Streamer("h264")
        self.assertEqual(len(Streamer.get_available_ports()), 3)
        streamer2 = Streamer("mjpeg")
        self.assertEqual(len(Streamer.get_available_ports()), 2)
        streamer3 = Streamer("yuv420")
        self.assertEqual(len(Streamer.get_available_ports()), 1)
        streamer4 = Streamer("h264", recording_options={"resize": "1280x720"})
        self.assertEqual(len(Streamer.get_available_ports()), 0)

        self.assertIsNot(streamer1, streamer2)
        self.assertIsNot(streamer1, streamer3)
        self.assertIsNot(streamer1, streamer4)
        self.assertIsNot(streamer2, streamer3)
        self.assertIsNot(streamer2, streamer4)
        self.assertIsNot(streamer3, streamer4)

        self.assertIsInstance(streamer1, SplitFrameStreamer)
        self.assertIsInstance(streamer2, SplitFrameStreamer)
        self.assertIsInstance(streamer3, BaseStreamer)
        self.assertIsInstance(streamer4, SplitFrameStreamer)
        self.assertRaises(Exception, Streamer, "mjpeg", recording_options={"resize": "1920x1080"})

        streamer4.stop()
        self.assertEqual(len(Streamer.get_available_ports()), 1)
        streamer4 = Streamer("mjpeg", recording_options={"resize": "1920x1080"})
        self.assertEqual(len(Streamer.get_available_ports()), 0)
        self.assertRaises(Exception, Streamer, "mjpeg", recording_options={"resize": "480p"})
        streamer1.stop()
        self.assertEqual(len(Streamer.get_available_ports()), 1)
        streamer2.stop()
        self.assertEqual(len(Streamer.get_available_ports()), 2)
        streamer3.stop()
        self.assertEqual(len(Streamer.get_available_ports()), 3)
        streamer4.stop()
        self.assertEqual(len(Streamer.get_available_ports()), 4)

    def test_get_picture_port(self):
        # Check initial port availability
        self.assertEqual(len(Streamer.get_available_ports()), 4)

        # Get a picture port and check port availability
        picture_port = Streamer._get_picture_port()
        self.assertEqual(len(Streamer.get_available_ports()), 3)

        # Get another picture port and check port availability and that it's same port
        repicture_port = Streamer._get_picture_port()
        self.assertEqual(len(Streamer.get_available_ports()), 3)
        self.assertEqual(picture_port, repicture_port)

        # Return the picture port and check that availability has been restored
        Streamer._return_port_availability(picture_port)
        self.assertIsNone(Streamer._picture_port)
        self.assertEqual(len(Streamer.get_available_ports()), 4)

    @patch("picamerax.PiCamera.capture")
    def test_take_picture(self, mocked_capture):
        # Check initial port availability and port being set
        self.assertEqual(len(Streamer.get_available_ports()), 4)
        self.assertIsNone(Streamer._picture_port)

        # Take picture with all possible extra args
        Streamer.take_picture("test_output.jpg",
                              format="randomFormat",
                              **{"option1": 1, "option2": 2, "resize": (100,200)})

        # Check everything was returned after picture was taken
        self.assertEqual(len(Streamer.get_available_ports()), 4)
        self.assertIsNone(Streamer._picture_port)

        # Check picamerax.capture was called correctly
        mocked_capture.assert_called_once_with('test_output.jpg',
                                               format='randomFormat',
                                               option1=1,
                                               option2=2,
                                               resize=(100, 200),
                                               splitter_port=2,
                                               use_video_port=True)


if __name__ == '__main__':
    unittest.main()
