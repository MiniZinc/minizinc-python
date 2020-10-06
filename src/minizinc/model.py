#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import threading
import warnings
from enum import Enum, EnumMeta
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

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
            s: String expected to contain either "sat", "min", or "max".

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
            raise ValueError(
                f"Unknown Method {s}, valid options are 'sat', 'min', or 'max'"
            )


class UnknownExpression(str):
    pass


class Model:
    """The representation of a MiniZinc model in Python

    Attributes:
        output_type (Type): the type used to store the solution values created
            in the process of solving the Instance. This attribute is
            particularly helpful when comparing the results of multiple
            instances together. The type must support initialisation with the
            assignments returned by MiniZinc. These assignments currently
            always include "__output_item" and include "objective" if the
            instance is not a satisfaction problem.

    Raises:
        MiniZincError: when an error occurs during the parsing or
            type checking of the model object.
    """

    output_type: Optional[Type] = None

    _code_fragments: List[str]
    _data: Dict[str, Any]
    _enum_map: Dict[str, Enum]
    _includes: List[Path]
    _lock: threading.Lock
    _checker: bool = False

    def __init__(self, files: Optional[Union[ParPath, List[ParPath]]] = None):
        self._data = {}
        self._includes = []
        self._code_fragments = []
        self._enum_map = {}
        self._lock = threading.Lock()
        if isinstance(files, Path) or isinstance(files, str):
            self.add_file(files)
        elif files is not None:
            for file in files:
                self.add_file(file)

    def __setitem__(self, key: str, value: Any):
        """Set parameter of Model.

        This method overrides the default implementation of item access
        (``obj[key] = value``) for models. Item access on a Model can be used to
        set parameters of the Model.

        Args:
            key (str): Identifier of the parameter.
            value (Any): Value to be assigned to the parameter.
        """
        with self._lock:
            if self._data.get(key, None) is None:
                if isinstance(value, EnumMeta):
                    self._register_enum_values(value)
                self._data.__setitem__(key, value)
            else:
                if self._data[key] != value:
                    # TODO: Fix the error type and document
                    raise AssertionError(
                        f"The parameter '{key}' cannot be assigned multiple values. "
                        f"If you are changing the model, consider using the branch "
                        f"method before assigning the parameter."
                    )

    def _register_enum_values(self, t: EnumMeta):
        for name in t.__members__:
            if name in self._enum_map:
                # TODO: Fix the error type and document
                raise AssertionError(
                    f"Identifier '{name}' is used in multiple enumerated types"
                    f"within the same model. Identifiers in enumerated types "
                    f"have to be unique."
                )
            self._enum_map[name] = t.__members__[name]

    def __getitem__(self, key: str) -> Any:
        """Get parameter of Model.

        This method overrides the default implementation of item access
        (``obj[key]``) for models. Item access on a Model can be used to get
        parameters of the Model.

        Args:
            key (str): Identifier of the parameter.

        Returns:
            The value assigned to the parameter.

        Raises:
            KeyError: The parameter you are trying to access is not known.

        """
        return self._data.__getitem__(key)

    def add_file(self, file: ParPath, parse_data: bool = False) -> None:
        """Adds a MiniZinc file (``.mzn``, ``.dzn``, or ``.json``) to the Model.

        Args:
            file (Union[Path, str]): Path to the file to be added
            parse_data (bool): Signal if the data should be parsed for usage
                within Python. This option is ignored if the extra `dzn` is
                not enabled.
        Raises:
            MiniZincError: when an error occurs during the parsing or
                type checking of the model object.
        """
        if not isinstance(file, Path):
            file = Path(file)
        assert file.exists()
        if not parse_data:
            with self._lock:
                self._includes.append(file)
            return
        if file.suffix == ".json":
            data = json.load(file.open())
            for k, v in data.items():
                self.__setitem__(k, v)
        elif file.suffix == ".dzn" and parse_data:
            try:
                from lark.exceptions import LarkError

                from .dzn import parse_dzn

                try:
                    data = parse_dzn(file)
                    for k, v in data.items():
                        self.__setitem__(k, v)
                except LarkError:
                    warnings.warn(
                        f"Could not parse {file}. Parameters included within this file "
                        f"are not available in Python"
                    )
                    with self._lock:
                        self._includes.append(file)
            except ImportError:
                with self._lock:
                    self._includes.append(file)
        elif file.suffix not in [".dzn", ".mzn", ".mzc"]:
            raise NameError("Unknown file suffix %s", file.suffix)
        else:
            with self._lock:
                if ".mzc" in file.suffixes:
                    self._checker = True
                self._includes.append(file)

    def add_string(self, code: str) -> None:
        """Adds a string of MiniZinc code to the Model.

        Args:
            code (str): A string contain MiniZinc code
        Raises:
            MiniZincError: when an error occurs during the parsing or
                type checking of the model object.
        """
        with self._lock:
            self._code_fragments.append(code)

    def __copy__(self):
        copy = self.__class__()
        copy._includes = self._includes[:]
        copy._code_fragments = self._code_fragments[:]
        copy._data = dict.copy(self._data)
        return copy
