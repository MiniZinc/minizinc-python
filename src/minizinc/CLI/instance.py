#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import contextlib
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from ..instance import Instance, Method


class CLIInstance(Instance):
    data: Dict[str, Any]
    _input: Optional[Dict[str, Type]]
    _files: List[Path]
    _method: Optional[Method]
    _code_fragments: List[str]
    _parent: Optional[Instance]

    def __init__(self, files: Optional[List[Union[Path, str]]] = None):
        super().__init__(files)
        self._parent = None
        self._method = None
        self._input = None
        self.data = {}
        if files is None:
            self._files = []
        else:
            self._files = [Path(f) if isinstance(f, str) else f for f in files]
        self._code_fragments = []

    def __setitem__(self, key, value):
        self.data.__setitem__(key, value)

    def __getitem__(self, *args, **kwargs):
        self.data.__getitem__(*args, **kwargs)

    def add_to_model(self, code: str):
        self._code_fragments.append(code)

    @contextlib.contextmanager
    def files(self) -> List[Path]:
        """Gets list of files of the Instance

        Files will create a list of paths to the files that together form the Instance. Parts of the Instance supplied
        as files will remain in this form. Code fragments and parameter data that was supplied separately will be saved
        to files and are only guaranteed to exist while within the created context.

        Yields:
            List of Path to create the Instance from the CLI
        """
        files: List[Path] = self._files.copy()
        fragments = None
        data = None
        if len(self._code_fragments) > 0:
            fragments = tempfile.NamedTemporaryFile(prefix="mzn_fragment", suffix=".mzn")
            for code in self._code_fragments:
                fragments.write(code.encode())
            fragments.flush()
            fragments.seek(0)
            files.append(Path(fragments.name))
        if len(self.data) > 0:
            data = tempfile.NamedTemporaryFile(prefix="mzn_data", suffix=".json")
            data.write(json.dumps(self.data).encode())
            data.flush()
            data.seek(0)
            files.append(Path(data.name))
        try:
            if self._parent is not None:
                with self._parent.files() as parent:
                    files.extend(parent)
                    yield files
            else:
                yield files
        finally:
            if fragments is not None:
                fragments.close()
            if data is not None:
                data.close()

    @contextlib.contextmanager
    def branch(self) -> Instance:  # TODO: Self reference
        child = self.__class__()
        child._parent = self
        try:
            yield child
        finally:
            del child

    @property
    def method(self) -> Method:
        if self._method is None:
            self.driver.analyse(self)
        return self._method

    @property
    def input(self):
        if self._input is None:
            self.driver.analyse(self)
        return self._input

    @input.setter
    def input(self, value):
        self._input = value

    def solve(self, solver, *args, **kwargs):
        return self.driver.solve(solver, self, *args, **kwargs)
