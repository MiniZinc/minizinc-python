import contextlib
import tempfile
from pathlib import Path
from typing import List, Optional, Union

from ..instance import Instance, Method


class CLIInstance(Instance):
    _files: List[Path]
    _method: Optional[Method]
    _code_fragments: List[str]

    def __init__(self, files: Optional[List[Union[Path, str]]] = None, driver=None):
        super().__init__(files, driver)
        from minizinc.CLI import CLIDriver
        if not isinstance(self.driver, CLIDriver):
            raise TypeError(str(type(self.driver)) + " is not an instance of CLIDriver")
        self._parent = None
        self._method = None
        if files is None:
            self._files = []
        else:
            self._files = [Path(f) if isinstance(f, str) else f for f in files]
        self._code_fragments = []

    def add_to_model(self, code: str):
        self._code_fragments.append(code)

    @contextlib.contextmanager
    def files(self):
        files = self._files.copy()
        fragments = None
        if len(self._code_fragments) > 0:
            fragments = tempfile.NamedTemporaryFile(prefix="mzn_fragment", suffix=".mzn")
            for code in self._code_fragments:
                fragments.write(code.encode())
            fragments.flush()
            fragments.seek(0)
            files.append(Path(fragments.name))
        try:
            yield files
        finally:
            if fragments is not None:
                fragments.close()

    @property
    def method(self):
        if self._method is None:
            self.driver.analyse(self)
        return self._method

    def solve(self, solver, *args, **kwargs):
        """
        Forwarding method to the driver's solve method using the instance
        :param solver: the MiniZinc solver configuration to be used
        :param args, kwargs: accepts all other arguments found in the drivers solve method
        :return: A result object containing the solution to the instance
        """
        return self.driver.solve(solver, self, *args, **kwargs)
