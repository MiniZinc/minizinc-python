#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

from abc import ABC, abstractmethod
from typing import Optional

from .model import Method, Model
from .solver import Solver


class Instance(Model, ABC):
    """Abstract representation of a MiniZinc instance in Python.
    """

    @abstractmethod
    def __init__(self, solver: Solver, model: Optional[Model] = None):
        super().__init__()

    @property
    @abstractmethod
    def method(self) -> Method:
        """Query the Method used by the Instance.

        Returns:
            Method: Method of the goal used by the Instance.
        """
        pass

    @abstractmethod
    def solve(self, *args, **kwargs):
        """Solve instance using the solver driver with which it was initialised.

        Solve is a forwarding method to the Solver solve method that will use the current instance and the supplied
        solver configuration.

        Args:
            *args: Arguments to be forwarded to the Driver solve method.
            **kwargs: Keyword arguments to be forwarded to the Driver solve method.

        Returns:
            Result: A MiniZinc Result object.
        """
        pass
