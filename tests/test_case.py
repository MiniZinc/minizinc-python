import unittest

from minizinc import Instance, Solver, load_solver


class InstanceTestCase(unittest.TestCase):
    code = ""
    instance: Instance
    solver: Solver

    def setUp(self):
        self.solver = load_solver("gecode")
        self.instance = Instance()
        self.instance.add_to_model(self.code)
