#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

from minizinc import Instance, Solver
from minizinc.instance import Method
from minizinc.result import Status
from support import InstanceTestCase

class TestEnum(InstanceTestCase):
    code = """
    enum DAY = {Mo, Tu, We, Th, Fr, Sa, Su};
    var DAY: d;
    """

    def test_value(self):
        self.instance.add_string("constraint d == Mo;")
        result = self.instance.solve()
        assert isinstance(result["d"], str)
        assert result["d"] == "Mo"

    def test_cmp_in_instance(self):
        self.instance.add_string("var DAY: d2;")
        self.instance.add_string("constraint d < d2;")
        result = self.instance.solve()
        assert type(result["d"]) == type(result["d2"])
        # TODO: assert result["d"] < result["d2"]

    def test_cmp_between_instances(self):
        append = "constraint d == Mo;"
        self.instance.add_string(append)
        result = self.instance.solve()

        inst = Instance(self.solver)
        inst.add_string(self.code + append)
        result2 = inst.solve()
        assert type(result["d"]) == type(result2["d"])
        assert result["d"] == result2["d"]

        inst = Instance(self.solver)
        inst.add_string( """
          enum DAY = {Mo, Tu, We, Th, Fr};
          var DAY: d;
          """ + append)
        result2 = inst.solve()
        # TODO: assert type(result["d"]) != type(result2["d"])
        # TODO: assert result["d"] == result2["d"]

