#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

from enum import Enum
from json import JSONDecoder, JSONEncoder


class MZNJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Enum):
            return {"e": o.name}
        if isinstance(o, set) or isinstance(o, range):
            return {"set": [{"e": i.name} if isinstance(i, Enum) else i for i in o]}

        return super().default(o)


class MZNJSONDecoder(JSONDecoder):
    def __init__(self, enum_map=None, *args, **kwargs):
        if enum_map is None:
            self.enum_map = {}
        else:
            self.enum_map = enum_map
        JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if len(obj) == 1 and "set" in obj:
            if len(obj["set"]) == 1 and isinstance(obj["set"][0], list):
                assert len(obj["set"][0]) == 2
                return range(obj["set"][0][0], obj["set"][0][1] + 1)

            li = []
            for item in obj["set"]:
                if isinstance(item, list):
                    assert len(item) == 2
                    li.extend([i for i in range(item[0], item[1] + 1)])
                elif len(obj) == 1 and "e" in obj:
                    li.append(self.enum_map.get(obj["e"], obj["e"]))
                else:
                    li.append(item)
            return set(li)
        elif len(obj) == 1 and "e" in obj:
            return self.enum_map.get(obj["e"], obj["e"])
        else:
            return obj
