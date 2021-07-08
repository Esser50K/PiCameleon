"""
This is the OutputHolder class.

This class helps streamers reuse camera ports for the same format and size combination
by passing the captured content through the various output analyzers
"""

from time import sleep
from collections import deque
from threading import Thread, Event, Lock, active_count, enumerate
from concurrent.futures import ThreadPoolExecutor


class OutputHolder:
    def __init__(self, outputs={}):
        self.outputs = outputs.copy()
        self.outputs_to_add = {}
        self.writable = False
        self.output_lock = Lock()
        self.writer_thread = None
        self.pool = ThreadPoolExecutor(max_workers=10)

    def has_outputs(self):
        return len(self.outputs) > 0

    def has_output(self, output_id):
        return output_id in self.outputs.keys()

    def get_output(self, output_id):
        return self.outputs[output_id]

    def add_output(self, output_id, output):
        with self.output_lock:
            self.outputs[output_id] = output

    def prepare_new_output(self, output_id, output):
        self.outputs_to_add[output_id] = output

    def remove_output(self, output_id):
        with self.output_lock:
            del self.outputs[output_id]

    def shutdown(self, wait=True):
        self.pool.shutdown(wait)


class WriterOutputHolder(Thread, OutputHolder):
    def __init__(self, outputs={}):
        Thread.__init__(self)
        OutputHolder.__init__(self, outputs)
        self.aux_buffer = deque()
        self.rebind_wait = Event()
        self.want_split = False
        self.outputs_to_split = {}

    def split_recording(self, output_id, output):
        self.want_split = True
        self.outputs_to_split[output_id] = output

    def write(self, buffer):
        """
        write method must return fast in order not to slow down the framerate
        """
        if self.writable:
            self.aux_buffer.append(buffer)

    def wait_for_rebind(self):
        self.rebind_wait.wait()
        self.rebind_wait.clear()

    def notify_split(self):
        self.aux_buffer.append(True)

    def run(self):
        self.writable = True
        with ThreadPoolExecutor(max_workers=10) as pool:
            while self.writable:
                try:
                    buffer = self.aux_buffer.popleft()

                    futures = []
                    with self.output_lock:
                        for oid, output in self.outputs.items():
                            # Using pool because instantiating Threads on every write is pretty slow
                            futures.append((oid, pool.submit(output.write, buffer)))
                        for oid, future in futures:
                            # Wait for result, if false remove the output
                            try:
                                if not future.result():
                                    del self.outputs[oid]
                            except Exception as e:
                                print("error writing to output %s %s:" % (oid, self.outputs[oid]), e)
                                del self.outputs[oid]

                    #  Check if its a split notifier
                    if type(buffer) is bool:
                        for out_id, out in self.outputs_to_add.items():
                            print("Changing output with id: %s" % out_id)
                            self.outputs[out_id] = out
                        self.outputs_to_add = {}
                        self.rebind_wait.set()
                        continue
                except IndexError:
                    sleep(0.05)
                except Exception as e:
                    print("Error writing frame to outputs:", e)
                    print("threads:\n", active_count(), enumerate())
                    self.stop()

    def stop(self):
        self.writable = False
