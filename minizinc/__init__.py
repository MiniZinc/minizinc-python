from .driver import load_solver, find_minizinc, default_driver
from .model import Model, ModelInstance

# Try and find MiniZinc and setup default driver
driver.default_driver = find_minizinc("minizinc")
