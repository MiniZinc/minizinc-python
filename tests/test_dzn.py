#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from minizinc.model import UnknownExpression

lark = pytest.importorskip("lark")
from minizinc.dzn import parse_dzn  # noqa: E402


def test_dzn_empty():
    assert parse_dzn("") == {}


def test_dzn_int():
    assert parse_dzn("x = 0") == {"x": 0}
    assert parse_dzn("x = -10") == {"x": -10}
    assert parse_dzn("x = 2123") == {"x": 2123}
    assert parse_dzn("x = 0xFF") == {"x": 255}
    assert parse_dzn("x = -0x100") == {"x": -256}
    assert parse_dzn("x = 0x0") == {"x": 0}
    assert parse_dzn("x = 0o23") == {"x": 19}
    assert parse_dzn("x = -0o30") == {"x": -24}
    assert parse_dzn("x = 0o0") == {"x": 0}


def test_dzn_float():
    assert parse_dzn("x = 0.0") == {"x": 0.0}
    assert parse_dzn("x = 0.125") == {"x": 0.125}
    assert parse_dzn("x = -0.99") == {"x": -0.99}
    assert parse_dzn("x = 3.8e10") == {"x": 3.8e10}
    assert parse_dzn("x = -1.4e7") == {"x": -1.4e7}
    assert parse_dzn("x = 2.45E-3") == {"x": 2.45e-3}
    assert parse_dzn("x = -1.33e-2") == {"x": -1.33e-2}
    assert parse_dzn("x = 4e12") == {"x": 4e12}
    assert parse_dzn("x = -3E10") == {"x": -3e10}
    assert parse_dzn("x = 2e-110") == {"x": 2e-110}
    assert parse_dzn("x = -9e-124") == {"x": -9e-124}


def test_dzn_string():
    assert parse_dzn('x = ""') == {"x": ""}
    assert parse_dzn('x = "test string"') == {"x": "test string"}
    assert parse_dzn('x = "ކ"') == {"x": "ކ"}
    assert parse_dzn('x = "🐛"') == {"x": "🐛"}


def test_dzn_set():
    # Set literals
    assert parse_dzn("x = {}") == {"x": set()}
    assert parse_dzn("x = {1}") == {"x": {1}}
    assert parse_dzn("x = {1,2,3}") == {"x": {1, 2, 3}}
    assert parse_dzn("x = {1,1,2}") == {"x": {1, 1, 2}}
    assert parse_dzn("x = {1.2,2.1}") == {"x": {1.2, 2.1}}

    # Set Ranges
    # note: upper range limit is exclusive in Python
    assert parse_dzn("x = 1..1") == {"x": range(1, 2)}
    assert set(parse_dzn("x = 1..1")["x"]) == {1}
    assert parse_dzn("x = 1..3") == {"x": range(1, 4)}
    assert set(parse_dzn("x = 1..3")["x"]) == {1, 2, 3}


def test_dzn_array():
    assert parse_dzn("x = []") == {"x": []}
    assert parse_dzn("x = [1]") == {"x": [1]}
    assert parse_dzn("x = [1,2,3,4]") == {"x": [1, 2, 3, 4]}
    assert parse_dzn("x = [2.1]") == {"x": [2.1]}
    assert parse_dzn("x = [2.1,3.2,4.2]") == {"x": [2.1, 3.2, 4.2]}
    assert parse_dzn('x = ["str1", "str2"]') == {"x": ["str1", "str2"]}
    assert parse_dzn("x = [{1,2,3}, {1,2}]") == {"x": [{1, 2, 3}, {1, 2}]}


def test_dzn_array2d():
    assert parse_dzn("x = [||]") == {"x": []}
    assert parse_dzn("x = [|1|2|3|]") == {"x": [[1], [2], [3]]}
    assert parse_dzn("x = [|1,4|2,5|3,6|]") == {"x": [[1, 4], [2, 5], [3, 6]]}
    assert parse_dzn("x = [|1.1,4.4|2.2,5.5|3.3,6.6|]") == {
        "x": [[1.1, 4.4], [2.2, 5.5], [3.3, 6.6]]
    }


def test_dzn_unknown():
    assert parse_dzn("x = array2d(index1,1..2,[4, 3, 4, 5, 3, 6]);") == {
        "x": UnknownExpression("array2d(index1,1..2,[4, 3, 4, 5, 3, 6])")
    }


def test_dzn_semicolon():
    assert parse_dzn("x = 1;") == {"x": 1}
    assert parse_dzn("x = 1") == {"x": 1}
    assert parse_dzn("x = 1; y = 2") == {"x": 1, "y": 2}
    assert parse_dzn("x = 1; y = 2;") == {"x": 1, "y": 2}
    assert parse_dzn('x = -20; y = 2e3; z = "string"') == {
        "x": -20,
        "y": 2e3,
        "z": "string",
    }


def test_dzn_trailing_comma():
    assert parse_dzn("x = [1,2,3,]") == {"x": [1, 2, 3]}
    assert parse_dzn("x = {1,2,3,}") == {"x": {1, 2, 3}}
    assert parse_dzn("x = [{1,},{2,},]") == {"x": [{1}, {2}]}
    assert parse_dzn("x = [|1,|2,|3,|]") == {"x": [[1], [2], [3]]}
