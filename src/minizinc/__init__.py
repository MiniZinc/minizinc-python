#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
import logging
import warnings
from typing import Optional

from .driver import Driver
from .error import ConfigurationError, MiniZincError
from .instance import Instance
from .model import Method, Model
from .result import Result, Status
from .solver import Solver
from .types import AnonEnum, ConstrEnum

__version__ = "0.7.0"

logger = logging.getLogger("minizinc")

#: Default MiniZinc driver used by the python package
try:
    default_driver: Optional[Driver] = Driver.find()
    if default_driver is not None:
        default_driver.make_default()
    else:
        warnings.warn(
            "MiniZinc was not found on the system. No default driver could be "
            "initialised.",
            RuntimeWarning,
        )
except ConfigurationError as err:
    warnings.warn(
        f"The MiniZinc version found on the system is incompatible with "
        f"MiniZinc Python:\n{err}\n No default driver could be initialised.",
        RuntimeWarning,
    )

__all__ = [
    "__version__",
    "default_driver",
    "AnonEnum",
    "ConstrEnum",
    "Driver",
    "Instance",
    "Method",
    "MiniZincError",
    "Model",
    "Result",
    "Solver",
    "Status",
]
