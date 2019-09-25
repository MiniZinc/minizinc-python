#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

from minizinc.instance import Instance


class APIInstance(Instance):
    pass
    # _ptr: c_void_p

    # def __init__(self, files: Optional[List[Union[Path, str]]] = None):
    #     self._ptr = self.driver._minizinc_instance_init()
    #     if self._ptr is None:
    #         msg = self.driver._minizinc_error()
    #         raise SystemError(msg.decode())
    #     super().__init__(files)

    # def solve(self, solver, *args, **kwargs):
    #     pass

    # def __del__(self):
    #     if self._ptr is not None:
    #         succes = self.driver._minizinc_instance_destroy(self._ptr)
    #         if not succes:
    #             msg = self.driver._minizinc_error()
    #             raise SystemError(msg.decode())

    # def __setitem__(self, key: str, value: Any):
    #     pass

    # def __getitem__(self, key: str) -> Any:
    #     pass

    # def add_to_model(self, code: str) -> None:
    #     pass

    # def branch(self):
    #     pass

    # @property
    # def method(self) -> Method:
    #     pass
