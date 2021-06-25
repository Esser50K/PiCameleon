import sys
sys.path.append("/picameleon")
from trigger_responses.trigger_response_store import TriggerResponseStore
import unittest
from unittest.mock import Mock, ANY, call, patch, mock_open


class TestHTTP(unittest.TestCase):
    trigger_response = None

    def import_and_initialize(self):
        from trigger_responses.http import HTTP
        self.trigger_response = HTTP(
            http_service_urls={
                "http://test_with_pic.com": True,
                "http://test_without_pic.com": False,
            })

    @patch("requests.post")
    @patch("builtins.open")
    def test_open_and_send(self, mocked_open, mocked_post):
        self.import_and_initialize()
        self.trigger_response._open_and_send(
            "http://test.com/v1/faces?id=the_id.jpg", "/tmp/image/path.jpg")
        mocked_open.assert_called_once_with("/tmp/image/path.jpg", "rb")
        mocked_post.assert_called_once_with("http://test.com/v1/faces?id=the_id.jpg",
                                            files={"file": mocked_open.return_value})
        mocked_open.return_value.assert_has_calls([call.close()])

    @patch("requests.post")
    @patch("builtins.open", new_callable=mock_open, read_data=b'test content')
    def test_trigger_response(self, mocked_open, mocked_post):
        self.import_and_initialize()
        # given
        post_response = Mock()
        post_response.status_code = 200
        mocked_post.return_value = post_response

        # when
        self.trigger_response._trigger_response()

        # then
        self.assertEqual(mocked_post.call_count, 2)
        mocked_post.assert_has_calls([call("http://test_with_pic.com", files=ANY),
                                      call("http://test_without_pic.com")],
                                      any_order=True)

if __name__ == '__main__':
    unittest.main()
