CHANGELOG
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/>`_ and
this project adheres to `Semantic Versioning <https://semver.org/>`_.

Unreleased_
------------

0.4.2_ - 2020-11-25
-------------------

Fixed
^^^^^

- Terminate the MiniZinc process when stopping early (instead of killing it).
  This allows MiniZinc to correctly stop any solver processes.

Changed
^^^^^^^

- Revert change from 0.4.1 where enumerated types unknown to Python would be
  made stored as anonymous enumerations. Interoperability between the MiniZinc
  driver and the MiniZinc Python has instead changed to allow JSON strings as
  valid input for enumerated types. (required MiniZinc 2.5.3)

0.4.1_ - 2020-11-11
-------------------

Added
^^^^^
- Support for Python 3.9. (MiniZinc Python will aim to support all versions of
  Python that are not deprecated)
- Experimental support for capturing the error output of the MiniZinc process
  in ``CLIInstance``.
- Experimental support for verbose compiler and solver output (using the ``-v``
  flag) in ``CLIInstance``.

Changed
^^^^^^^
- The MiniZinc Python repository moved from GitLab to GitHub, replacing GitLab
  CI for GitHub Actions for the continuous testing.
- Values of an enumerated type defined in MiniZinc will now appear in solutions
  as a member of a singular anonymous ``enum.Enum`` class.

Fixed
^^^^^
- Handle the cancellation of asynchronous solving and correctly dispose of the
  process
- Correct the JSON representation of sets of with ``IntEnum`` members. (Lists
  are still not correctly represented).
- ``check_solution`` will now correctly handle solution values of an enumerated
  type defined in MiniZinc.

0.4.0_ - 2020-10-06
-------------------

Changed
^^^^^^^
- The ``check_solution`` has been split into two separate functions. The
  ``check_result`` function allows the user to check the correctness of a
  ``Result`` object and the new ``check_solution`` function can check the
  correctness of an individual solution in the form of a data class object or a
  dictionary.
- ``Model.add_file`` no longer has its ``parse_data`` flag enabled by default.

Fixed
^^^^^
- Catch lark ``ImportError`` before ``LarkError`` during ``Model.add_file()`` since
  ``LarkError`` will not exist if the import failed.
- Ensure a DZN file does not get included if its data is parsed.

0.3.3_ - 2020-08-17
-------------------

Added
^^^^^
- Add ``requiredFlags`` field to the ``Solver`` data class.

Fixed
^^^^^
- Ignore extra (undocumented) fields from MiniZinc's ``--solvers-json`` output
  when initialising ``Solver`` objects.

0.3.2_ - 2020-08-14
-------------------

Fixed
^^^^^
- Add full support for string input and output. The usage of strings would
  previously incorrectly give a warning.

0.3.1_ - 2020-07-21
-------------------

Changed
^^^^^^^
- Store path of loaded solver configuration paths so that no configuration file
  has to be generated if no changes are made to the solver.

Fixed
^^^^^
- Ensure generated solver configurations exists during the full existence of
  the created asynchronous process.


0.3.0_ - 2020-07-21
-------------------

Added
^^^^^
- Add support for different MiniZinc compiler optimisation levels. All methods that
  compile an instance now have an additional `optimisation_level` argument.

Changed
^^^^^^^
- The DZN parser functionality has been moved into the ``dzn`` extra. If your
  application requires parsed ``dzn`` information, then you have to ensure your
  MiniZinc Python is installed with this extra enabled:
  ``pip install minizinc[dzn]``.
- ``Solver`` has been turned into a ``dataclass`` and has been updated with all
  attributes used in the compiler.

Fixed
^^^^^
- Resolve relative paths when directly loading a solver configuration. This
  ensures that when a temporary solver configuration is created, the paths are
  correct.

0.2.3_ - 2020-03-31
-------------------

Changed
^^^^^^^
- Add text to the empty MiniZincError that occurs when MiniZinc exits with a non-zero
  exit status

Fixed
^^^^^
- Close generated solver configuration before handing it to MiniZinc. This fixes the
  usage of generated solver configurations on Windows.
- The DZN parser now constructs correct range objects. The parser was off by one due to
  the exclusive upper bound in Python range objects.
- Rewrite MiniZinc fields that are keywords in Python. These names cannot be used
  directly as members of a dataclass. Python keywords used in MiniZinc are rewritten to
  ``"mzn_" + {keyword}`` and a warning is thrown.

0.2.2_ - 2020-02-17
-------------------

Added
^^^^^
- Add output property to ``CLIInstance`` to expose the output interface given by
  MiniZinc.

Changed
^^^^^^^
- Improved interaction with solution checker models. Solution checkers can
  now be added to an ```Instance``/``Model`` and an ``check`` method will be
  added to the generated solution objects.
- Change the Python packaging system back to setuptools due to the excessive
  required dependencies of Poetry.

Fixed
^^^^^
- Fix the MiniZinc output parsing of sets of an enumerated type.
- Fix the TypeError that occurred when a hard timeout occurred.
- Allow trailing commas for sets and arrays in DZN files.

0.2.1_ - 2020-01-13
-------------------

Added
^^^^^
- Add support for other command line flags for ``CLIInstance.flatten()``
  through the use of ``**kwargs``.
- Add initial ``Checker`` class to allow the usage of MiniZinc solution
  checkers.

Changed
^^^^^^^
- The string method for ``Result`` will now refer to the string method of its
  ``Solution`` attribute.

Fixed
^^^^^
- Ensure the event loop selection on Windows to always selects
  ``ProactorEventLoop``. This ensures the usage on Windows when the python
  version ``<= 3.8.0``.

0.2.0_ - 2019-12-13
-------------------

Added
^^^^^
- Support and testing for Python 3.8
- Logging of started processes and attributes of generated output items
- Export `Pygments <https://pygments.org>`_ Lexer for MiniZinc

Changed
^^^^^^^
- ``Driver.check_version`` now raises an ``ConfigurationError`` exception
  when an incompatible function is detected; otherwise, the method not return a
  value.
- Output classes generated by ``CLIIinstance.analyse()`` no longer contain
  the `_output_item` `str` attribute when MiniZinc does not find a output item.
  (New in MiniZinc 2.3.3)
- Improved parsing of non-standard (numerical) statistical information
  provided by the solver.

Fixed
^^^^^
- ``CLIInstance.solutions()``: The separator detection is now OS independent.
  The separator previously included a ``\n`` literal instead of ``\r\n`` on
  Windows.
- Solve an issue in ``CLIInstance.solution()`` where a solution with a size
  bigger than the buffer size would result in a ``LimitOverrunError`` exception.
- Correctly catch the ``asyncio.TimeoutError`` and kill the process when
  reaching a hard timeout. (i.e., the solver and ``minizinc`` do not stop in
  time)
- Check if file exists before opening file when an error occurs. (File might
  have been part of a compiled solver)
- Ensure the ``objective`` attribute is only added to the generated solution
  type once
- Remove '\r' characters from input when parsing statistics (Windows Specific).


0.1.0_ - 2019-10-11
---------------------

Initial release of MiniZinc Python. This release contains an initial
functionality to use MiniZinc directly from Python using an interface to the
``minizinc`` command line application. The exact functionality available in this
release is best described in the `documentation
<https://minizinc-python.readthedocs.io/en/0.1.0/>`_.


..  _0.4.2: https://github.com/MiniZinc/minizinc-python/compare/0.4.1...0.4.2
..  _0.4.1: https://github.com/MiniZinc/minizinc-python/compare/0.4.0...0.4.1
..  _0.4.0: https://github.com/MiniZinc/minizinc-python/compare/0.3.3...0.4.0
..  _0.3.3: https://github.com/MiniZinc/minizinc-python/compare/0.3.2...0.3.3
..  _0.3.2: https://github.com/MiniZinc/minizinc-python/compare/0.3.1...0.3.2
..  _0.3.1: https://github.com/MiniZinc/minizinc-python/compare/0.3.0...0.3.1
..  _0.3.0: https://github.com/MiniZinc/minizinc-python/compare/0.2.3...0.3.0
..  _0.2.3: https://github.com/MiniZinc/minizinc-python/compare/0.2.2...0.2.3
..  _0.2.2: https://github.com/MiniZinc/minizinc-python/compare/0.2.1...0.2.2
..  _0.2.1: https://github.com/MiniZinc/minizinc-python/compare/0.2.0...0.2.1
..  _0.2.0: https://github.com/MiniZinc/minizinc-python/compare/0.1.0...0.2.0
..  _0.1.0: https://github.com/MiniZinc/minizinc-python/compare/d14654d65eb747470e11c10747e6dd49baaab0b4...0.1.0
..  _Unreleased: https://github.com/MiniZinc/minizinc-python/compare/stable...prime
