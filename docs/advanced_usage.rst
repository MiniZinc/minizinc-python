Advanced Usage
==============

This page provides examples of usages of MiniZinc Python other than solving just
a basic model instance.


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




