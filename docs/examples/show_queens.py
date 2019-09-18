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
