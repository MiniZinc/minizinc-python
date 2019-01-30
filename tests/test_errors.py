import pytest
from minizinc.error import MiniZincAssertionError, MiniZincTypeError, Location
from test_case import InstanceTestCase


class AssertionTest(InstanceTestCase):
    code = """
        array [1..10] of int: a = [i | i in 1..10];
        constraint assert(forall (i in 1..9) (a[i] > a[i + 1]), "a not decreasing");
        var 1..10: x;
        constraint a[x] = max(a);
        solve satisfy;
    """

    def test_assert(self):
        with pytest.raises(MiniZincAssertionError, match="a not decreasing") as error:
            self.solver.solve(self.instance)
        loc = error.value.location
        assert str(loc.file).endswith(".mzn")
        assert loc.line == 3
        assert loc.columns == Location.unknown().columns


class TypeErrorTest(InstanceTestCase):
    code = """
        array[1..2] of var int: i;
        constraint i = 1.5;
    """

    def test_assert(self):
        with pytest.raises(MiniZincTypeError, match="No matching operator found") as error:
            self.solver.solve(self.instance)
        loc = error.value.location
        assert str(loc.file).endswith(".mzn")
        assert loc.line == 3
        assert loc.columns == range(20, 26)
