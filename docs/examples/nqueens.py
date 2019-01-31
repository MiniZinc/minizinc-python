from minizinc import *

# Load n-Queens model from file
nqueens = Instance(['./nqueens.mzn'])
# Assign 4 to n
nqueens.n = 4
# Solve using the Gecode solver
gecode = load_solver("gecode")
result = gecode.solve(nqueens)
# Output the array q
print(result["q"])
