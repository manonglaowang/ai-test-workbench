#!/usr/bin/env python3
"""
最小变异测试引擎。
对目标源文件注入单点变异，用给定测试集去跑，统计杀伤率。

用法:
  python harness/mutate.py --target <src.py> --tests <test_dir_or_file> [--limit N]
"""
import argparse, ast, io, os, re, shutil, subprocess, sys, tempfile, json
from pathlib import Path

# ── 变异算子：(名称, 匹配正则, 替换) ──
OPERATORS = [
    ("比较符 > → >=",      r'(?<![<>=!])>(?![=>])',   '>='),
    ("比较符 < → <=",      r'(?<![<>=!])<(?![=<])',   '<='),
    ("比较符 >= → >",      r'>=',                     '>'),
    ("比较符 <= → <",      r'<=',                     '<'),
    ("相等 == → !=",       r'==',                     '!='),
    ("布尔 True → False",  r'\bTrue\b',               'False'),
    ("布尔 False → True",  r'\bFalse\b',              'True'),
    ("逻辑 and → or",      r'\band\b',                'or'),
    ("逻辑 or → and",      r'\bor\b',                 'and'),
    ("否定 not 删除",       r'\bnot\s+',              ''),
    ("加减 + → -",         r'(?<![+\-=<>!*/])\+(?![+=])', '-'),
    ("索引 0 → 1",         r'\[0\]',                  '[1]'),
    ("索引 -1 → 0",        r'\[-1\]',                 '[0]'),
]

def find_mutations(src: str):
    """返回 [(算子名, 行号, 原行, 变异后整份源码)]"""
    lines = src.split('\n')
    muts = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        for name, pat, rep in OPERATORS:
            for m in re.finditer(pat, line):
                new_line = line[:m.start()] + rep + line[m.end():]
                if new_line == line:
                    continue
                new_lines = lines[:]; new_lines[i] = new_line
                candidate = '\n'.join(new_lines)
                try:
                    ast.parse(candidate)          # 语法必须仍合法
                except SyntaxError:
                    continue
                muts.append({
                    "op": name, "line": i + 1,
                    "before": line.strip(), "after": new_line.strip(),
                    "src": candidate,
                })
    return muts

def run_tests(test_path, cwd, python_bin, timeout=120, extra=None):
    """返回 True=测试全通过"""
    cmd = [python_bin, "-m", "pytest", str(test_path), "-q", "--no-header", "-x", "-p", "no:cacheprovider"]
    if extra: cmd += extra
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return r.returncode == 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True, help="被变异的源文件")
    ap.add_argument("--tests", required=True, help="测试文件或目录")
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--limit", type=int, default=0, help="最多跑几个变异体，0=全部")
    ap.add_argument("--label", default="run", help="本轮标签，用于输出文件名")
    ap.add_argument("--out", default="results")
    ap.add_argument("--deselect", action="append", default=[], help="排除的用例 node id，可多次")
    a = ap.parse_args()

    target = Path(a.target).resolve()
    original = target.read_text(encoding="utf-8")
    cwd = Path.cwd()

    muts = find_mutations(original)
    if a.limit: muts = muts[:a.limit]
    print(f"目标文件: {target.name}")
    print(f"生成变异体: {len(muts)} 个")

    # 基线：未变异时测试必须全绿，否则杀伤率无意义
    print("基线检查（原始代码跑测试）...", end=" ", flush=True)
    extra = [x for d in a.deselect for x in ("--deselect", d)]
    if not run_tests(a.tests, cwd, a.python, extra=extra):
        print("❌ 基线未通过 —— 测试集在原始代码上就有失败，无法计算杀伤率")
        print("   请先修掉失败用例，或确认这些失败是「命中真 bug」（那属于轨道 A 的结果）")
        target.write_text(original, encoding="utf-8")
        sys.exit(2)
    print("✅ 全绿")

    killed, survived, errors = [], [], []
    try:
        for idx, m in enumerate(muts, 1):
            target.write_text(m["src"], encoding="utf-8")
            try:
                passed = run_tests(a.tests, cwd, a.python, extra=extra)
                (survived if passed else killed).append(m)
                mark = "存活" if passed else "杀死"
            except subprocess.TimeoutExpired:
                errors.append(m); mark = "超时"
            print(f"  [{idx}/{len(muts)}] L{m['line']:>4} {m['op']:<18} → {mark}")
    finally:
        target.write_text(original, encoding="utf-8")   # 无论如何恢复原文件
        print("已恢复原始源码")

    valid = len(killed) + len(survived)
    rate = len(killed) / valid * 100 if valid else 0.0
    print(f"\n{'='*52}")
    print(f"杀死 {len(killed)} / 有效 {valid}   杀伤率 = {rate:.1f}%")
    if errors: print(f"超时/异常 {len(errors)} 个（不计入）")

    os.makedirs(a.out, exist_ok=True)
    out = Path(a.out) / f"mutation_{a.label}.json"
    out.write_text(json.dumps({
        "target": str(target), "tests": a.tests, "label": a.label,
        "total": len(muts), "killed": len(killed),
        "survived": len(survived), "errors": len(errors),
        "kill_rate": round(rate, 2),
        "survived_detail": [{k: v for k, v in m.items() if k != "src"} for m in survived],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"明细已写入 {out}")

if __name__ == "__main__":
    main()
