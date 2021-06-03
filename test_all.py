import os
import sys
import subprocess

BLACKLIST = {"__init__.py"}
TEST_PATH = os.getenv("TEST_PATH", "tests/")


def run_test_file(test_file):
    p = subprocess.Popen(["python3", TEST_PATH + test_file], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    return p.communicate()[0], p.returncode


test_files = os.listdir(TEST_PATH)
pattern = ".py"
if len(sys.argv) > 1:
    pattern = sys.argv[1]

filtered_test_files = [f for f in test_files if pattern in f and f not in BLACKLIST]
print("Testing files:\n" + "\n".join(filtered_test_files))

totaloutput = ""
returncode = 0
for f in filtered_test_files:
    output, rcode = run_test_file(f)
    if rcode > returncode:
        returncode = rcode
    totaloutput += output.decode("utf-8") + "\n"

print(totaloutput)
sys.exit(returncode)
