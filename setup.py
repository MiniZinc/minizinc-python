#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
from pathlib import Path

from setuptools import find_packages, setup

setup(
    name="minizinc",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    python_requires=">=3.6",
    author="Jip J. Dekker",
    author_email="jip.dekker@monash.edu",
    description="Access MiniZinc directly from Python",
    long_description=Path("README.md").read_text(encoding="UTF-8"),
    long_description_content_type="text/markdown",
    url="https://www.minizinc.org/",
    project_urls={
        "Bug Tracker": "https://github.com/MiniZinc/minizinc-python/issues",
        "Documentation": "https://minizinc-python.readthedocs.io",
        "Source": "https://github.com/MiniZinc/minizinc-python",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
    install_requires=[
        "dataclasses>=0.6.0; python_version < '3.7'",
    ],
    extras_require={
        "dzn": ["lark-parser>=0.7.5"],
    },
    entry_points='''
        [pygments.lexers]
        minizinclexer = minizinc.pygments:MiniZincLexer
    '''
)
