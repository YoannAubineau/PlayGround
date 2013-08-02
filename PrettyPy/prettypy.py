#!/usr/bin/env python

# Bugs:
#   - (a + b) * c --> a + b * c

# Todo:
#   - Rework lines management
#   - Rework spaces management
#   - Rework comments management

from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import ast
import StringIO
import tokenize

import pyma


chunks = []


def format_str(node, indent, ext=None):
    chunks.append(node)


def format_alias(node, indent, ext=None):
    dispatch(node.name, indent)
    if node.asname is not None:
        chunks.append(' as ')
        dispatch(node.asname, indent)


def format_NoneType(node, indent, ext=None):
    chunks.append(' None ')


def format_int(node, indent, ext=None):
    chunks.append(str(node))


def format_ImportFrom(node, indent, ext=None):
    chunks.append('    ' * indent)
    chunks.append('from ')
    dispatch(node.module, indent)
    chunks.append(' import ')
    for subnode in node.names:
        dispatch(subnode, indent)
        chunks.append(', ')
    if node.names:
        chunks.pop()
    #node.level


def format_Import(node, indent, ext=None):
    chunks.append('    ' * indent)
    chunks.append('import ')
    for subnodes in node.names:
        dispatch(subnodes, indent)
        chunks.append(', ')
    if node.names:
        chunks.pop()


def format_FunctionDef(node, indent, ext=None):
    for subnode in node.decorator_list:
        chunks.append('    ' * indent)
        chunks.append('@')
        dispatch(subnode, indent)
        chunks.append('\n')
    chunks.append('    ' * indent)
    chunks.append('def ')
    dispatch(node.name, indent)
    chunks.append('(')
    dispatch(node.args, indent)
    chunks.append('):\n')
    indent += 1
    prev = None
    for subnode in node.body:
        chunks.append('    ' * indent)
        dispatch(subnode, indent)
        chunks.append('\n')
        prev = subnode
    if node.body:
        chunks.pop()


def format_arguments(node, indent, ext=None):
    no_default_arg_count = len(node.args) - len(node.defaults)
    for i, subnode in enumerate(node.args, - no_default_arg_count):
        dispatch(subnode, indent)
        if i >= 0:
            chunks.append('=')
            dispatch(node.defaults[i], indent)
        chunks.append(', ')
    if node.args:
        chunks.pop()
    #node.vararg
    #node.kwarg


def format_Attribute(node, indent, ext=None):
    dispatch(node.value, indent)
    chunks.append('.')
    chunks.append(node.attr)


def format_IsNot(node, indent, ext=None):
    chunks.append(' is not ')


def format_Not(node, indent, ext=None):
    chunks.append('not')


def format_While(node, indent, ext=None):
    chunks.append('while ')
    dispatch(node.test, indent)
    chunks.append(':')
    chunks.append('\n')
    indent += 1
    for subnode in node.body:
        chunks.append('    ' * indent)
        dispatch(subnode, indent)
        chunks.append('\n')
    indent -= 1
    if node.orelse:
        chunks.append('    ' * indent)
        chunks.append('else:')
        chunks.append('\n')
        indent += 1
        for subnode in node.orelse:
            chunks.append('    ' * indent)
            dispatch(subnode, indent)
            chunks.append('\n')
    if node.body or node.orelse:
        chunks.pop()


def format_For(node, indent, ext=None):
    chunks.append('for ')
    dispatch(node.target, indent)
    chunks.append(' in ')
    dispatch(node.iter, indent)
    chunks.append(':')
    chunks.append('\n')
    indent += 1
    for subnode in node.body:
        chunks.append('    ' * indent)
        dispatch(subnode, indent)
        chunks.append('\n')
    indent -= 1
    if node.orelse:
        chunks.append('    ' * indent)
        chunks.append('else:')
        chunks.append('\n')
        indent += 1
        for subnode in node.orelse:
            chunks.append('    ' * indent)
            dispatch(subnode, indent)
            chunks.append('\n')
    if node.body or node.orelse:
        chunks.pop()


def format_NotIn(node, indent, ext=None):
    chunks.append(' not in ')


def format_Break(node, indent, ext=None):
    chunks.append('break')


def format_In(node, indent, ext=None):
    chunks.append(' in ')


def format_And(node, indent, ext=None):
    chunks.append(' and ')


def format_Is(node, indent, ext=None):
    chunks.append(' is ')


def format_IfExp(node, indent, ext=None):
    dispatch(node.body, indent)
    chunks.append(' if ')
    dispatch(node.test, indent)
    chunks.append(' else ')
    dispatch(node.orelse, indent)


def format_Add(node, indent, ext=None):
    chunks.append('+')


def format_Or(node, indent, ext=None):
    chunks.append(' or ')


def format_Num(node, indent, ext=None):
    chunks.append(str(node.n))


def format_Sub(node, indent, ext=None):
    chunks.append('-')


def format_Lt(node, indent, ext=None):
    chunks.append(' < ')


def format_LtE(node, indent, ext=None):
    chunks.append(' <= ')


def format_Gt(node, indent, ext=None):
    chunks.append(' > ')


def format_GtE(node, indent, ext=None):
    chunks.append(' >= ')


def format_USub(node, indent, ext=None):
    chunks.append('-')


def format_AugAssign(node, indent, ext=None):
    dispatch(node.target, indent)
    chunks.append(' ')
    dispatch(node.op, indent)
    chunks.append('=')
    chunks.append(' ')
    dispatch(node.value, indent)


def format_Raise(node, indent, ext=None):
    chunks.append('raise ')
    dispatch(node.type, indent)
    #node.inst
    #node.tback


def format_Subscript(node, indent, ext=None):
    dispatch(node.value, indent)
    chunks.append('[')
    dispatch(node.slice, indent)
    chunks.append(']')


def format_With(node, indent, ext=None):
    chunks.append('with ')
    dispatch(node.context_expr, indent)
    if node.optional_vars:
        chunks.append(' as ')
        dispatch(node.optional_vars, indent)
    chunks.append(':')
    chunks.append('\n')
    indent += 1
    for subnode in node.body:
        chunks.append('    ' * indent)
        dispatch(subnode, indent)
        chunks.append('\n')
    if node.body:
        chunks.pop()


def format_If(node, indent, ext=None):
    chunks.append('if ')
    if ext == 'elif':
        chunks.pop()
    dispatch(node.test, indent)
    chunks.append(':')
    chunks.append('\n')
    indent += 1
    for subnode in node.body:
        chunks.append('    ' * indent)
        dispatch(subnode, indent)
        chunks.append('\n')
    indent -= 1
    if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
        chunks.append('    ' * indent)
        chunks.append('elif ')
        dispatch(node.orelse[0], indent, ext='elif')
        chunks.append('\n')
    elif node.orelse:
        chunks.append('    ' * indent)
        chunks.append('else:')
        chunks.append('\n')
        indent += 1
        for subnode in node.orelse:
            chunks.append('    ' * indent)
            dispatch(subnode, indent)
            chunks.append('\n')
    if node.body or node.orelse:
        chunks.pop()
    indent -= 1


def format_Compare(node, indent, ext=None):
    dispatch(node.left, indent)
    for subnode in node.ops:
        dispatch(subnode, indent)
    for subnode in node.comparators:
        dispatch(subnode, indent)


def format_Expr(node, indent, ext=None):
    dispatch(node.value, indent)


def format_Name(node, indent, ext=None):
    chunks.append(node.id)


def format_Call(node, indent, ext=None):
    dispatch(node.func, indent)
    chunks.append('(')
    for subnode in node.args:
        dispatch(subnode, indent)
        chunks.append(', ')
    for subnode in node.keywords:
        dispatch(subnode, indent)
        chunks.append(', ')
    if node.args or node.keywords:
        chunks.pop()
    chunks.append(')')
    #node.starargs
    #node.kwargs


def format_Eq(node, indent, ext=None):
    chunks.append(' == ')


def format_NotEq(node, indent, ext=None):
    chunks.append(' != ')


def format_Mult(node, indent, ext=None):
    chunks.append('*')


def format_Str(node, indent, ext=None):
    quote = "'" if "'" not in node.s else '"'
    chunks.append(quote)
    chunks.append(node.s.encode('unicode_escape'))
    chunks.append(quote)


def format_DictComp(node, indent, ext=None):
    chunks.append('{')
    dispatch(node.key, indent)
    chunks.append(': ')
    dispatch(node.value, indent)
    chunks.append(' ')
    for subnode in node.generators:
        dispatch(subnode, indent)
    chunks.append('}')


def format_ListComp(node, indent, ext=None):
    chunks.append('[')
    dispatch(node.elt, indent)
    chunks.append(' ')
    for subnode in node.generators:
        dispatch(subnode, indent)
    chunks.append(']')


def format_comprehension(node, indent, ext=None):
    chunks.append('for ')
    dispatch(node.target, indent)
    chunks.append(' in ')
    dispatch(node.iter, indent)
    if node.ifs:
        chunks.append(' if ')
        for subnode in node.ifs:
            dispatch(subnode, indent)


def format_Tuple(node, indent, ext=None):
    if not isinstance(node.ctx, ast.Store):
        chunks.append('(')
    for subnode in node.elts:
        dispatch(subnode, indent)
        chunks.append(', ')
    if node.elts:
        chunks.pop()
    if not isinstance(node.ctx, ast.Store):
        chunks.append(')')


def format_keyword(node, indent, ext=None):
    dispatch(node.arg, indent)
    chunks.append('=')
    dispatch(node.value, indent)


def format_Index(node, indent, ext=None):
    dispatch(node.value, indent)


def format_UnaryOp(node, indent, ext=None):
    dispatch(node.op, indent)
    chunks.append(' ')
    dispatch(node.operand, indent)


def format_Pass(node, indent, ext=None):
    chunks.append('pass')


def format_BoolOp(node, indent, ext=None):
    for i, subnode in enumerate(node.values):
        dispatch(subnode, indent)
        if i + 1 < len(node.values):
            dispatch(node.op, indent)


def format_BinOp(node, indent, ext=None):
    dispatch(node.left, indent)
    chunks.append(' ')
    dispatch(node.op, indent)
    chunks.append(' ')
    dispatch(node.right, indent)


def format_Assign(node, indent, ext=None):
    for subnode in node.targets:
        dispatch(subnode, indent)
        chunks.append(', ')
    if node.targets:
        chunks.pop()
    chunks.append(' = ')
    dispatch(node.value, indent)


def format_List(node, indent, ext=None):
    chunks.append('[')
    for subnode in node.elts:
        dispatch(subnode, indent)
        token.append(', ')
    if node.elts:
        token.pop()
    chunks.append(']')


funcmap = {k: v for k, v in locals().items() if callable(v)}


def dispatch(node, indent, ext=None):
    typename = type(node).__name__
    funcname = 'format_{}'.format(typename)
    if funcname in funcmap:
        func = funcmap[funcname]
        func(node, indent, ext)
    else:
        chunks.append(' <{}> '.format(type(node).__name__))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filepath')
    args = parser.parse_args()

    with open(args.filepath) as f:
        content = f.read()
        root = ast.parse(content)
        tokens = tokenize.generate_tokens(StringIO.StringIO(content).readline)

    comments = [t for t in tokens if t[0] == tokenize.COMMENT]

    prev = None
    for node in root.body:

        while comments:
            next_comment_txt = comments[0][1]
            next_comment_lineno = comments[0][2][0]
            next_comment_col = comments[0][2][1]
            if next_comment_lineno > node.lineno:
                break
            if prev is not None:
                chunks.append('\n')
            chunks.append(' ' * next_comment_col)
            chunks.append(next_comment_txt)
            comments.pop(0)
            prev = tokenize.COMMENT

        line_count = 0
        if isinstance(prev, ast.FunctionDef):
            line_count = 2
        elif isinstance(node, ast.FunctionDef):
            line_count = 2
        elif isinstance(prev, (ast.Import, ast.ImportFrom)) and not isinstance(node, (ast.Import, ast.ImportFrom)):
            line_count = 2
        elif type(prev) != type(node):
            line_count = 1

        chunks.append('\n' * (line_count + 1))
        dispatch(node, indent=0)
        prev = node
    chunks.append('\n')

    print(''.join(chunks))


if __name__ == '__main__':
    main()

