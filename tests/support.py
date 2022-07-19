#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest
from typing import ClassVar

from minizinc import Instance, Solver


class InstanceTestCase(unittest.TestCase):
    code = ""
    instance: Instance
    solver: ClassVar[Solver]

    @classmethod
    def setUpClass(cls):
        cls.solver = Solver.lookup("gecode")

    def setUp(self):
        self.instance = Instance(self.solver)
        self.instance.add_string(self.code)
