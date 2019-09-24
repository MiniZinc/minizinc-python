Advanced Usage
==============

This page provides examples of usages of MiniZinc Python other than solving just
a basic model instance.


Custom Output Type
------------------

You can change the type in which MiniZinc Python will provide its solutions. By
default the output type will automatically be generated for every mode, but it
can be changed by setting the `output_type` attribute of a model or instance.
This can be useful if you require the data in a particular format for later use.
The following example solves a task assignment problem and its result will store
the solutions in a class with an additional method to check that the tasks in
the solution are scheduled uniquely.


..  literalinclude:: examples/output_type.py
    :language: python


Concurrent Solving
------------------

MiniZinc Python provides asynchronous methods for solving MiniZinc instances.
These methods can be used to concurrently solve an instances and/or use some of
pythons other functionality. The following code sample shows a MiniZinc instance
that is solved by two solvers at the same time. The solver that solves the
instance the fastest is proclaimed the winner!

..  literalinclude:: examples/solver_race.py
    :language: python



Concurrent Solutions
--------------------

MiniZinc Python provides an asynchronous generator to receive the generated
solutions. The generator allows users to process solutions as they come in. The
following example solves the n-queens problem and displays a board with the
letter Q on any position that contains a queen.

..  literalinclude:: examples/show_queens.py
    :language: python


..  _multiple-minizinc:
               
Using multiple MiniZinc versions
--------------------------------

MiniZinc Python is designed to be flexible in its communication with MiniZinc.
That is why it is possible to switch to a different version of MiniZinc, or even
use multiple versions of MiniZinc at the same time. This can be useful to
compare different versions of MiniZinc.

In MiniZinc Python a MiniZinc executable or shared library is represented by a
:class:`Driver` object. The :func:`find_driver` function can help finding a
compatible MiniZinc executable or shared library and create an associated Driver
object. The following example shows how to load two versions of MiniZinc and
sets one as the new default.

..  code-block:: python

    from minizinc import Driver, Instance, Solver, default_driver, find_driver

    print(default_driver.minizinc_version)

    v23: Driver = find_driver(["/minizinc/2.3.2/bin"])
    print(v23.minizinc_version)
    gecode = Solver.lookup("gecode", driver=v23)
    v23_instance = Instance(gecode, driver=v23)

    v24: Driver = find_driver(["/minizinc/2.4.0/bin"])
    print(v24.minizinc_version)
    gecode = Solver.lookup("gecode", driver=v24)
    v24_instance = Instance(gecode, driver=v24)

    v24.make_default()
    print(default_driver.minizinc_version)
    gecode = Solver.lookup("gecode")  # using the new default_driver
    instance = Instance(gecode)

..  seealso::

    For more information about how MiniZinc Python connect to MiniZinc using
    either an executable or shared library, please read about the :ref:`library
    structure <library-structure>`
