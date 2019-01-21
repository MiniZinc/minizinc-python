from minizinc import Solver as load_solver


def test_gecode():
    gecode = load_solver("gecode")
    assert gecode is not None
    assert gecode.id.endswith("gecode")
    assert gecode.executable == "fzn-gecode"


def test_chuffed():
    chuffed = load_solver("chuffed")
    assert chuffed is not None
    assert chuffed.id.endswith("chuffed")
    assert chuffed.executable == "fzn-chuffed"


def test_osicbc():
    osicbc = load_solver("osicbc")
    assert osicbc is not None
    assert osicbc.id.endswith("osicbc")
    assert osicbc.executable == ""
