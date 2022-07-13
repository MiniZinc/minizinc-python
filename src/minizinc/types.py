#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AnonEnum:
    """Representation of anonymous enumeration values in MiniZinc"""

    enumName: str
    value: int

    def __str__(self):
        return f"to_enum({self.enumName},{self.value})"


@dataclass(frozen=True)
class ConstrEnum:
    """Representation of constructor function enumerated values in MiniZinc"""

    constructor: str
    argument: Any

    def __str__(self):
        return f"{self.constructor}({self.argument})"
