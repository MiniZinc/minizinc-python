#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from support import InstanceTestCase

import minizinc
from minizinc.error import AssertionError, MiniZincError, SyntaxError, TypeError


class AssertionTest(InstanceTestCase):
    code = """
        array [1..10] of int: a = [i | i in 1..10];
        constraint assert(forall (i in 1..9) (a[i] > a[i + 1]), "a not decreasing");
        var 1..10: x;
        constraint a[x] = max(a);
        solve satisfy;
    """

    def test_assertion_error(self):
        with pytest.raises(AssertionError, match="a not decreasing") as error:
            self.instance.solve()
        loc = error.value.location
        assert str(loc.file).endswith(".mzn")
        assert loc.lines == (3, 3)
        if minizinc.default_driver.parsed_version >= (2, 6, 0):
            assert loc.columns == (27, 62)
        else:
            assert loc.columns == (0, 0)


class TypeErrorTest(InstanceTestCase):
    code = """
        array[1..2] of var int: i;
        constraint i = 1.5;
    """

    def test_type_error(self):
        with pytest.raises(TypeError, match="No matching operator found") as error:
            self.instance.solve()
        loc = error.value.location
        assert str(loc.file).endswith(".mzn")
        assert loc.lines == (3, 3)
        assert loc.columns == (20, 26)


class SyntaxErrorTest(InstanceTestCase):
    code = "constrain true;"

    def test_syntax_error(self):
        with pytest.raises(SyntaxError, match="unexpected bool literal") as error:
            self.instance.solve()
        loc = error.value.location
        assert str(loc.file).endswith(".mzn")
        assert loc.lines == (1, 1)
        assert loc.columns == (11, 14)


class EvaluationErrorTest(InstanceTestCase):
    def test_infinite_recursion(self):
        self.instance.add_string(
            """
test overflow(int: x) = overflow(x + 1);
int: cause_overflow = overflow(1);
"""
        )

        with pytest.raises(
            MiniZincError,
            match="stack overflow"
            if minizinc.default_driver.parsed_version >= (2, 6, 0)
            else "non-zero exit code",
        ):
            print(self.instance.solve())
