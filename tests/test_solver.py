#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

from minizinc import Solver


def test_gecode():
    gecode = Solver.lookup("gecode")
    assert gecode is not None
    assert gecode.id.endswith("gecode")
    assert gecode.executable.endswith("fzn-gecode")


def test_chuffed():
    chuffed = Solver.lookup("chuffed")
    assert chuffed is not None
    assert chuffed.id.endswith("chuffed")
    assert chuffed.executable.endswith("fzn-chuffed")


def test_coinbc():
    coinbc = Solver.lookup("coin-bc")
    assert coinbc is not None
    assert coinbc.id.endswith("coin-bc")
    assert coinbc.executable is None
