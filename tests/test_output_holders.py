import sys
sys.path.append("/picameleon")
from outputs.motion_output_holder import MotionOutputHolder
from outputs.output_holder import OutputHolder, WriterOutputHolder
import time
import unittest
from unittest.mock import Mock, call

mock_output = Mock()


def create_and_start_writer_output_holder():
    output_holder = WriterOutputHolder()
    output_holder.start()
    return output_holder


def write_and_wait(writer_output_holder, sleep, *test_data, analyze=False):
    action = writer_output_holder.analyze if analyze else writer_output_holder.write
    for data in test_data:
        action(data)
    time.sleep(sleep)


class TestOutputHolder(unittest.TestCase):

    def test_add_output(self):
        output_holder = OutputHolder()
        output_holder.add_output("test", mock_output)
        self.assertEqual(1, len(output_holder.outputs))
        self.assertIn("test", output_holder.outputs.keys())

    def test_remove_output(self):
        output_holder = OutputHolder()
        output_holder.add_output("test", mock_output)
        self.assertEqual(1, len(output_holder.outputs))
        output_holder.remove_output("test")
        self.assertEqual(0, len(output_holder.outputs))
        self.assertRaises(KeyError, output_holder.remove_output, "test")

    def test_has_output(self):
        output_holder = OutputHolder()
        output_holder.add_output("test", mock_output)
        self.assertTrue(output_holder.has_output("test"))

    def test_get_output(self):
        output_holder = OutputHolder()
        output_holder.add_output("test", mock_output)
        output = output_holder.get_output("test")
        self.assertIs(output, mock_output)


class TestWriterOutputHolder(unittest.TestCase):

    def setUp(self):
        mock_output.reset_mock()

    def test_write(self):
        """Checks that calls to write on the output 
        handler are correctly passed to the internal outputs
        """

        test_data = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        output_holder = create_and_start_writer_output_holder()
        output_holder.add_output("test1", mock_output)
        write_and_wait(output_holder, .2, *test_data)
        self.assertEqual(mock_output.write.call_count, len(test_data))
        mock_output.assert_has_calls([call.write(data) for data in test_data])
        output_holder.stop()
        output_holder.join()

    def test_stop(self):
        """Checks that no more write calls to the 
        internal outputs are made after closing the output holder
        """

        output_holder = create_and_start_writer_output_holder()
        output_holder.add_output("test", mock_output)
        write_and_wait(output_holder, .1, "test1")
        self.assertEqual(mock_output.write.call_count, 1)
        output_holder.stop()
        time.sleep(.1)
        self.assertFalse(output_holder.is_alive())
        write_and_wait(output_holder, .1, "test1")
        self.assertEqual(mock_output.write.call_count, 1)
        self.assertEqual(len(output_holder.aux_buffer), 0)


class TestMotionOutputHolder(unittest.TestCase):

    def setUp(self):
        mock_output.reset_mock()

    def test_analyze(self):
        test_data = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        output = MotionOutputHolder(outputs={"test": mock_output})
        write_and_wait(output, .1, *test_data, analyze=True)
        self.assertEqual(mock_output.analyze.call_count, len(test_data))
        mock_output.assert_has_calls(
            [call.analyze(data) for data in test_data])


if __name__ == '__main__':
    unittest.main()
