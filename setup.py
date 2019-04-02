#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
from pathlib import Path

from setuptools import find_packages, setup

setup(
    name="minizinc",
    version="0.1.0-alpha.2",
    python_requires='>=3.6',
    author="Jip J. Dekker",
    author_email="jip.dekker@monash.edu",
    description="Access MiniZinc directly from Python",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    url="http://minizinc.org",
    project_urls={
        'Bug Tracker': 'https://gitlab.com/minizinc/python/issues',
        "Documentation": "https://minizinc-python.readthedocs.io",
        'Source': 'https://gitlab.com/minizinc/python',
    },
    packages=find_packages(where="src"),
    package_dir={'': 'src'},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
    install_requires=['lark-parser']
)
