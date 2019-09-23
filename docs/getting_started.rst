Getting Started
===============

This page will guide you through the process of setting up MiniZinc Python.
MiniZinc Python requires the following software to be installed on you machine:

- `MiniZinc <https://www.minizinc.org/>`_ 2.2.3 (or higher)
- `Python <https://www.python.org/>`_ 3.6 (or higher)

..  note::

    MiniZinc is expected to be in its default location. If you are on a Linux
    machine or changed this location, then you will have to ensure that the
    ``minizinc`` executable is located in a folder in the ``$PATH``
    environmental variable. When MiniZinc cannot be located, the following
    warning will be shown: **MiniZinc was not found on the system: no default
    driver could be initialised**. The path can manually be provided using
    ``find_driver`` function.

Installation
------------

MiniZinc Python can be found on `PyPI <https://pypi.org/project/minizinc/>`_. If
you have the ``pip`` package manager installed, then the simplest way of
installing MiniZinc Python is using the following command:

..  code-block:: bash

    $ pip install minizinc

..  note::

    On machines that have both Python 2 and Python 3 installed you might have to
    use ``pip3`` instead of ``pip``

A basic example
---------------

To test everything is working let's run a basic example. The n-Queens problem is
a famous problem within the constraint programming community. In the MiniZinc
Examples we can find the following model for this problem:

..  literalinclude:: examples/nqueens.mzn
    :language: minizinc

The following Python code will use MiniZinc Python to:

1. Load the model from a file (``nqueens.mzn``)
2. Create an instance of the model for the Gecode solver
3. Assign the value 4 to ``n`` in the instance
4. Print the positions of the Queens store in the array ``q``

..  literalinclude:: examples/nqueens.py
    :language: python

Finding all solutions
---------------------

Sometimes we don't just require one solution for the given MiniZinc instance,
but all possible solutions. The following variation of the previous example uses
the ``all_solutions=True`` parameter to ask for all solutions to the problem
instance.

..  code-block:: python

    from minizinc import Instance, Model, Solver

    gecode = Solver.lookup("gecode")

    nqueens = Model("./nqueens.mzn")
    instance = Instance(gecode, nqueens)
    instance["n"] = 4

    # Find and print all possible solutions
    result = instance.solve(all_solutions=True)
    for i in range(len(result)):
        print(result[i, "q"])

The use of the ``all_solutions=True`` parameter is limited to satisfaction
models (``solve satisfy``). MiniZinc currently does not support looking for all
solutions for an optimisation model.

Similarly, in a optimisation model (``solve maximize`` or ``solve minimize``) we
could want access to the intermediate solutions created by the solver during the
optimisation process. (This could provide insight into the progress the solver
makes). In this case the ``intermediate_solutions=True`` parameter can be used.
The following example prints the intermediate solutions that Gecode found to the
trivial problem of find the highest uneven number between 1 and 10, but trying
smaller values first.

..  code-block:: python

    from minizinc import Instance, Model, Solver

    gecode = Solver.lookup("gecode")

    trivial = Model()
    trivial.add_string(
        """
        var 1..10: x;
        constraint (x mod 2) = 1;
        solve ::int_search([x], input_order, indomain_min) maximize x;
        """
    )
    instance = Instance(gecode, trivial)

    # Find and print all intermediate solutions
    result = instance.solve(intermediate_solutions=True)
    for i in range(len(result)):
        print(result[i, "x"])

..  note::

    Not all solver support the finding of all solutions and the printing of
    intermediate solutions. Solvers that support these functionalities will have
    ``-a`` among the standard flags supported by the solvers. MiniZinc Python
    will automatically check if this flag is available. If this is not the case,
    then an exception will be thrown when the requesting all or intermediate
    solutions.

For information about other parameters that are available when solving a model
instance, see :meth:`minizinc.Instance.solve`
