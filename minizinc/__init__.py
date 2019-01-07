from .driver import Driver, load_solver, find_minizinc
from .model import Model, Instance
from .solver import Solver

# Try and find MiniZinc and setup default driver
driver.default_driver = find_minizinc("minizinc")
if driver.default_driver is None:
    import warnings
    warnings.warn("MiniZinc was not found on the system: no default driver could be initialised", RuntimeWarning)
