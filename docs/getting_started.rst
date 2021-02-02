Getting Started
===============

This page will guide you through the process of setting up MiniZinc Python.
MiniZinc Python requires the following software to be installed on you machine:

- `MiniZinc <https://www.minizinc.org/>`_ 2.5.0 (or higher)
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

..  note::

    If you require the parsed information of ``.dzn`` files within your python
    environment, then you have to install the ``dzn`` extra with the MiniZinc
    package: ``pip install minizinc[dzn]``

A basic example
---------------

To test everything is working let's run a basic example. The n-Queens problem is
a famous problem within the constraint programming community. In the MiniZinc
Examples we can find the following model for this problem:

..  code-block:: minizinc

    int: n; % The number of queens.

    array [1..n] of var 1..n: q;

    include "alldifferent.mzn";

    constraint alldifferent(q);
    constraint alldifferent(i in 1..n)(q[i] + i);
    constraint alldifferent(i in 1..n)(q[i] - i);


The following Python code will use MiniZinc Python to:

1. Load the model from a file (``nqueens.mzn``)
2. Create an instance of the model for the Gecode solver
3. Assign the value 4 to ``n`` in the instance
4. Print the positions of the Queens store in the array ``q``

..  code-block:: python

    from minizinc import Instance, Model, Solver

    # Load n-Queens model from file
    nqueens = Model("./nqueens.mzn")
    # Find the MiniZinc solver configuration for Gecode
    gecode = Solver.lookup("gecode")
    # Create an Instance of the n-Queens model for Gecode
    instance = Instance(gecode, nqueens)
    # Assign 4 to n
    instance["n"] = 4
    result = instance.solve()
    # Output the array q
    print(result["q"])


Using different solvers
------------------------

One of MiniZinc's key features is the ability to use multiple solvers. MiniZinc
Python allows you to use all of MiniZinc's solver using a `solver configuration
<https://www.minizinc.org/doc-latest/en/fzn-spec.html#solver-configuration-files>`.
Solver configurations were introduces in MiniZinc 2.2. In MiniZinc Python there
are three ways of accessing a solver using solver configurations:

I. You can ``lookup`` a solver configuration that is known to MiniZinc. These
   are solver configurations that are placed on standard locations or in a
   folder included in the ``$MZN_SOLVER_PATH`` environmental variable. This is
   the most common way of accessing solvers.
II. You can ``load`` a solver configuration directly from a solver configuration
    file, ``.msc``. A description of the formatting of such files can be found
    in the `MiniZinc documentation
    <https://www.minizinc.org/doc-latest/en/fzn-spec.html>`_.
    The :meth:`minizinc.Solver.output_configuration` method can be used to
    generate a valid solver configuration.
III. You can create a new solver configuration, ``Solver``.

..  note::

    Solver loaded from file (2) or created in MiniZinc Python (3). Cannot share
    the combination of identifier and version with a solver known to MiniZinc
    (1). In these cases the solver configuration as known to MiniZinc will be
    used.

The following example shows an example of each method. It will lookup the
Chuffed solver, then load a solver configuration from a file located at
``./solvers/or-tools.msc``, and, finally, create a new solver configuration for
a solver named "My Solver".

..  code-block:: python

    from minizinc import Solver
    from pathlib import Path

    # Lookup Chuffed among MiniZinc solver configurations.
    # The argument can be a solver tag, its full identifier, or the last part of
    # its identifier
    chuffed = Solver.lookup("chuffed")

    # Load solver configuration from file
    or_tools = Solver.load(Path("./solvers/or-tools.msc"))

    # Create a new solver configuration
    # Arguments: name, version, identifier, executable
    my_solver = Solver(
        "My Solver",
        "0.7",
        "com.example.mysolver",
        "/usr/local/bin/fzn-my-solver",
    )

    # You can now change other options in the solver created configuration
    my_solver.mznlib = "/usr/local/share/mysolver/mznlib"
    my_solver.stdFlags = ["-a", "-t", "-s"]


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

..  seealso::

    For information about other parameters that are available when solving a
    model instance, see :meth:`minizinc.Instance.solve`
