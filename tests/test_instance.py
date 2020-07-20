#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from support import InstanceTestCase

from minizinc.result import Status


class TestAssign(InstanceTestCase):
    code = """
        include "globals.mzn";
        int: n;
        array[1..4] of var 1..5: x;
        constraint increasing(x);
        constraint alldifferent(x);
        constraint sum(x) = n;
    """

    def test_assign(self):
        self.instance["n"] = 14
        result = self.instance.solve(all_solutions=True)
        assert result.status == Status.ALL_SOLUTIONS
        assert len(result.solution) == 1
        assert result[0, "x"] == [i for i in range(2, 5 + 1)]

    def test_reassign(self):
        self.instance["n"] = 14
        with pytest.raises(AssertionError, match="cannot be assigned multiple values."):
            self.instance["n"] = 15


class TestPythonConflict(InstanceTestCase):
    code = """
        include "globals.mzn";
        var 1..2: return;
        constraint return > 1;
    """

    def test_rename(self):
        with pytest.warns(SyntaxWarning):
            result = self.instance.solve()
            assert result.solution.mzn_return == 2


class TestBranch(InstanceTestCase):
    code = """
        include "globals.mzn";
        var 14..15: n;
        array[1..4] of var 1..5: x;
        constraint increasing(x);
        constraint sum(x) = n;
    """

    def test_add_data(self):
        result = self.instance.solve(all_solutions=True)
        assert result.status == Status.ALL_SOLUTIONS
        assert len(result.solution) == 12
        with self.instance.branch() as child:
            child["n"] = 15
            result = child.solve(all_solutions=True)
            assert result.status == Status.ALL_SOLUTIONS
            assert len(result.solution) == 5
        with self.instance.branch() as child:
            child["n"] = 14
            result = child.solve(all_solutions=True)
            assert result.status == Status.ALL_SOLUTIONS
            assert len(result.solution) == 7

    def test_extra_constraint(self):
        self.instance["n"] = 14
        result = self.instance.solve(all_solutions=True)
        assert result.status == Status.ALL_SOLUTIONS
        assert len(result.solution) == 7
        with self.instance.branch() as child:
            child.add_string("constraint all_different(x);")
            result = child.solve(all_solutions=True)
            assert result.status == Status.ALL_SOLUTIONS
            assert len(result.solution) == 1

    def test_replace_data(self):
        self.instance["n"] = 14
        result = self.instance.solve(all_solutions=True)
        assert result.status == Status.ALL_SOLUTIONS
        assert len(result.solution) == 7
        with self.instance.branch() as child:
            child["n"] = 15
            result = child.solve(all_solutions=True)
            assert result.status == Status.UNSATISFIABLE
            assert len(result.solution) == 0
