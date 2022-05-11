#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
import minizinc


def test_default_driver():
    assert minizinc.default_driver is not None
    assert minizinc.default_driver.executable.exists()


def test_version():
    # Test normal behaviour
    assert "MiniZinc" in minizinc.default_driver.minizinc_version
