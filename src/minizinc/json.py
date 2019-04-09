#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

from json import JSONDecoder, JSONEncoder


class MZNJSONEncoder(JSONEncoder):
    def default(self, o):
        from minizinc.CLI import CLISolver
        if isinstance(o, set):
            return {"set": [i for i in o]}
        elif isinstance(o, CLISolver):
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
    def __init__(self, *args, **kwargs):
        JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    @staticmethod
    def object_hook(obj):
        from minizinc.CLI import CLISolver
        if len(obj) == 1 and "set" in obj:
            return set(obj["set"])
        elif all([i in obj.keys() for i in ["name", "version", "id", "executable"]]) \
                and all([i in CLISolver.FIELDS for i in obj.keys()]):
            return CLISolver._from_dict(obj)
        else:
            return obj
