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


..  code-block:: python

    from dataclasses import InitVar, dataclass
    from typing import List

    from minizinc import Instance, Model, Solver


    @dataclass
    class TaskAssignment:
        task: List[int]
        objective: int
        __output_item: InitVar[str] = None

        def check(self) -> bool:
            return len(set(self.task)) == len(self.task)


    gecode = Solver.lookup("gecode")
    model = Model()
    model.add_string(
        """
        int: n;
        set of int: DOM = 1..n;
        int: m;
        set of int: COD = 1..m;
        array[DOM,COD] of int: profit;

        array[DOM] of var COD: task;

        include "all_different.mzn";
        constraint all_different(task);

        solve maximize sum(w in DOM)
                    (profit[w,task[w]]);
        """
    )
    model.output_type = TaskAssignment

    inst = Instance(gecode, model)
    inst["n"] = 4
    inst["m"] = 5
    inst["profit"] = [[7, 1, 3, 4, 6], [8, 2, 5, 1, 4], [4, 3, 7, 2, 5], [3, 1, 6, 3, 6]]


    sol = inst.solve().solution
    assert type(sol) == TaskAssignment

    if sol.check:
        print("A valid assignment!")
    else:
        print("A bad assignment!")


..  _meta-heuristics:

Defining Meta-Heuristics
------------------------

Modellers will sometimes require the use of meta-heuristics to more
efficiently solve their problem instances. MiniZinc Python can assist in the
formatting of Meta-Heuristics by the use of the :func:`Instance.branch`
method. This method allows you to make incremental (temporary) changes to a
:class:`Instance` object. This could, for example allow you to explore a
different part of the search space.

The following example shows a manual implementation of the branch-and-bound
algorithm used in various solvers. It first looks for any solution. Once a
solution is found, a new constraint is added to ensure that the next solution
has a higher objective value. The second step is repeated until no solutions
can be found.

..  code-block:: python

    from minizinc import Instance, Model, Result, Solver, Status

    gecode = Solver.lookup("gecode")
    m = Model()
    m.add_string(
        """
        array[1..4] of var 1..10: x;
        var int: obj;

        constraint obj = sum(x);
        output ["\\(obj)"];
        """
    )
    inst = Instance(gecode, m)

    res: Result = inst.solve()
    print(res.solution)
    while res.status == Status.SATISFIED:
        with inst.branch() as child:
            child.add_string(f"constraint obj > {res['obj']};")
            res = child.solve()
            if res.solution is not None:
                print(res.solution)

Note that all constraints added to the child instance are removed once the
with-context ends. For branch-and-bound the added constraints are
complementary and do not have to be retracted. For other search algorithms
this is not the case. The following example performs a simple Large
Neighbourhood search. After finding an initial solution, the search will
randomly fix 70% of its variables and try and find a better solution. If no
better solution is found in the last 3 iterations, it will stop.

..  code-block:: python

    import random

    from minizinc import Instance, Model, Result, Solver, Status

    gecode = Solver.lookup("gecode")
    m = Model()
    m.add_string(
        """
        array[1..10] of var 1..10: x;
        var int: obj;

        constraint obj = sum(x);
        output ["\\(obj)"]
        """
    )
    inst = Instance(gecode, m)

    res: Result = inst.solve()
    incumbent = res.solution
    i = 0
    print(incumbent)
    while i < 10:
        with inst.branch() as child:
            for i in random.sample(range(10), 7):
                child.add_string(f"constraint x[{i + 1}] == {incumbent.x[i]};\n")
            child.add_string(f"solve maximize obj;\n")
            res = child.solve()
            if res.solution is not None and res["obj"] > incumbent.obj:
                i = 0
                incumbent = res.solution
                print(incumbent)
            else:
                i += 1


Concurrent Solving
------------------

MiniZinc Python provides asynchronous methods for solving MiniZinc instances.
These methods can be used to concurrently solve an instances and/or use some of
pythons other functionality. The following code sample shows a MiniZinc instance
that is solved by two solvers at the same time. The solver that solves the
instance the fastest is proclaimed the winner!

..  code-block:: python

    import asyncio
    import minizinc

    # Lookup solvers to compete
    chuffed = minizinc.Solver.lookup("chuffed")
    gecode = minizinc.Solver.lookup("gecode")

    # Create model
    model = minizinc.Model(["nqueens.mzn"])
    model["n"] = 16


    async def solver_race(model, solvers):
        tasks = set()
        for solver in solvers:
            # Create an instance of the model for every solver
            inst = minizinc.Instance(solver, model)

            # Create a task for the solving of each instance
            task = asyncio.create_task(inst.solve_async())
            task.solver = solver.name
            tasks.add(task)

        # Wait on the first task to finish and cancel the other tasks
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for t in pending:
            t.cancel()

        # Declare the winner
        for t in done:
            print("{} finished solving the problem first!".format(t.solver))


    asyncio.run(solver_race(model, [chuffed, gecode]))


Concurrent Solutions
--------------------

MiniZinc Python provides an asynchronous generator to receive the generated
solutions. The generator allows users to process solutions as they come in. The
following example solves the n-queens problem and displays a board with the
letter Q on any position that contains a queen.

..  code-block:: python

    import asyncio
    import minizinc


    async def show_queens(n):
        # Create model
        model = minizinc.Model(["nqueens.mzn"])
        model["n"] = n
        # Lookup solver
        gecode = minizinc.Solver.lookup("gecode")
        instance = minizinc.Instance(gecode, model)

        async for result in instance.solutions(all_solutions=True):
            if result.solution is None:
                continue
            queens = result["q"]

            for row in range(len(queens)):
                # Print line
                print("".join(["--" for _ in range(len(queens))]) + "-")
                print("|", end="")
                for col in range(len(queens)):
                    if queens[row] == col:
                        print("Q|", end="")
                    else:
                        print(" |", end="")
                print("")

            print("".join(["--" for _ in range(len(queens))]) + "-")

            print("\n --------------------------------- \n")


    asyncio.run(show_queens(6))


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

Debugging the Python to MiniZinc connection
-------------------------------------------

This package has been setup to contain useful logging features to find any
potential issues in the connections from Python to MiniZinc. The logging is
implemented using Python's default `logging` package and is always enabled. To
view this log one has to set the preferred output mode and event level before
importing the MiniZinc package. The following example will view all logged
events and write them to a file:

..  code-block:: python

    import logging

    logging.basicConfig(filename="minizinc-python.log", level=logging.DEBUG)

    import minizinc

    model = minizinc.Model(["nqueens.mzn"])
    solver = minizinc.Solver.lookup("gecode")
    instance = minizinc.Instance(solver, model)
    instance["n"] = 9
    print(instance.solve())


The generated file will contain all remote calls to the MiniZinc executable:

..  code-block:: none

    DEBUG:minizinc:CLIDriver:run -> command: "/Applications/MiniZincIDE.app/Contents/Resources/minizinc --allow-multiple-assignments --version", timeout None
    DEBUG:minizinc:CLIDriver:run -> command: "/Applications/MiniZincIDE.app/Contents/Resources/minizinc --allow-multiple-assignments --version", timeout None
    DEBUG:minizinc:CLIDriver:run -> command: "/Applications/MiniZincIDE.app/Contents/Resources/minizinc --allow-multiple-assignments --solvers-json", timeout None
    DEBUG:minizinc:CLIDriver:run -> command: "/Applications/MiniZincIDE.app/Contents/Resources/minizinc --solver org.gecode.gecode@6.1.1 --allow-multiple-assignments --model-interface-only nqueens.mzn", timeout None
    DEBUG:minizinc:CLIInstance:analyse -> output fields: [('q', typing.List[int]), ('_checker', <class 'str'>)]
    DEBUG:asyncio:Using selector: KqueueSelector
    DEBUG:minizinc:CLIDriver:create_process -> program: /Applications/MiniZincIDE.app/Contents/Resources/minizinc args: "--solver org.gecode.gecode@6.1.1 --allow-multiple-assignments --output-mode json --output-time --output-objective --output-output-item -s nqueens.mzn"
    DEBUG:minizinc:CLIDriver:run -> command: "/Applications/MiniZincIDE.app/Contents/Resources/minizinc --allow-multiple-assignments --version", timeout None
    DEBUG:minizinc:CLIDriver:run -> command: "/Applications/MiniZincIDE.app/Contents/Resources/minizinc --allow-multiple-assignments --solvers-json", timeout None
    DEBUG:minizinc:CLIDriver:run -> command: "/Applications/MiniZincIDE.app/Contents/Resources/minizinc --solver org.gecode.gecode@6.1.1 --allow-multiple-assignments --model-interface-only nqueens.mzn", timeout None
    DEBUG:minizinc:CLIInstance:analyse -> output fields: [('q', typing.List[int]), ('_checker', <class 'str'>)]
    DEBUG:asyncio:Using selector: KqueueSelector
    DEBUG:minizinc:CLIDriver:create_process -> program: /Applications/MiniZincIDE.app/Contents/Resources/minizinc args: "--solver org.gecode.gecode@6.1.1 --allow-multiple-assignments --output-mode json --output-time --output-objective --output-output-item -s nqueens.mzn /var/folders/gj/cmhh026j5ddb28sw1z95pygdy5kk20/T/mzn_datau1ss0gze.json"
    DEBUG:minizinc:CLIDriver:run -> command: "/Applications/MiniZincIDE.app/Contents/Resources/minizinc --allow-multiple-assignments --version", timeout None
    DEBUG:minizinc:CLIDriver:run -> command: "/Applications/MiniZincIDE.app/Contents/Resources/minizinc --allow-multiple-assignments --solvers-json", timeout None
    DEBUG:minizinc:CLIDriver:run -> command: "/Applications/MiniZincIDE.app/Contents/Resources/minizinc --solver org.gecode.gecode@6.1.1 --allow-multiple-assignments --model-interface-only nqueens.mzn", timeout None
    DEBUG:minizinc:CLIInstance:analyse -> output fields: [('q', typing.List[int]), ('_checker', <class 'str'>)]
    DEBUG:asyncio:Using selector: KqueueSelector
    DEBUG:minizinc:CLIDriver:create_process -> program: /Applications/MiniZincIDE.app/Contents/Resources/minizinc args: "--solver org.gecode.gecode@6.1.1 --allow-multiple-assignments --output-mode json --output-time --output-objective --output-output-item -s nqueens.mzn /var/folders/gj/cmhh026j5ddb28sw1z95pygdy5kk20/T/mzn_datamnhikzwo.json"


If MiniZinc Python instances are instantiated directly from Python, then the
CLI driver will generate temporary files to use with the created MiniZinc
process. When something seems wrong with MiniZinc Python it is often a good
idea to retrieve these objects to both check if the files are generated
correctly and to recreate the exact MiniZinc command that is ran. For a
``CLIInstance`` object, you can use the ``files()`` method to generate the
files. You can then inspect or copy these files:

..  code-block:: python

    import minizinc
    from pathlib import Path

    model = minizinc.Model(["nqueens.mzn"])
    solver = minizinc.Solver.lookup("gecode")
    instance = minizinc.Instance(solver, model)
    instance["n"] = 9

    with instance.files() as files:
        store = Path("./tmp")
        store.mkdir()
        for f in files:
            f.link_to(store / f.name)


Finally, if you are looking for bugs related to the behaviour of MiniZinc,
solvers, or solver libraries, then it could be helpful to have a look at the
direct MiniZinc output on ``stderr``.  The ``CLIInstance`` class now has
experimental support for to write the output from ``stderr`` to a file and to
enable verbose compilation and solving (using the command line ``-v`` flag).
The former is enable by providing a ``pathlib.Path`` object as the
``debug_output`` parameter to any solving method. Similarly, the verbose flag
is triggered by setting the ``verbose`` parameter to ``True``. The following
fragment shows capture the verbose output of a model that contains trace
statements (which are also captured on ``stderr``):

..  code-block:: python

    import minizinc
    from pathlib import Path

    gecode = minizinc.Solver.lookup("gecode")
    instance = minizinc.Instance(gecode)
    instance.add_string("""
        constraint trace("--- TRACE: This is a trace statement\\n");
    """)

    instance.solve(verbose=True, debug_output=Path("./debug_output.txt"))
