from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

import minizinc

from .driver import Driver


class Method(Enum):
    SATISFY = 1
    MINIMIZE = 2
    MAXIMIZE = 3

    @classmethod
    def from_string(cls, s: str):
        if s == "sat":
            return cls.SATISFY
        elif s == "min":
            return cls.MINIMIZE
        elif s == "max":
            return cls.MAXIMIZE
        else:
            raise ValueError("Unknown Method %r, valid options are 'sat', 'min', or 'max'" % s)


class Instance(ABC):
    driver: Driver

    @abstractmethod
    def __init__(self, files: Optional[List[Union[Path, str]]] = None, driver: Driver = None):
        if driver is None:
            if minizinc.default_driver is None:
                raise LookupError("Could not initiate instance without a given or default driver")
            self.driver = minizinc.default_driver
        else:
            self.driver = driver

    @abstractmethod
    def add_to_model(self, code: str):
        pass

    @property
    @abstractmethod
    def method(self):
        pass

    def solve(self, solver, *args, **kwargs):
        """
        Forwarding method to the driver's solve method using the instance
        :param solver: the MiniZinc solver configuration to be used
        :param args, kwargs: accepts all other arguments found in the drivers solve method
        :return: A result object containing the solution to the instance
        """
        return self.driver.solve(solver, self, *args, **kwargs)
