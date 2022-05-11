API
===

.. module:: minizinc

This part of the documentation lists the full API reference of all public
classes and functions.

Solvers
-------

..  autoclass:: minizinc.solver.Solver
    :members:

Models
------

..  autoclass:: minizinc.model.Method

..  autoclass:: minizinc.model.Model
    :members:
    :special-members:  __getitem__, __setitem__

Instances
---------

..  autoclass:: minizinc.instance.Instance
    :members:
    :special-members:  __getitem__, __setitem__

Results
-------

..  autoclass:: minizinc.result.Result
    :members:
    :special-members:  __getitem__, __len__

..  autoclass:: minizinc.result.Status
    :members:

Drivers
-------

..  autoclass:: minizinc.driver.Driver
    :members:

Errors
------

..  autoexception:: minizinc.error.ConfigurationError
    :members:

..  autofunction:: minizinc.error.parse_error

..  autoexception:: minizinc.error.MiniZincError
    :members:

..  autoclass:: minizinc.error.Location

..  autoexception:: minizinc.error.EvaluationError
    :members:

..  autoexception:: minizinc.error.AssertionError
    :members:

..  autoexception:: minizinc.error.TypeError
    :members:

..  autoexception:: minizinc.error.SyntaxError
    :members:

Helper Functions
----------------

..  autofunction:: minizinc.helpers.check_result

..  autofunction:: minizinc.helpers.check_solution
