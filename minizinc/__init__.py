from minizinc.driver import load_minizinc
from minizinc.model import Model

Instance = None
Solver = None

# Try and find MiniZinc and setup default driver
default_driver = load_minizinc()
if default_driver is None:
    import warnings
    warnings.warn("MiniZinc was not found on the system: no default driver could be initialised", RuntimeWarning)
