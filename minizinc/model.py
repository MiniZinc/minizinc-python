import os
import tempfile
from pathlib import Path


class Model:
    def __init__(self, model: str):
        self._mem = model
        self._file = None

    @property
    def file(self):
        if self._file is None:
            self._file = tempfile.NamedTemporaryFile(prefix="minizinc_model_", suffix=".mzn")
            self._file.write(self._mem.encode())
            self._file.flush()
            self._file.seek(0)
        return self._file.name

    def __del__(self):
        if self._file is not None:
            self._file.close()


class Instance:
    method: Method

    def __init__(self, model, data=None):
        self.files: list[Path] = []
        if isinstance(model, Model):
            self.files.append(Path(model.file))
        else:
            self.files.append(Path(os.path.abspath(model)))
        if data is not None:
            self.files.append(Path(os.path.abspath(data)))