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




