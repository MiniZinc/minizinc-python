#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
import enum

import pytest
from support import InstanceTestCase

from minizinc import Instance
from minizinc.result import Status


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
        assert isinstance(result["d"], str)
        assert isinstance(result["d2"], str)
        # TODO: assert result["d"] < result["d2"]

    def test_cmp_between_instances(self):
        append = "constraint d == Mo;"
        self.instance.add_string(append)
        result = self.instance.solve()

        inst = Instance(self.solver)
        inst.add_string(self.code + append)
        result2 = inst.solve()
        assert isinstance(result["d"], str)
        assert isinstance(result2["d"], str)
        assert result["d"] == result2["d"]

        inst = Instance(self.solver)
        inst.add_string(
            """
            enum DAY = {Mo, Tu, We, Th, Fr};
            var DAY: d;
            """
            + append
        )
        result2 = inst.solve()
        assert result["d"] == result2["d"]

    def test_assign(self):
        self.instance = Instance(self.solver)
        self.instance.add_string(
            """
            enum TT;
            var TT: t1;
            """
        )
        TT = enum.Enum("TT", ["one"])
        self.instance["TT"] = TT
        result = self.instance.solve()

        assert isinstance(result["t1"], TT)
        assert result["t1"] is TT.one

    def test_collections(self):
        self.instance = Instance(self.solver)
        self.instance.add_string(
            """
            enum TT;
            array[int] of var TT: arr_t;
            var set of TT: set_t;
            """
        )
        TT = enum.Enum("TT", ["one", "two", "three"])
        self.instance["TT"] = TT
        self.instance["arr_t"] = [TT(3), TT(2), TT(1)]
        self.instance["set_t"] = {TT(2), TT(1)}
        result = self.instance.solve()

        assert result["arr_t"] == [TT(3), TT(2), TT(1)]
        assert result["set_t"] == {TT(1), TT(2)}

    def test_intenum_collections(self):
        self.instance = Instance(self.solver)
        self.instance.add_string(
            """
            enum TT;
            % array[int] of var TT: arr_t;
            var set of TT: set_t;
            """
        )
        TT = enum.IntEnum("TT", ["one", "two", "three"])
        self.instance["TT"] = TT
        # TODO:  self.instance["arr_t"] = [TT(3), TT(2), TT(1)]
        self.instance["set_t"] = {TT(2), TT(1)}
        result = self.instance.solve()

        # TODO: assert result["arr_t"] == [TT(3), TT(2), TT(1)]
        assert result["set_t"] == {TT(1), TT(2)}


class TestSets(InstanceTestCase):
    def test_ranges(self):
        self.instance.add_string(
            """
            var set of 0..10: s;
            set of int: s1;
            constraint s1 = s;
            """
        )

        self.instance["s1"] = range(1, 4)
        result = self.instance.solve()
        assert isinstance(result["s"], range)
        assert result["s"] == range(1, 4)


class TestString(InstanceTestCase):
    code = """
    array[int] of string: names;
    var index_set(names): x;
    string: name ::output_only ::add_to_output = names[fix(x)];
    """

    def test_string(self):
        names = ["Guido", "Peter"]
        self.instance["names"] = names

        result = self.instance.solve()
        assert result.solution.name in names


class TestNumPy(InstanceTestCase):
    def test_nparray_bool(self):
        numpy = pytest.importorskip("numpy")
        self.instance.add_string("array[int] of bool: x;")
        self.instance["x"] = numpy.array([True, False], dtype=numpy.bool_)
        result = self.instance.solve()
        assert result.status is Status.SATISFIED

    def test_nparray_f32(self):
        numpy = pytest.importorskip("numpy")
        self.instance.add_string("array[int] of float: x;")
        self.instance["x"] = numpy.array([1, 2, 3], dtype=numpy.float32)
        result = self.instance.solve()
        assert result.status is Status.SATISFIED

    def test_nparray_f64(self):
        numpy = pytest.importorskip("numpy")
        self.instance.add_string("array[int] of float: x;")
        self.instance["x"] = numpy.array([1, 2, 3], dtype=numpy.float64)
        result = self.instance.solve()
        assert result.status is Status.SATISFIED

    def test_nparray_int32(self):
        numpy = pytest.importorskip("numpy")
        self.instance.add_string("array[int] of int: x;")
        self.instance["x"] = numpy.array([1, 2, 3], dtype=numpy.int32)
        result = self.instance.solve()
        assert result.status is Status.SATISFIED

    def test_nparray_int64(self):
        numpy = pytest.importorskip("numpy")
        self.instance.add_string("array[int] of int: x;")
        self.instance["x"] = numpy.array([1, 2, 3], dtype=numpy.int64)
        result = self.instance.solve()
        assert result.status is Status.SATISFIED

    def test_nparray_uint32(self):
        numpy = pytest.importorskip("numpy")
        self.instance.add_string("array[int] of int: x;")
        self.instance["x"] = numpy.array([1, 2, 3], dtype=numpy.uint32)
        result = self.instance.solve()
        assert result.status is Status.SATISFIED

    def test_nparray_uint64(self):
        numpy = pytest.importorskip("numpy")
        self.instance.add_string("array[int] of int: x;")
        self.instance["x"] = numpy.array([1, 2, 3], dtype=numpy.uint64)
        result = self.instance.solve()
        assert result.status is Status.SATISFIED

    def test_npbool(self):
        numpy = pytest.importorskip("numpy")
        self.instance.add_string("bool: x;")
        self.instance["x"] = numpy.bool_(0)
        result = self.instance.solve()
        assert result.status is Status.SATISFIED

    def test_npf32(self):
        numpy = pytest.importorskip("numpy")
        self.instance.add_string("float: x;")
        self.instance["x"] = numpy.float32(0)
        result = self.instance.solve()
        assert result.status is Status.SATISFIED

    def test_npf64(self):
        numpy = pytest.importorskip("numpy")
        self.instance.add_string("float: x;")
        self.instance["x"] = numpy.float64(0)
        result = self.instance.solve()
        assert result.status is Status.SATISFIED

    def test_npint32(self):
        numpy = pytest.importorskip("numpy")
        self.instance.add_string("int: x;")
        self.instance["x"] = numpy.int32(0)
        result = self.instance.solve()
        assert result.status is Status.SATISFIED

    def test_npint64(self):
        numpy = pytest.importorskip("numpy")
        self.instance.add_string("int: x;")
        self.instance["x"] = numpy.int64(0)
        result = self.instance.solve()
        assert result.status is Status.SATISFIED


# Enable on MiniZinc 2.6+ (JSON output of annotations is broken before then)
# class TestAnn(InstanceTestCase):
#     def test_ann_atom(self):
#         self.instance.add_string("ann: x :: add_to_output = promise_total;")
#         result = self.instance.solve()
#         assert result.status is Status.SATISFIED
#         assert result["x"] == "promise_total"

#     def test_ann_call(self):
#         self.instance.add_string(
#         'ann: x :: add_to_output = expression_name("test");')
#         result = self.instance.solve()
#         assert result.status is Status.SATISFIED
#         assert result["x"] == 'expression_name("test")'
