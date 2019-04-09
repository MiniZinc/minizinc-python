#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import warnings
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from lark.exceptions import LarkError

from .dzn import parse_dzn

ParPath = Union[Path, str]


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


class Model:
    _data: Dict[str, Any]
    _includes: List[Path]
    _code_fragments: List[str]

    def __init__(self, files: Optional[Union[ParPath, List[ParPath]]] = None):
        self._data = {}
        self._includes = []
        self._code_fragments = []
        if isinstance(files, Path) or isinstance(files, str):
            self.add_file(files)
        elif files is not None:
            for file in files:
                self.add_file(file)

    def __setitem__(self, key: str, value: Any):
        """Set parameter of Model.

        This method overrides the default implementation of item access (``obj[key] = value``) for models. Item
        access on a Model can be used to set parameters of the Model.

        Args:
            key (str): Identifier of the parameter.
            value (Any): Value to be assigned to the parameter.
        """
        if self._data.get(key, None) is None:
            self._data.__setitem__(key, value)
        else:
            if self._data[key] != value:
                raise AssertionError("The parameter '%s' cannot be assigned multiple values. If you are changing the "
                                     "model, consider using the branch method before assigning the parameter")

    def __getitem__(self, key: str) -> Any:
        """Get parameter of Model.

        This method overrides the default implementation of item access (``obj[key]``) for models. Item access on a
        Model can be used to get parameters of the Model.

        Args:
            key (str): Identifier of the parameter.

        Returns:
            The value assigned to the parameter.

        Raises:
            KeyError: The parameter you are trying to access is not known.
        """
        return self._data.__getitem__(key)

    def add_file(self, file: ParPath) -> None:
        """Adds a MiniZinc file (``.mzn``, ``.dzn``, or ``.json``) to the Model.

        Args:
            file (Union[Path, str]): Path to the file to be added
        """
        if not isinstance(file, Path):
            file = Path(file)
        assert file.exists()
        if file.suffix == ".json":
            data = json.load(file.open())
            for k, v in data.items():
                self.__setitem__(k, v)
        elif file.suffix == ".dzn":
            try:
                data = parse_dzn(file)
                for k, v in data.items():
                    self.__setitem__(k, v)
            except LarkError:
                warnings.warn("Could not parse %s. Parameters included within this file are not available in Python"
                              % file)
                self._includes.append(file)
        elif file.suffix != ".mzn":
            raise NameError("Unknown file suffix %s", file.suffix)
        else:
            self._includes.append(file)

    def add_string(self, code: str) -> None:
        """Adds a string of MiniZinc code to the Model.

        Args:
            code (str): A string contain MiniZinc code
        """
        self._code_fragments.append(code)

    def __copy__(self):
        copy = self.__class__()
        copy._includes = self._includes[:]
        copy._code_fragments = self._code_fragments[:]
        copy._data = dict.copy(self._data)
