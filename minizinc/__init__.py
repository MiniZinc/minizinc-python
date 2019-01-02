from .driver import load_solver, find_minizinc, default_driver

# Try and find MiniZinc and setup default driver
driver.default_driver = find_minizinc("minizinc")
