import sys
sys.path.append("/picameleon")
from streamers.streamer import Streamer, ROOT_PATH
from utils.single_picamera import SinglePiCamera
from streamers.streamer import Streamer
import unittest
from unittest.mock import MagicMock, call, patch, ANY

SECONDS_BEFORE = 5
SECONDS_AFTER = 5


class TestRecordToFile(unittest.TestCase):

    trigger_reponse = None

    def import_and_initialize(self):
        from trigger_responses.record_to_file import RecordToFile
        self.trigger_reponse = RecordToFile(format="h264",
                                            destination_path="captures",
                                            record_time_before_trigger=SECONDS_BEFORE,
                                            record_time_after_trigger=SECONDS_AFTER,
                                            use_detrigger=False)

    @patch("utils.single_picamera.SinglePiCamera")
    @patch("picamerax.PiCameraCircularIO")
    @patch("streamers.streamer.Streamer")
    def test_initialize_trigger_response(self, mocked_streamer, mocked_picam_io, mocked_picam):
        self.import_and_initialize()
        self.trigger_reponse._initialize_trigger_response()
        mocked_streamer.assert_called_once_with("h264",
                                                split_frames=False,
                                                recording_options={})
        mocked_picam_io.assert_called_once_with(
            ANY, seconds=SECONDS_BEFORE, splitter_port=ANY)
        self.assertEqual(self.trigger_reponse.streamer.output,
                         self.trigger_reponse.before_buffer)
        self.trigger_reponse.streamer.assert_has_calls([call.start()])

    def test_trigger_response(self):
        self.import_and_initialize()
        self.trigger_reponse.streamer = MagicMock()
        self.trigger_reponse.before_buffer = MagicMock()

        self.trigger_reponse._trigger_response()
        self.trigger_reponse.before_buffer.assert_has_calls(
            [call.copy_to(ANY, seconds=SECONDS_BEFORE), call.clear()])
        self.trigger_reponse.streamer.assert_has_calls([call.split_recording(ANY),
                                                        call.wait_recording(
                                                            SECONDS_AFTER),
                                                        call.split_recording(self.trigger_reponse.before_buffer)])


if __name__ == '__main__':
    unittest.main()
