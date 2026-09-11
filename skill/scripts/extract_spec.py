#!/usr/bin/env python3
"""
从 Python 源文件提取「规格」：只要签名和 docstring，剥掉全部实现。
用于指令①（给规格不给源码）。

用法:
  python extract_spec.py <源文件> [-o SPEC.md] [--private]
"""
import argparse, ast, pathlib, sys

def fmt_args(fn):
    a = fn.args
    parts, defaults = [], [None] * (len(a.args) - len(a.defaults)) + list(a.defaults)
    for arg, d in zip(a.args, defaults):
        parts.append(arg.arg if d is None else f"{arg.arg}={ast.unparse(d)}")
    if a.vararg: parts.append(f"*{a.vararg.arg}")
    for arg, d in zip(a.kwonlyargs, a.kw_defaults):
        parts.append(arg.arg if d is None else f"{arg.arg}={ast.unparse(d)}")
    if a.kwarg: parts.append(f"**{a.kwarg.arg}")
    return ", ".join(parts)

DUNDER_KEEP = {'__init__','__getitem__','__setitem__','__delitem__',
               '__contains__','__len__','__iter__','__call__','__eq__'}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("-o", "--output", default="SPEC.md")
    ap.add_argument("--private", action="store_true", help="也包含下划线开头的成员")
    a = ap.parse_args()

    src = pathlib.Path(a.source).read_text(encoding="utf-8")
    tree = ast.parse(src)
    keep = lambda n: a.private or not n.startswith('_') or n in DUNDER_KEEP

    out = [f"# {pathlib.Path(a.source).stem} 规格说明", "",
           "> 只含签名与文档说明，**不含任何实现代码**。",
           "> 期望行为请依据「按规范应该返回什么」推导，而非「代码会返回什么」。", ""]
    md = ast.get_docstring(tree)
    if md: out += ["## 模块说明", "", "```", md, "```", ""]

    nf = nc = 0
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and keep(node.name):
            nf += 1
            out += [f"## `{node.name}({fmt_args(node)})`", "",
                    "```", ast.get_docstring(node) or "（无文档）", "```", ""]
        elif isinstance(node, ast.ClassDef) and keep(node.name):
            nc += 1
            bases = ", ".join(ast.unparse(b) for b in node.bases)
            out += [f"## class `{node.name}({bases})`", "",
                    "```", ast.get_docstring(node) or "（无文档）", "```", ""]
            for m in node.body:
                if isinstance(m, ast.FunctionDef) and keep(m.name):
                    nf += 1
                    out += [f"### `{node.name}.{m.name}({fmt_args(m)})`", ""]
                    d = ast.get_docstring(m)
                    if d: out += ["```", d, "```", ""]

    text = "\n".join(out)
    pathlib.Path(a.output).write_text(text, encoding="utf-8")

    # 自检：不该出现实现代码
    import re
    leak = [l for l in text.splitlines()
            if re.match(r"^\s+(return |if |for |while |raise |yield |self\.\w+\s*=)", l)]
    print(f"✓ {a.output}：{nc} 个类，{nf} 个函数/方法")
    if leak:
        print(f"⚠ 疑似实现代码残留 {len(leak)} 行（docstring 内的示例代码通常无害，请人工确认）：")
        for l in leak[:5]: print("   ", l.strip()[:70])
    else:
        print("✓ 零实现代码残留")

if __name__ == "__main__":
    main()
