from ctypes import CDLL

from ..driver import Driver


class APIDriver(Driver):
    def __init__(self, library: CDLL):
        self.library = library

        super(APIDriver, self).__init__()

    # TODO: IMPLEMENT
