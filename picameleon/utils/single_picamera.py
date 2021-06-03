"""
SinglePiCamera class

Since only one instance of PiCamera can exist this
simply wraps the PiCamera object in a singleton class.
"""
import inspect

from picamerax import PiCamera


class SinglePiCamera:
    instance = None

    def __init__(self, **options):
        if not SinglePiCamera.instance:
            picam_args = set(inspect.getfullargspec(PiCamera).args)

            # clean up args that dont belong and set new ones that didn't exist before
            args = {k: v for k, v in options.items() if k in picam_args}
            options = {k: v for k, v in options.items() if k not in picam_args}

            SinglePiCamera.instance = PiCamera(**args)
            for k, v in options.items():
                setattr(SinglePiCamera.instance, k, v)

    def __getattr__(self, attr):
        return getattr(SinglePiCamera.instance, attr)

    def __setattr__(self, name, value):
        return setattr(SinglePiCamera.instance, name, value)
