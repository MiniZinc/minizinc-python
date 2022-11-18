#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import warnings
from enum import Enum
from json import JSONDecoder, JSONEncoder, loads

from .error import MiniZincWarning, error_from_stream_obj
from .types import AnonEnum, ConstrEnum

try:
    import numpy
except ImportError:
    numpy = None


class MZNJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Enum):
            return {"e": o.name}
        if isinstance(o, AnonEnum):
            return {"e": o.enumName, "i": o.value}
        if isinstance(o, ConstrEnum):
            return {"c": o.constructor, "e": o.argument}
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
        kwargs["object_hook"] = self.mzn_object_hook
        JSONDecoder.__init__(self, *args, **kwargs)

    def transform_enum_object(self, obj):
        # TODO: This probably is an enum, but could still be a record
        if "e" in obj:
            if len(obj) == 1:
                return self.enum_map.get(obj["e"], obj["e"])
            elif len(obj) == 2 and "c" in obj:
                return ConstrEnum(obj["c"], obj["e"])
            elif len(obj) == 2 and "i" in obj:
                return AnonEnum(obj["e"], obj["i"])
        return obj

    def mzn_object_hook(self, obj):
        if isinstance(obj, dict):
            if len(obj) == 1 and "set" in obj:
                if len(obj["set"]) == 1 and isinstance(obj["set"][0], list):
                    assert len(obj["set"][0]) == 2
                    return range(obj["set"][0][0], obj["set"][0][1] + 1)

                li = []
                for item in obj["set"]:
                    if isinstance(item, list):
                        assert len(item) == 2
                        li.extend(list(range(item[0], item[1] + 1)))
                    elif isinstance(item, dict):
                        li.append(self.transform_enum_object(item))
                    else:
                        li.append(item)
                return set(li)
            else:
                return self.transform_enum_object(obj)
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
