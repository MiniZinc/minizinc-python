from .driver import load_solver, find_minizinc, default_driver
from .model import Model, Instance

# Try and find MiniZinc and setup default driver
driver.default_driver = find_minizinc("minizinc")
if driver.default_driver is None:
    import warnings
    warnings.warn("MiniZinc was not found on the system: no default driver could be initialised", RuntimeWarning)
