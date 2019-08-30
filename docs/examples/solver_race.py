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
