import json
from abc import ABC, abstractmethod
from typing import List

import minizinc

from .instance import Instance


class Solver(ABC):
    # Solver Configuration Options
    name: str
    version: str
    mznlib: str
    tags: List[str]
    stdFlags = List[str]
    extraFlags = List[str]
    executable: str
    supportsMzn: bool
    supportsFzn: bool
    needsSolns2Out: bool
    needsMznExecutable: bool
    needsStdlibDir: bool
    isGUIApplication: bool

    @abstractmethod
    def __init__(self, name: str, version: str, executable: str, driver=None):
        if driver is None:
            if minizinc.default_driver is None:
                raise LookupError("Could not initiate instance without a given or default driver")
            self.driver = minizinc.default_driver
        self.driver = driver

    @property
    @abstractmethod
    def id(self) -> str:
        pass

    def solve(self, instance: Instance, *args, **kwargs):
        """
        Forwarding method to the driver's solve method using the solver configuration
        :param instance: the MiniZinc instance to be solved
        :param args, kwargs: accepts all other arguments found in the drivers solve method
        :return: A result object containing the solution to the instance
        """
        if self.driver is not None:
            return self.driver.solve(self, instance, *args, **kwargs)
        else:
            raise LookupError("Solver is not linked to a MiniZinc driver")

    def to_json(self):
        info = {
            "name": self.name,
            "version": self.version,
            "id": self.id,
            "executable": self.executable,
            "mznlib": self.mznlib,
            "tags": self.tags,
            "stdFlags": self.stdFlags,
            "extraFlags": self.extraFlags,
            "supportsMzn": self.supportsMzn,
            "supportsFzn": self.supportsFzn,
            "needsSolns2Out": self.needsSolns2Out,
            "needsMznExecutable": self.needsMznExecutable,
            "needsStdlibDir": self.needsStdlibDir,
            "isGUIApplication": self.isGUIApplication,
        }

        return json.dumps(info, sort_keys=True, indent=4)
