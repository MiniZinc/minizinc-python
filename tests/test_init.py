import minizinc


def test_default_driver():
    assert minizinc.default_driver is not None
