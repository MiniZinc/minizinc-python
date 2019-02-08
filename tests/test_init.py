#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import minizinc


def test_default_driver():
    assert minizinc.default_driver is not None


def test_version():
    # Test normal behaviour
    assert minizinc.default_driver.check_version()
    assert "MiniZinc" in minizinc.default_driver.version

    # Test failure
    minizinc.driver.required_version = (3, 2, 1)
    assert not minizinc.default_driver.check_version()
