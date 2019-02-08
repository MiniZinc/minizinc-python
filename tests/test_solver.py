from minizinc import load_solver


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


def test_coinbc():
    coinbc = load_solver("coinbc")
    assert coinbc is not None
    assert coinbc.id.endswith("coinbc")
    assert coinbc.executable == ""