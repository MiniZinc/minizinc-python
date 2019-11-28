CHANGELOG
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/>`_ and
this project adheres to `Semantic Versioning <https://semver.org/>`_.

Unreleased_
------------

Added
^^^^^
- Support and testing for Python 3.8
- Logging of started processes and attributes of generated output items

Changed
^^^^^^^
- ``Driver.check_version`` now raises an ``ConfigurationError`` exception
  when an incompatible function is detected; otherwise, the method not return a
  value.

Fixed
^^^^^
- ``CLIInstance.solutions()``: The separator detection is now OS independent.
  The separator previously included a ``\n`` literal instead of ``\r\n`` on
  Windows.


0.1.0_ - 2019-10-11
---------------------

Initial release of MiniZinc Python. This release contains an initial
functionality to use MiniZinc directly from Python using an interface to the
``minizinc`` command line application. The exact functionality available in this
release is best described in the `documentation
<https://minizinc-python.readthedocs.io/en/0.1.0/>`_.


..  _Unreleased: https://gitlab.com/minizinc/minizinc-python/compare/master...develop
..  _0.1.0: https://gitlab.com/minizinc/minizinc-python/compare/d14654d65eb747470e11c10747e6dd49baaab0b4...0.1.0
