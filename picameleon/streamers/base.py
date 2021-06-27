"""
BaseStreamer is the base class for generic streamer implementations.
"""
from utils.single_picamera import SinglePiCamera
from outputs.output_holder import WriterOutputHolder
from outputs.motion_output_holder import MotionOutputHolder
from threading import Thread, Lock


class BaseStreamer:
    def __init__(self, port, format, options):
        self.camera = SinglePiCamera()
        self.port = port
        self.format = format
        self.resize = self.parse_resize(options["resize"])
        del options["resize"]
        self.output = WriterOutputHolder()
        self.motion_output = MotionOutputHolder(size=self.resize)
        self.sub_output = None
        self.options = options
        self.is_running = False
        self.is_recording = False
        self._callback = lambda port: None
        self._lock = Lock()

    def parse_resize(self, resize):
        try:
            if type(resize) is str:
                width, height = map(int, resize.split("x"))
                return (width, height)
            if type(resize) is tuple or type(resize) is list:
                return (resize[0], resize[1])
        except Exception as e:
            print("error parsing resize parameter:", e)

        return (self.camera.resolution[0], self.camera.resolution[1])

    def close(self):
        try:
            if self.is_recording:
                print("trying to stop recording on port %d" % self.port)
                self.camera.stop_recording(splitter_port=self.port)
        except Exception as e:
            print("Error stopping recording on port %d: %s" % (self.port, e))
        finally:
            self.is_recording = False
            print("stopped recording on port %d" % self.port)

    def stop(self):
        with self._lock:
            self._callback(self.port)
            if not self.is_running:
                return

            self.close()
            self.is_running = False
            if self.motion_output:
                self.motion_output.shutdown(True)
            if self.output and type(self.output) is WriterOutputHolder:
                self.output.stop()
                self.output.shutdown(True)
            self._teardown_streamer()

    def start(self):
        with self._lock:
            if not self.is_running:
                self.is_running = True
                self._setup_streamer()
                if type(self.output) is WriterOutputHolder and not self.output.writable:
                    self.output.start()
                self.run_streamer()

    def run_streamer(self):
        output = self.sub_output if self.sub_output else self.output
        print("Start recording with %s format, size: %s, on port %d" % (self.format, str(self.resize), self.port))
        if self.format == "h264":
            self.options["motion_output"] = self.motion_output

        if self.resize[0] == self.camera.resolution[0] and self.resize[1] == self.camera.resolution[1]:
            self.resize = None

        if not self.is_recording:
            self.camera.start_recording(output,
                                        format=self.format,
                                        resize = self.resize,
                                        splitter_port=self.port,
                                        **self.options)
            print("started recording on port %d" % self.port)
            self.is_recording = True

    def wait_recording(self, seconds):
        self.camera.wait_recording(seconds, self.port)

    def split_recording(self, output):
        """
        Only use this method if you have changed the default output of OutputHolder
        """
        self.camera.split_recording(output, splitter_port=self.port)
        self.output = output

    def rebind_output(self, output_id, output):
        self.output.prepare_new_output(output_id, output)
        self.camera.split_recording(self.output, splitter_port=self.port)
        self.output.notify_split()

    def _setup_streamer(self):
        pass

    def _teardown_streamer(self):
        pass

    def shutdown(self):
        self.stop()
        if self.motion_output:
            self.motion_output.shutdown()
        if type(self.output) is WriterOutputHolder:
                self.output.stop()
                self.output.shutdown()

