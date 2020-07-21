#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pathlib import Path
from typing import Union

from lark import Lark, Transformer

from minizinc.model import UnknownExpression

dzn_grammar = r"""
    items: [item (";" item)* ";"?]
    item: ident "=" value | ident "=" unknown
    ident: /([A-Za-z][A-Za-z0-9_]*)|(\'[^\']*\')/
    value: array
         | array2d
         | set
         | int
         | float
         | string
         | "true"       -> true
         | "false"      -> false
    list: [value ("," value)* ","?]
    array: "[" list "]"
    array2d: "[" "|" [ list ("|" list)*] "|" "]"
    set: "{" list "}"
       | int ".." int

    int: /-?((0o[0-7]+)|(0x[0-9A-Fa-f]+)|(\d+))/
    float: /-?((\d+\.\d+[Ee][-+]?\d+)|(\d+[Ee][-+]?\d+)|(\d+\.\d+))/
    string: ESCAPED_STRING

    unknown: /[^[{;]+[^;]*/

    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS
    COMMENT: "%" /[^\n]/*
    %ignore COMMENT
"""


def arg1_construct(cls):
    return lambda self, s: cls(s[0])


class TreeToDZN(Transformer):
    @staticmethod
    def int(s):
        i = s[0]
        if i.startswith("0o") or i.startswith("-0o"):
            return int(i, 8)
        elif i.startswith("0x") or i.startswith("-0x"):
            return int(i, 16)
        else:
            return int(i)

    @staticmethod
    def item(s):
        return s[0], s[1]

    @staticmethod
    def array2d(s):
        return [li for li in s]

    @staticmethod
    def set(s):
        if len(s) == 1:
            return set(s[0])
        else:
            return range(s[0], s[1] + 1)

    @staticmethod
    def string(s):
        return str(s[0][1:-1])

    @staticmethod
    def true(_):
        return True

    @staticmethod
    def false(_):
        return False

    items = dict
    unknown = arg1_construct(UnknownExpression)
    list = list
    array = arg1_construct(lambda i: i)
    ident = arg1_construct(str)
    float = arg1_construct(float)
    value = arg1_construct(lambda i: i)


dzn_parser = Lark(dzn_grammar, start="items", parser="lalr")


def parse_dzn(dzn: Union[Path, str]):
    if isinstance(dzn, Path):
        dzn = dzn.read_text()
    tree = dzn_parser.parse(dzn)
    dzn_dict = TreeToDZN().transform(tree)
    return dzn_dict
