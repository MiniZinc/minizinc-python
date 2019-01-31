API
===

.. module:: minizinc

This part of the documentation lists the full API reference of all public classes and functions.

Solvers
-------

..  autoclass:: minizinc.solver.Solver
    :members:

..  autoclass:: minizinc.CLI.CLISolver
    :members:

Instances
---------

..  autoclass:: minizinc.instance.Instance
    :members:

.. autoclass:: minizinc.instance.Method

..  autoclass:: minizinc.CLI.CLIInstance
    :members:

Results
-------

..  autoclass:: minizinc.result.Result
    :members:

..  autoclass:: minizinc.result.Status
    :members:

Utilities
---------

..  autofunction:: find_driver

Drivers
-------

..  autoclass:: minizinc.driver.Driver
    :members:

..  autoclass:: minizinc.CLI.CLIDriver
    :members:

Errors
------

..  autofunction:: minizinc.error.parse_error

..  autoexception:: minizinc.error.MiniZincError
    :members:

..  autoclass:: minizinc.error.Location
    :members:

..  autoexception:: minizinc.error.EvaluationError
    :members:

..  autoexception:: minizinc.error.MiniZincAssertionError
    :members:

..  autoexception:: minizinc.error.MiniZincTypeError
    :members:

..  autoexception:: minizinc.error.MiniZincSyntaxError
    :members:
