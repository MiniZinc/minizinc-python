import os
from sys import platform
from typing import Optional

from minizinc.driver import load_minizinc, Driver
from minizinc.model import Model

Instance = None
Solver = None

#: Default MiniZinc driver used by the python package
default_driver: Optional[Driver] = None
load_minizinc(set_default=True)
if default_driver is None:
    import warnings
    warnings.warn("MiniZinc was not found on the system: no default driver could be initialised", RuntimeWarning)
