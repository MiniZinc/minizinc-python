import os
from pathlib import Path


def append_environment(key: str, path: Path):
    tmp = os.environ.get(key, None)
    if tmp is None:
        os.environ[key] = str(path)
    else:
        os.environ[key] += os.pathsep + str(path)
