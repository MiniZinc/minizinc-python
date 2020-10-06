# type: ignore
# flake8: noqa

# DO NOT EDIT -- AUTOMATICALLY GENERATED FROM:
# https://github.com/Dekker1/iro-mzn

import re

from pygments.lexer import RegexLexer, bygroups
from pygments.token import *

__all__ = ["MiniZincLexer"]


class MiniZincLexer(RegexLexer):
    name = "MiniZinc"
    aliases = ["fzn", "dzn", "mzn", "minizinc"]
    filenames = ["*.mzn", "*.fzn", "*.dzn"]
    flags = re.MULTILINE | re.UNICODE

    tokens = {
        "root": [
            ("(/\\*)", bygroups(Comment), "multi_line_comment__1"),
            ("(%.*)", bygroups(Comment)),
            ("(@)", bygroups(Generic.Inserted), "main__1"),
            ("(\\b0o[0-7]+)", bygroups(Number)),
            ("(\\b0x[0-9A-Fa-f]+)", bygroups(Number)),
            ("(\\b0x[0-9A-Fa-f]+)", bygroups(Number)),
            ("(\\b\\d+(?:(?:.\\d+)?[Ee][-+]?\\d+|.\\d+))", bygroups(Number)),
            ("(\\b\\d+)", bygroups(Number)),
            ('(\\")', bygroups(String), "string__1"),
            ("(\\b(?:true|false)\\b)", bygroups(Literal)),
            ("(\\bnot\\b|<->|->|<-|\\\\/|\\bxor\\b|/\\\\)", bygroups(Operator)),
            ("(<|>|<=|>=|==|=|!=)", bygroups(Operator)),
            ("(\\+|-|\\*|/|\\bdiv\\b|\\bmod\\b)", bygroups(Operator)),
            (
                "(\\b(?:in|subset|superset|union|diff|symdiff|intersect|\\.\\.)\\b)",
                bygroups(Operator),
            ),
            ("(;)", bygroups(Punctuation)),
            ("(:)", bygroups(Punctuation)),
            ("(,)", bygroups(Punctuation)),
            ("(\\{)", bygroups(Punctuation), "main__2"),
            ("(\\[)", bygroups(Punctuation), "main__3"),
            ("(\\()", bygroups(Punctuation), "main__4"),
            ("(\\}|\\]|\\))", bygroups(Generic.Error)),
            ("(\\|)", bygroups(Generic.Error)),
            (
                "(\\b(?:annotation|constraint|function|include|op|output|minimize|maximize|predicate|satisfy|solve|test|type)\\b)",
                bygroups(Keyword),
            ),
            (
                "(\\b(?:ann|array|bool|enum|float|int|list|of|par|set|string|tuple|var)\\b)",
                bygroups(Keyword.Type),
            ),
            (
                "(\\b(?:for|forall|if|then|elseif|else|endif|where|let|in)\\b)",
                bygroups(Keyword),
            ),
            ("(\\b(?:any|case|op|record)\\b)", bygroups(Generic.Error)),
            (
                "(\\b(?:abort|abs|acosh|array_intersect|array_union|array1d|array2d|array3d|array4d|array5d|array6d|asin|assert|atan|bool2int|card|ceil|concat|cos|cosh|dom|dom_array|dom_size|fix|exp|floor|index_set|index_set_1of2|index_set_2of2|index_set_1of3|index_set_2of3|index_set_3of3|int2float|is_fixed|join|lb|lb_array|length|ln|log|log2|log10|min|max|pow|product|round|set2array|show|show_int|show_float|sin|sinh|sqrt|sum|tan|tanh|trace|ub|ub_array)\\b)",
                bygroups(Name.Builtin),
            ),
            (
                "(\\b(?:circuit|disjoint|maximum|maximum_arg|member|minimum|minimum_arg|network_flow|network_flow_cost|partition_set|range|roots|sliding_sum|subcircuit|sum_pred)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:alldifferent|all_different|all_disjoint|all_equal|alldifferent_except_0|nvalue|symmetric_all_different)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:lex2|lex_greater|lex_greatereq|lex_less|lex_lesseq|strict_lex2|value_precede|value_precede_chain)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:arg_sort|decreasing|increasing|sort)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:int_set_channel|inverse|inverse_set|link_set_to_booleans)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:among|at_least|at_most|at_most1|count|count_eq|count_geq|count_gt|count_leq|count_lt|count_neq|distribute|exactly|global_cardinality|global_cardinality_closed|global_cardinality_low_up|global_cardinality_low_up_closed)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:bin_packing|bin_packing_capa|bin_packing_load|diffn|diffn_k|diffn_nonstrict|diffn_nonstrict_k|geost|geost_bb|geost_smallest_bb|knapsack)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:alternative|cumulative|disjunctive|disjunctive_strict|span)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            ("(\\b(?:regular|regular_nfa|table)\\b)", bygroups(Name.Builtin.Pseudo)),
            (
                "(\\b[A-Za-z][A-Za-z0-9_]*|'[^'\\n\\r]*')(\\()",
                bygroups(Name.Function, Punctuation),
                "main__5",
            ),
            ("(\\b[A-Za-z][A-Za-z0-9_]*|'[^'\\n\\r]*')", bygroups(Name.Variable)),
            ("(\n|\r|\r\n)", String),
            (".", String),
        ],
        "main__1": [
            ("(\n|\r|\r\n)", String),
            (".", Generic.Inserted),
        ],
        "main__2": [
            ("(\\|)", bygroups(Punctuation)),
            ("(/\\*)", bygroups(Comment), "multi_line_comment__1"),
            ("(%.*)", bygroups(Comment)),
            ("(@)", bygroups(Generic.Inserted), "main__1"),
            ("(\\b0o[0-7]+)", bygroups(Number)),
            ("(\\b0x[0-9A-Fa-f]+)", bygroups(Number)),
            ("(\\b0x[0-9A-Fa-f]+)", bygroups(Number)),
            ("(\\b\\d+(?:(?:.\\d+)?[Ee][-+]?\\d+|.\\d+))", bygroups(Number)),
            ("(\\b\\d+)", bygroups(Number)),
            ('(\\")', bygroups(String), "string__1"),
            ("(\\b(?:true|false)\\b)", bygroups(Literal)),
            ("(\\bnot\\b|<->|->|<-|\\\\/|\\bxor\\b|/\\\\)", bygroups(Operator)),
            ("(<|>|<=|>=|==|=|!=)", bygroups(Operator)),
            ("(\\+|-|\\*|/|\\bdiv\\b|\\bmod\\b)", bygroups(Operator)),
            (
                "(\\b(?:in|subset|superset|union|diff|symdiff|intersect|\\.\\.)\\b)",
                bygroups(Operator),
            ),
            ("(;)", bygroups(Punctuation)),
            ("(:)", bygroups(Punctuation)),
            ("(,)", bygroups(Punctuation)),
            ("(\\{)", bygroups(Punctuation), "main__2"),
            ("(\\[)", bygroups(Punctuation), "main__3"),
            ("(\\()", bygroups(Punctuation), "main__4"),
            ("(\\}|\\]|\\))", bygroups(Generic.Error)),
            ("(\\|)", bygroups(Generic.Error)),
            (
                "(\\b(?:annotation|constraint|function|include|op|output|minimize|maximize|predicate|satisfy|solve|test|type)\\b)",
                bygroups(Keyword),
            ),
            (
                "(\\b(?:ann|array|bool|enum|float|int|list|of|par|set|string|tuple|var)\\b)",
                bygroups(Keyword.Type),
            ),
            (
                "(\\b(?:for|forall|if|then|elseif|else|endif|where|let|in)\\b)",
                bygroups(Keyword),
            ),
            ("(\\b(?:any|case|op|record)\\b)", bygroups(Generic.Error)),
            (
                "(\\b(?:abort|abs|acosh|array_intersect|array_union|array1d|array2d|array3d|array4d|array5d|array6d|asin|assert|atan|bool2int|card|ceil|concat|cos|cosh|dom|dom_array|dom_size|fix|exp|floor|index_set|index_set_1of2|index_set_2of2|index_set_1of3|index_set_2of3|index_set_3of3|int2float|is_fixed|join|lb|lb_array|length|ln|log|log2|log10|min|max|pow|product|round|set2array|show|show_int|show_float|sin|sinh|sqrt|sum|tan|tanh|trace|ub|ub_array)\\b)",
                bygroups(Name.Builtin),
            ),
            (
                "(\\b(?:circuit|disjoint|maximum|maximum_arg|member|minimum|minimum_arg|network_flow|network_flow_cost|partition_set|range|roots|sliding_sum|subcircuit|sum_pred)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:alldifferent|all_different|all_disjoint|all_equal|alldifferent_except_0|nvalue|symmetric_all_different)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:lex2|lex_greater|lex_greatereq|lex_less|lex_lesseq|strict_lex2|value_precede|value_precede_chain)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:arg_sort|decreasing|increasing|sort)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:int_set_channel|inverse|inverse_set|link_set_to_booleans)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:among|at_least|at_most|at_most1|count|count_eq|count_geq|count_gt|count_leq|count_lt|count_neq|distribute|exactly|global_cardinality|global_cardinality_closed|global_cardinality_low_up|global_cardinality_low_up_closed)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:bin_packing|bin_packing_capa|bin_packing_load|diffn|diffn_k|diffn_nonstrict|diffn_nonstrict_k|geost|geost_bb|geost_smallest_bb|knapsack)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:alternative|cumulative|disjunctive|disjunctive_strict|span)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            ("(\\b(?:regular|regular_nfa|table)\\b)", bygroups(Name.Builtin.Pseudo)),
            (
                "(\\b[A-Za-z][A-Za-z0-9_]*|'[^'\\n\\r]*')(\\()",
                bygroups(Name.Function, Punctuation),
                "main__5",
            ),
            ("(\\b[A-Za-z][A-Za-z0-9_]*|'[^'\\n\\r]*')", bygroups(Name.Variable)),
            ("(\n|\r|\r\n)", String),
            (".", String),
        ],
        "main__3": [
            ("(\\|)", bygroups(Punctuation)),
            ("(/\\*)", bygroups(Comment), "multi_line_comment__1"),
            ("(%.*)", bygroups(Comment)),
            ("(@)", bygroups(Generic.Inserted), "main__1"),
            ("(\\b0o[0-7]+)", bygroups(Number)),
            ("(\\b0x[0-9A-Fa-f]+)", bygroups(Number)),
            ("(\\b0x[0-9A-Fa-f]+)", bygroups(Number)),
            ("(\\b\\d+(?:(?:.\\d+)?[Ee][-+]?\\d+|.\\d+))", bygroups(Number)),
            ("(\\b\\d+)", bygroups(Number)),
            ('(\\")', bygroups(String), "string__1"),
            ("(\\b(?:true|false)\\b)", bygroups(Literal)),
            ("(\\bnot\\b|<->|->|<-|\\\\/|\\bxor\\b|/\\\\)", bygroups(Operator)),
            ("(<|>|<=|>=|==|=|!=)", bygroups(Operator)),
            ("(\\+|-|\\*|/|\\bdiv\\b|\\bmod\\b)", bygroups(Operator)),
            (
                "(\\b(?:in|subset|superset|union|diff|symdiff|intersect|\\.\\.)\\b)",
                bygroups(Operator),
            ),
            ("(;)", bygroups(Punctuation)),
            ("(:)", bygroups(Punctuation)),
            ("(,)", bygroups(Punctuation)),
            ("(\\{)", bygroups(Punctuation), "main__2"),
            ("(\\[)", bygroups(Punctuation), "main__3"),
            ("(\\()", bygroups(Punctuation), "main__4"),
            ("(\\}|\\]|\\))", bygroups(Generic.Error)),
            ("(\\|)", bygroups(Generic.Error)),
            (
                "(\\b(?:annotation|constraint|function|include|op|output|minimize|maximize|predicate|satisfy|solve|test|type)\\b)",
                bygroups(Keyword),
            ),
            (
                "(\\b(?:ann|array|bool|enum|float|int|list|of|par|set|string|tuple|var)\\b)",
                bygroups(Keyword.Type),
            ),
            (
                "(\\b(?:for|forall|if|then|elseif|else|endif|where|let|in)\\b)",
                bygroups(Keyword),
            ),
            ("(\\b(?:any|case|op|record)\\b)", bygroups(Generic.Error)),
            (
                "(\\b(?:abort|abs|acosh|array_intersect|array_union|array1d|array2d|array3d|array4d|array5d|array6d|asin|assert|atan|bool2int|card|ceil|concat|cos|cosh|dom|dom_array|dom_size|fix|exp|floor|index_set|index_set_1of2|index_set_2of2|index_set_1of3|index_set_2of3|index_set_3of3|int2float|is_fixed|join|lb|lb_array|length|ln|log|log2|log10|min|max|pow|product|round|set2array|show|show_int|show_float|sin|sinh|sqrt|sum|tan|tanh|trace|ub|ub_array)\\b)",
                bygroups(Name.Builtin),
            ),
            (
                "(\\b(?:circuit|disjoint|maximum|maximum_arg|member|minimum|minimum_arg|network_flow|network_flow_cost|partition_set|range|roots|sliding_sum|subcircuit|sum_pred)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:alldifferent|all_different|all_disjoint|all_equal|alldifferent_except_0|nvalue|symmetric_all_different)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:lex2|lex_greater|lex_greatereq|lex_less|lex_lesseq|strict_lex2|value_precede|value_precede_chain)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:arg_sort|decreasing|increasing|sort)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:int_set_channel|inverse|inverse_set|link_set_to_booleans)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:among|at_least|at_most|at_most1|count|count_eq|count_geq|count_gt|count_leq|count_lt|count_neq|distribute|exactly|global_cardinality|global_cardinality_closed|global_cardinality_low_up|global_cardinality_low_up_closed)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:bin_packing|bin_packing_capa|bin_packing_load|diffn|diffn_k|diffn_nonstrict|diffn_nonstrict_k|geost|geost_bb|geost_smallest_bb|knapsack)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:alternative|cumulative|disjunctive|disjunctive_strict|span)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            ("(\\b(?:regular|regular_nfa|table)\\b)", bygroups(Name.Builtin.Pseudo)),
            (
                "(\\b[A-Za-z][A-Za-z0-9_]*|'[^'\\n\\r]*')(\\()",
                bygroups(Name.Function, Punctuation),
                "main__5",
            ),
            ("(\\b[A-Za-z][A-Za-z0-9_]*|'[^'\\n\\r]*')", bygroups(Name.Variable)),
            ("(\n|\r|\r\n)", String),
            (".", String),
        ],
        "main__4": [
            ("(/\\*)", bygroups(Comment), "multi_line_comment__1"),
            ("(%.*)", bygroups(Comment)),
            ("(@)", bygroups(Generic.Inserted), "main__1"),
            ("(\\b0o[0-7]+)", bygroups(Number)),
            ("(\\b0x[0-9A-Fa-f]+)", bygroups(Number)),
            ("(\\b0x[0-9A-Fa-f]+)", bygroups(Number)),
            ("(\\b\\d+(?:(?:.\\d+)?[Ee][-+]?\\d+|.\\d+))", bygroups(Number)),
            ("(\\b\\d+)", bygroups(Number)),
            ('(\\")', bygroups(String), "string__1"),
            ("(\\b(?:true|false)\\b)", bygroups(Literal)),
            ("(\\bnot\\b|<->|->|<-|\\\\/|\\bxor\\b|/\\\\)", bygroups(Operator)),
            ("(<|>|<=|>=|==|=|!=)", bygroups(Operator)),
            ("(\\+|-|\\*|/|\\bdiv\\b|\\bmod\\b)", bygroups(Operator)),
            (
                "(\\b(?:in|subset|superset|union|diff|symdiff|intersect|\\.\\.)\\b)",
                bygroups(Operator),
            ),
            ("(;)", bygroups(Punctuation)),
            ("(:)", bygroups(Punctuation)),
            ("(,)", bygroups(Punctuation)),
            ("(\\{)", bygroups(Punctuation), "main__2"),
            ("(\\[)", bygroups(Punctuation), "main__3"),
            ("(\\()", bygroups(Punctuation), "main__4"),
            ("(\\}|\\]|\\))", bygroups(Generic.Error)),
            ("(\\|)", bygroups(Generic.Error)),
            (
                "(\\b(?:annotation|constraint|function|include|op|output|minimize|maximize|predicate|satisfy|solve|test|type)\\b)",
                bygroups(Keyword),
            ),
            (
                "(\\b(?:ann|array|bool|enum|float|int|list|of|par|set|string|tuple|var)\\b)",
                bygroups(Keyword.Type),
            ),
            (
                "(\\b(?:for|forall|if|then|elseif|else|endif|where|let|in)\\b)",
                bygroups(Keyword),
            ),
            ("(\\b(?:any|case|op|record)\\b)", bygroups(Generic.Error)),
            (
                "(\\b(?:abort|abs|acosh|array_intersect|array_union|array1d|array2d|array3d|array4d|array5d|array6d|asin|assert|atan|bool2int|card|ceil|concat|cos|cosh|dom|dom_array|dom_size|fix|exp|floor|index_set|index_set_1of2|index_set_2of2|index_set_1of3|index_set_2of3|index_set_3of3|int2float|is_fixed|join|lb|lb_array|length|ln|log|log2|log10|min|max|pow|product|round|set2array|show|show_int|show_float|sin|sinh|sqrt|sum|tan|tanh|trace|ub|ub_array)\\b)",
                bygroups(Name.Builtin),
            ),
            (
                "(\\b(?:circuit|disjoint|maximum|maximum_arg|member|minimum|minimum_arg|network_flow|network_flow_cost|partition_set|range|roots|sliding_sum|subcircuit|sum_pred)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:alldifferent|all_different|all_disjoint|all_equal|alldifferent_except_0|nvalue|symmetric_all_different)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:lex2|lex_greater|lex_greatereq|lex_less|lex_lesseq|strict_lex2|value_precede|value_precede_chain)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:arg_sort|decreasing|increasing|sort)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:int_set_channel|inverse|inverse_set|link_set_to_booleans)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:among|at_least|at_most|at_most1|count|count_eq|count_geq|count_gt|count_leq|count_lt|count_neq|distribute|exactly|global_cardinality|global_cardinality_closed|global_cardinality_low_up|global_cardinality_low_up_closed)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:bin_packing|bin_packing_capa|bin_packing_load|diffn|diffn_k|diffn_nonstrict|diffn_nonstrict_k|geost|geost_bb|geost_smallest_bb|knapsack)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:alternative|cumulative|disjunctive|disjunctive_strict|span)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            ("(\\b(?:regular|regular_nfa|table)\\b)", bygroups(Name.Builtin.Pseudo)),
            (
                "(\\b[A-Za-z][A-Za-z0-9_]*|'[^'\\n\\r]*')(\\()",
                bygroups(Name.Function, Punctuation),
                "main__5",
            ),
            ("(\\b[A-Za-z][A-Za-z0-9_]*|'[^'\\n\\r]*')", bygroups(Name.Variable)),
            ("(\n|\r|\r\n)", String),
            (".", String),
        ],
        "main__5": [
            ("(/\\*)", bygroups(Comment), "multi_line_comment__1"),
            ("(%.*)", bygroups(Comment)),
            ("(@)", bygroups(Generic.Inserted), "main__1"),
            ("(\\b0o[0-7]+)", bygroups(Number)),
            ("(\\b0x[0-9A-Fa-f]+)", bygroups(Number)),
            ("(\\b0x[0-9A-Fa-f]+)", bygroups(Number)),
            ("(\\b\\d+(?:(?:.\\d+)?[Ee][-+]?\\d+|.\\d+))", bygroups(Number)),
            ("(\\b\\d+)", bygroups(Number)),
            ('(\\")', bygroups(String), "string__1"),
            ("(\\b(?:true|false)\\b)", bygroups(Literal)),
            ("(\\bnot\\b|<->|->|<-|\\\\/|\\bxor\\b|/\\\\)", bygroups(Operator)),
            ("(<|>|<=|>=|==|=|!=)", bygroups(Operator)),
            ("(\\+|-|\\*|/|\\bdiv\\b|\\bmod\\b)", bygroups(Operator)),
            (
                "(\\b(?:in|subset|superset|union|diff|symdiff|intersect|\\.\\.)\\b)",
                bygroups(Operator),
            ),
            ("(;)", bygroups(Punctuation)),
            ("(:)", bygroups(Punctuation)),
            ("(,)", bygroups(Punctuation)),
            ("(\\{)", bygroups(Punctuation), "main__2"),
            ("(\\[)", bygroups(Punctuation), "main__3"),
            ("(\\()", bygroups(Punctuation), "main__4"),
            ("(\\}|\\]|\\))", bygroups(Generic.Error)),
            ("(\\|)", bygroups(Generic.Error)),
            (
                "(\\b(?:annotation|constraint|function|include|op|output|minimize|maximize|predicate|satisfy|solve|test|type)\\b)",
                bygroups(Keyword),
            ),
            (
                "(\\b(?:ann|array|bool|enum|float|int|list|of|par|set|string|tuple|var)\\b)",
                bygroups(Keyword.Type),
            ),
            (
                "(\\b(?:for|forall|if|then|elseif|else|endif|where|let|in)\\b)",
                bygroups(Keyword),
            ),
            ("(\\b(?:any|case|op|record)\\b)", bygroups(Generic.Error)),
            (
                "(\\b(?:abort|abs|acosh|array_intersect|array_union|array1d|array2d|array3d|array4d|array5d|array6d|asin|assert|atan|bool2int|card|ceil|concat|cos|cosh|dom|dom_array|dom_size|fix|exp|floor|index_set|index_set_1of2|index_set_2of2|index_set_1of3|index_set_2of3|index_set_3of3|int2float|is_fixed|join|lb|lb_array|length|ln|log|log2|log10|min|max|pow|product|round|set2array|show|show_int|show_float|sin|sinh|sqrt|sum|tan|tanh|trace|ub|ub_array)\\b)",
                bygroups(Name.Builtin),
            ),
            (
                "(\\b(?:circuit|disjoint|maximum|maximum_arg|member|minimum|minimum_arg|network_flow|network_flow_cost|partition_set|range|roots|sliding_sum|subcircuit|sum_pred)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:alldifferent|all_different|all_disjoint|all_equal|alldifferent_except_0|nvalue|symmetric_all_different)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:lex2|lex_greater|lex_greatereq|lex_less|lex_lesseq|strict_lex2|value_precede|value_precede_chain)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:arg_sort|decreasing|increasing|sort)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:int_set_channel|inverse|inverse_set|link_set_to_booleans)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:among|at_least|at_most|at_most1|count|count_eq|count_geq|count_gt|count_leq|count_lt|count_neq|distribute|exactly|global_cardinality|global_cardinality_closed|global_cardinality_low_up|global_cardinality_low_up_closed)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:bin_packing|bin_packing_capa|bin_packing_load|diffn|diffn_k|diffn_nonstrict|diffn_nonstrict_k|geost|geost_bb|geost_smallest_bb|knapsack)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:alternative|cumulative|disjunctive|disjunctive_strict|span)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            ("(\\b(?:regular|regular_nfa|table)\\b)", bygroups(Name.Builtin.Pseudo)),
            (
                "(\\b[A-Za-z][A-Za-z0-9_]*|'[^'\\n\\r]*')(\\()",
                bygroups(Name.Function, Punctuation),
                "main__5",
            ),
            ("(\\b[A-Za-z][A-Za-z0-9_]*|'[^'\\n\\r]*')", bygroups(Name.Variable)),
            ("(\n|\r|\r\n)", String),
            (".", String),
        ],
        "multi_line_comment__1": [
            ("(\n|\r|\r\n)", String),
            (".", Comment),
        ],
        "string__1": [
            ("(\\\\\\()", bygroups(Punctuation), "string__2"),
            ("(\\\\[\"'\\\\nrvt])", bygroups(String.Escape)),
            ('([^\\"\\\\\\n\\r]+)', bygroups(String)),
            ("(\n|\r|\r\n)", String),
            (".", String),
        ],
        "string__2": [
            ("(/\\*)", bygroups(Comment), "multi_line_comment__1"),
            ("(%.*)", bygroups(Comment)),
            ("(@)", bygroups(Generic.Inserted), "main__1"),
            ("(\\b0o[0-7]+)", bygroups(Number)),
            ("(\\b0x[0-9A-Fa-f]+)", bygroups(Number)),
            ("(\\b0x[0-9A-Fa-f]+)", bygroups(Number)),
            ("(\\b\\d+(?:(?:.\\d+)?[Ee][-+]?\\d+|.\\d+))", bygroups(Number)),
            ("(\\b\\d+)", bygroups(Number)),
            ('(\\")', bygroups(String), "string__1"),
            ("(\\b(?:true|false)\\b)", bygroups(Literal)),
            ("(\\bnot\\b|<->|->|<-|\\\\/|\\bxor\\b|/\\\\)", bygroups(Operator)),
            ("(<|>|<=|>=|==|=|!=)", bygroups(Operator)),
            ("(\\+|-|\\*|/|\\bdiv\\b|\\bmod\\b)", bygroups(Operator)),
            (
                "(\\b(?:in|subset|superset|union|diff|symdiff|intersect|\\.\\.)\\b)",
                bygroups(Operator),
            ),
            ("(;)", bygroups(Punctuation)),
            ("(:)", bygroups(Punctuation)),
            ("(,)", bygroups(Punctuation)),
            ("(\\{)", bygroups(Punctuation), "main__2"),
            ("(\\[)", bygroups(Punctuation), "main__3"),
            ("(\\()", bygroups(Punctuation), "main__4"),
            ("(\\}|\\]|\\))", bygroups(Generic.Error)),
            ("(\\|)", bygroups(Generic.Error)),
            (
                "(\\b(?:annotation|constraint|function|include|op|output|minimize|maximize|predicate|satisfy|solve|test|type)\\b)",
                bygroups(Keyword),
            ),
            (
                "(\\b(?:ann|array|bool|enum|float|int|list|of|par|set|string|tuple|var)\\b)",
                bygroups(Keyword.Type),
            ),
            (
                "(\\b(?:for|forall|if|then|elseif|else|endif|where|let|in)\\b)",
                bygroups(Keyword),
            ),
            ("(\\b(?:any|case|op|record)\\b)", bygroups(Generic.Error)),
            (
                "(\\b(?:abort|abs|acosh|array_intersect|array_union|array1d|array2d|array3d|array4d|array5d|array6d|asin|assert|atan|bool2int|card|ceil|concat|cos|cosh|dom|dom_array|dom_size|fix|exp|floor|index_set|index_set_1of2|index_set_2of2|index_set_1of3|index_set_2of3|index_set_3of3|int2float|is_fixed|join|lb|lb_array|length|ln|log|log2|log10|min|max|pow|product|round|set2array|show|show_int|show_float|sin|sinh|sqrt|sum|tan|tanh|trace|ub|ub_array)\\b)",
                bygroups(Name.Builtin),
            ),
            (
                "(\\b(?:circuit|disjoint|maximum|maximum_arg|member|minimum|minimum_arg|network_flow|network_flow_cost|partition_set|range|roots|sliding_sum|subcircuit|sum_pred)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:alldifferent|all_different|all_disjoint|all_equal|alldifferent_except_0|nvalue|symmetric_all_different)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:lex2|lex_greater|lex_greatereq|lex_less|lex_lesseq|strict_lex2|value_precede|value_precede_chain)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:arg_sort|decreasing|increasing|sort)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:int_set_channel|inverse|inverse_set|link_set_to_booleans)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:among|at_least|at_most|at_most1|count|count_eq|count_geq|count_gt|count_leq|count_lt|count_neq|distribute|exactly|global_cardinality|global_cardinality_closed|global_cardinality_low_up|global_cardinality_low_up_closed)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:bin_packing|bin_packing_capa|bin_packing_load|diffn|diffn_k|diffn_nonstrict|diffn_nonstrict_k|geost|geost_bb|geost_smallest_bb|knapsack)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            (
                "(\\b(?:alternative|cumulative|disjunctive|disjunctive_strict|span)\\b)",
                bygroups(Name.Builtin.Pseudo),
            ),
            ("(\\b(?:regular|regular_nfa|table)\\b)", bygroups(Name.Builtin.Pseudo)),
            (
                "(\\b[A-Za-z][A-Za-z0-9_]*|'[^'\\n\\r]*')(\\()",
                bygroups(Name.Function, Punctuation),
                "main__5",
            ),
            ("(\\b[A-Za-z][A-Za-z0-9_]*|'[^'\\n\\r]*')", bygroups(Name.Variable)),
            ("(\n|\r|\r\n)", String),
            (".", String),
        ],
    }
