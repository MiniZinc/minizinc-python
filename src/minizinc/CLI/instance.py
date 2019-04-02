#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import contextlib
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Type

from minizinc.model import Model

from ..instance import Instance, Method
from .solver import CLISolver


class CLIInstance(Instance):
    _solver: CLISolver
    _input: Optional[Dict[str, Type]]
    _method: Optional[Method]
    _parent: Optional[Instance]

    def __init__(self, solver: CLISolver, model: Optional[Model] = None):
        super().__init__(solver, model)
        self._solver = solver
        self._parent = None
        self._method = None
        self._input = None
        if model is not None:
            self._includes = model._includes[:]
            self._code_fragments = model._code_fragments[:]
            self._data = dict.copy(model._data)

    @contextlib.contextmanager
    def branch(self) -> Instance:  # TODO: Self reference
        child = self.__class__(self._solver)
        child._parent = self
        try:
            yield child
        finally:
            del child

    @property
    def method(self) -> Method:
        if self._method is None:
            self._solver.analyse(self)
        return self._method

    @contextlib.contextmanager
    def files(self) -> List[Path]:
        """Gets list of files of the Instance

        Files will create a list of paths to the files that together form the Instance. Parts of the Instance might be
        saved to files and are only guaranteed to exist while within the created context.

        Yields:
            List of Path objects to existing and created files
        """
        files: List[Path] = self._includes.copy()
        fragments = None
        data = None
        if len(self._code_fragments) > 0:
            fragments = tempfile.NamedTemporaryFile(prefix="mzn_fragment", suffix=".mzn")
            for code in self._code_fragments:
                fragments.write(code.encode())
            fragments.flush()
            fragments.seek(0)
            files.append(Path(fragments.name))
        if len(self._data) > 0:
            data = tempfile.NamedTemporaryFile(prefix="mzn_data", suffix=".json")
            data.write(json.dumps(self._data).encode())
            data.flush()
            data.seek(0)
            files.append(Path(data.name))
        try:
            if self._parent is not None:
                assert isinstance(self._parent, CLIInstance)
                with self._parent.files() as pfiles:
                    yield pfiles + files
            else:
                yield files
        finally:
            if fragments is not None:
                fragments.close()
            if data is not None:
                data.close()

    @property
    def input(self):
        if self._input is None:
            self._solver.analyse(self)
        return self._input

    @input.setter
    def input(self, value):
        self._input = value

    def solve(self, *args, **kwargs):
        return self._solver.solve(self, *args, **kwargs)

    def from_model(self):
        pass
