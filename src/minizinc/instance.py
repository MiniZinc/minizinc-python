import contextlib
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Union

import minizinc

from .driver import Driver


class Method(Enum):
    """Enumeration that represents of a solving method.

    Attributes:
        SATISFY: Represents a satisfaction problem.
        MINIMIZE: Represents a minimization problem.
        MAXIMIZE: Represents a maximization problem.
    """
    SATISFY = 1
    MINIMIZE = 2
    MAXIMIZE = 3

    @classmethod
    def from_string(cls, s: str):
        """Get Method represented by the string s.

        Args:
            s:

        Returns:
            Method: Method represented by s
        """
        if s == "sat":
            return cls.SATISFY
        elif s == "min":
            return cls.MINIMIZE
        elif s == "max":
            return cls.MAXIMIZE
        else:
            raise ValueError("Unknown Method %r, valid options are 'sat', 'min', or 'max'" % s)


class Instance(ABC):
    """Abstract representation of a MiniZinc instance in Python.

    Attributes:
        driver (Driver): The Driver used to interact with MiniZinc functionality.
    """
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
    def __setitem__(self, key: str, value: Any):
        """Set parameter of Instance.

        This method overrides the default implementation of item access (``obj[key] = value``) for instances. Item
        access on a Instance can be used to set parameters of the Instance.

        Args:
            key (str): Identifier of the parameter.
            value (Any): Value to be assigned to the parameter.
        """
        pass

    @abstractmethod
    def __getitem__(self, key: str) -> Any:
        """Get parameter of Instance.

        This method overrides the default implementation of item access (``obj[key]``) for instances. Item access on a
        Instance can be used to get parameters of the Instance.
        **Parameters not set through Python can not be accessed.**

        Args:
            key (str): Identifier of the parameter.

        Returns:
            The value assigned to the parameter.

        Raises:
            KeyError: The parameter you are trying to access is not known.
        """
        pass

    @abstractmethod
    def add_to_model(self, code: str) -> None:
        """Adds a string of MiniZinc code to the Instance.

        Args:
            code (str): A string contain MiniZinc code
        """
        pass

    @contextlib.contextmanager
    @abstractmethod
    def branch(self):
        """Creates new child of the Instance.

        Branch creates a new child of the instance that will inherit everything from the instance, but can be
        specialised to to solve sub-problems. Specialisations to the child instance will not change the parent instance.

        Yields:
            Instance: a new child of the current Instance.
        """
        pass

    @property
    @abstractmethod
    def method(self) -> Method:
        """Query the Method used by the Instance.

        Returns:
            Method: Method of the goal used by the Instance.
        """
        pass

    def solve(self, solver, *args, **kwargs):
        """Solve instance using supplied solver.

        Solve is a forwarding method to the Driver solve method that will use the current instance and the supplied
        solver configuration.

        Args:
            solver (Solver): A MiniZinc solver configuration.
            *args: Arguments to be forwarded to the Driver solve method.
            **kwargs: Keyword arguments to be forwarded to the Driver solve method.

        Returns:
            Result: A MiniZinc Result object.
        """
        return self.driver.solve(solver, self, *args, **kwargs)
