#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

from enum import Enum
from json import JSONDecoder, JSONEncoder


class MZNJSONEncoder(JSONEncoder):
    def default(self, o):
        from .solver import Solver

        if isinstance(o, set):
            return {"set": [i for i in o]}
        elif isinstance(o, range):
            return {"set": [i for i in o]}
        elif isinstance(o, Enum):
            return {"e": o.name}
        elif isinstance(o, Solver):
            return {
                "name": o.name,
                "version": o.version,
                "id": o.id,
                "executable": o.executable,
                "mznlib": o.mznlib,
                "tags": o.tags,
                "stdFlags": o.stdFlags,
                "extraFlags": o.extraFlags,
                "supportsMzn": o.supportsMzn,
                "supportsFzn": o.supportsFzn,
                "needsSolns2Out": o.needsSolns2Out,
                "needsMznExecutable": o.needsMznExecutable,
                "needsStdlibDir": o.needsStdlibDir,
                "isGUIApplication": o.isGUIApplication,
            }
        else:
            return super().default(o)


class MZNJSONDecoder(JSONDecoder):
    def __init__(self, enum_map=None, *args, **kwargs):
        if enum_map is None:
            self.enum_map = {}
        else:
            self.enum_map = enum_map
        JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        from .solver import Solver

        if len(obj) == 1 and "set" in obj:
            if len(obj["set"]) == 1 and isinstance(obj["set"][0], list):
                assert len(obj["set"][0]) == 2
                return range(obj["set"][0][0], obj["set"][0][1] + 1)

            li = []
            for item in obj["set"]:
                if isinstance(item, list):
                    assert len(item) == 2
                    li.extend([i for i in range(item[0], item[1] + 1)])
                else:
                    assert isinstance(item, int)
                    li.append(item)
            return set(li)
        elif len(obj) == 1 and "e" in obj:
            return self.enum_map.get(obj["e"], obj["e"])
        elif all(
            [i in obj.keys() for i in ["name", "version", "id", "executable"]]
        ) and all([i in Solver.FIELDS for i in obj.keys()]):
            return Solver._from_dict(obj)
        else:
            return obj
