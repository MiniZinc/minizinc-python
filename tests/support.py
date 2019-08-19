#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest

from minizinc import Instance, Solver


class InstanceTestCase(unittest.TestCase):
    code = ""
    instance: Instance
    solver: Solver

    def setUp(self):
        self.solver = Solver.lookup("gecode")
        self.instance = Instance(self.solver)
        self.instance.add_string(self.code)
