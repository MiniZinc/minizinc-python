#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import warnings
from enum import Enum
from json import JSONDecoder, JSONEncoder, loads

from .error import MiniZincWarning, error_from_stream_obj

try:
    import numpy
except ImportError:
    numpy = None


class MZNJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Enum):
            return {"e": o.name}
        if isinstance(o, set) or isinstance(o, range):
            return {"set": [{"e": i.name} if isinstance(i, Enum) else i for i in o]}
        if numpy is not None:
            if isinstance(o, numpy.ndarray):
                return o.tolist()
            if isinstance(o, numpy.generic):
                return o.item()
        return super().default(o)


class MZNJSONDecoder(JSONDecoder):
    def __init__(self, enum_map=None, *args, **kwargs):
        if enum_map is None:
            self.enum_map = {}
        else:
            self.enum_map = enum_map
        JSONDecoder.__init__(self, object_hook=self.mzn_object_hook, *args, **kwargs)

    def mzn_object_hook(self, obj):
        if isinstance(obj, dict) and len(obj) == 1:
            if "set" in obj:
                if len(obj["set"]) == 1 and isinstance(obj["set"][0], list):
                    assert len(obj["set"][0]) == 2
                    return range(obj["set"][0][0], obj["set"][0][1] + 1)

                li = []
                for item in obj["set"]:
                    if isinstance(item, list):
                        assert len(item) == 2
                        li.extend([i for i in range(item[0], item[1] + 1)])
                    elif isinstance(item, dict) and len(item) == 1 and "e" in item:
                        li.append(self.enum_map.get(item["e"], item["e"]))
                    else:
                        li.append(item)
                return set(li)
            elif "e" in obj:
                return self.enum_map.get(obj["e"], obj["e"])
        return obj


def decode_json_stream(byte_stream: bytes, cls=None, **kw):
    for line in byte_stream.split(b"\n"):
        line = line.strip()
        if line != b"":
            obj = loads(line, cls=cls, **kw)
            if obj["type"] == "warning" or (
                obj["type"] == "error" and obj["what"] == "warning"
            ):
                # TODO: stack trace and location
                warnings.warn(obj["message"], MiniZincWarning)
            elif obj["type"] == "error":
                raise error_from_stream_obj(obj)
            else:
                yield obj


async def decode_async_json_stream(stream: asyncio.StreamReader, cls=None, **kw):
    buffer: bytes = b""
    while not stream.at_eof():
        try:
            buffer += await stream.readuntil(b"\n")
            buffer = buffer.strip()
            if buffer == b"":
                continue
            obj = loads(buffer, cls=cls, **kw)
            if obj["type"] == "warning" or (
                obj["type"] == "error" and obj["what"] == "warning"
            ):
                # TODO: stack trace and location
                warnings.warn(obj["message"], MiniZincWarning)
            elif obj["type"] == "error":
                raise error_from_stream_obj(obj)
            else:
                yield obj
            buffer = b""
        except asyncio.LimitOverrunError as err:
            buffer += await stream.readexactly(err.consumed)
