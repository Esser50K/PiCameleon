import sys
import json
import signal
from streamers.streamer import Streamer
from croniter import croniter
from datetime import datetime
from utils.consts import GLOBALS
from utils.single_picamera import SinglePiCamera
from mode_executor.mode_executor import ModeExecutor
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler
# Import Modes
from modes.motion_detection import MotionDetectionMode
from modes.network_streaming import NetworkStreamingMode
from modes.network_serving import NetworkServingMode
from modes.network_trigger import NetowrkTriggerMode
from modes.photo_motion_detection import PhotoMotionDetection
# Import Trigger Responses
from trigger_responses.dummy import Dummy
from trigger_responses.snapshot import Snapshot
from trigger_responses.record_to_file import RecordToFile
from trigger_responses.http import HTTP
from trigger_responses.trigger_response_store import TriggerResponseStore

SCHEDULES_PATH = "schedules/"
RESOLUTION = "1280x720"
FRAMERATE = 25

MODE_MAP = {
    "motion_detection": MotionDetectionMode,
    "network_streaming": NetworkStreamingMode,
    "network_serving": NetworkServingMode,
    "network_trigger": NetowrkTriggerMode,
    "photo_motion_detection": PhotoMotionDetection
}

TRIGGER_RESPONSE_MAP = {
    "record_to_file": RecordToFile,
    "snapshot": Snapshot,
    "dummy": Dummy
}


def clean_stop(signum, frame):
    # Dummy way to signal the streaming_server configurator to stop
    try:
        with open("stop_configurator", "w") as stop_configurator:
            pass
        scheduler.shutdown(wait=False)
        for executor in mode_executors.values():
            executor[0].stop()
        Streamer.shutdown_streamers()
    except Exception as e:
        print("error exiting:", e)
    finally:
        try:
            SinglePiCamera().close()
        except Exception as e:
            print("failed to close PiCamera cleanly")


def help_message():
    print("./main.py <path_to_config_file>")


def parse_schedule(filename):
    with open(SCHEDULES_PATH + filename + ".cron") as schedule:
        start, finish = list(map(str.strip, schedule.read().split(":")))
    return start, finish


if len(sys.argv) < 2:
    print("Not enough arguments. Need to at least provide the configuration file.")
    help_message()
    sys.exit(1)

with open(sys.argv[1], "r") as config_file:
    config = json.loads(config_file.read())

# Load Globals
if "globals" in config.keys():
    for k, v in config["globals"]:
        GLOBALS[k] = v

if "camera_initialization_options" in config.keys():
    # Initialize singleton with the set configs
    camera = SinglePiCamera(**config["camera_initialization_options"])
else:
    camera = SinglePiCamera(resolution=RESOLUTION, framerate=FRAMERATE)

# Parse and instantiate trigger responses
trigger_response_store = TriggerResponseStore()
if "trigger_responses" in config.keys():
    for trigger_response_name, resp_args in config["trigger_responses"].items():
        if trigger_response_name in TRIGGER_RESPONSE_MAP.keys():
            trigger_response_store.add_trigger_response(trigger_response_name,
                                                        TRIGGER_RESPONSE_MAP[trigger_response_name](**resp_args))

if "modes" not in config.keys():
    print("Config file needs to have 'modes' configuration in order to run.")
    print("Please check the example configurations.")
    sys.exit(1)

modes_configs = config["modes"]

mode_executors = {}
for mode_name, mode_config_list in modes_configs.items():
    for idx, mode_config in enumerate(mode_config_list):
        if "schedules" not in mode_config.keys():
            print("Mode configuration for %s at index %d needs a list of schedules with the 'schedules' key." % (
                mode_name, idx))
            print("Skipping %s..." % mode_name)

        mode_id = "%s_%d" % (mode_name, idx)
        schedules = mode_config["schedules"]
        trigger_responses = mode_config["trigger_responses"] if "trigger_responses" in mode_config else {
        }
        mode_trigger_responses = [trigger_response_store.get_trigger_response(
            name) for name in trigger_responses]
        mode = MODE_MAP[mode_name](
            trigger_responses=mode_trigger_responses, config=mode_config["mode_config"])
        mode_executor = ModeExecutor(mode_id, mode)
        mode_executors[mode_id] = mode_executor, [
            parse_schedule(schedule) for schedule in schedules]

executors = {"default": ThreadPoolExecutor(max_workers=10)}
job_defaults = {"coalesce": True, "max_instances": 1}
scheduler = BlockingScheduler(executors=executors, job_defaults=job_defaults)
for mode, config in mode_executors.items():
    executor, schedules = config
    for sched in schedules:
        # Check if the job is supposed to always run
        # This means it doesn't need to be scheduled
        if sched[0] == sched[1]:
            executor.start()
            continue

        now = datetime.now()
        next_start = croniter(sched[0], now).get_next(datetime)
        next_stop = croniter(sched[1], now).get_next(datetime)
        minute, hour, mday, month, wday = sched[0].split()
        if (next_start - next_stop).total_seconds() >= 0:
            executor.start(sched[1])
            misfire_grace_time = int(
                (next_stop - croniter(sched[0], now).get_prev(datetime)).total_seconds())
        else:
            misfire_grace_time = int((next_stop - next_start).total_seconds())

        if misfire_grace_time == 0:
            misfire_grace_time = None

        # APScheduler and Croniter have different weekday normalization, transforming range into csv of days
        if "-" in wday:
            range_days = list(map(int, wday.split("-")))
            wday = list(map(lambda x: x % 7, list(
                range(range_days[0], range_days[1] + 1))))
            wday = ",".join(map(str, wday))

        # Add job to scheduler
        # The executor.start method checks if the mode is already running
        # If it is it will update its finish_time if it is greater than the current finish_time
        # misfire_grace_time is set to the supposed job duration (stop - start)
        scheduler.add_job(executor.start,
                          args=(sched[1],),
                          trigger="cron",
                          minute=minute,
                          hour=hour,
                          day=mday,
                          month=month,
                          day_of_week=wday,
                          id=mode,
                          misfire_grace_time=misfire_grace_time)

signal.signal(signal.SIGINT, clean_stop)
signal.signal(signal.SIGTERM, clean_stop)
try:
    scheduler.start()
finally:
    SinglePiCamera().close()
