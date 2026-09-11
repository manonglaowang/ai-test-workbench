#!/usr/bin/env bash
# 双版本验证：区分「真检出 / 误报 / bug 固化」
#
# 用法: verify_hits.sh <测试文件> <切到bug版的命令> <切到修复版的命令> [python路径]
# 注意：切换命令在子 shell 中执行，其 cd 不会影响测试运行目录。
set -u
T="$1"; BUG_CMD="$2"; FIX_CMD="$3"; PY="${4:-python}"
[ -f "$T" ] || { echo "❌ 测试文件不存在: $T"; exit 1; }

run() {
  ( eval "$1" ) >/dev/null 2>&1 || { echo "❌ 版本切换失败: $1" >&2; exit 1; }
  local out
  out="$("$PY" -m pytest "$T" -q --no-header -p no:cacheprovider --tb=no 2>&1)"
  if ! grep -qE '[0-9]+ (passed|failed)' <<<"$out"; then
    echo "❌ pytest 未正常执行，原始输出：" >&2; echo "$out" | tail -5 >&2; exit 1
  fi
  grep '^FAILED' <<<"$out" | sed 's/^FAILED //; s/ - .*//' | sort
}

run "$BUG_CMD" > /tmp/_vh_bug.txt
run "$FIX_CMD" > /tmp/_vh_fix.txt
echo "bug版失败 $(wc -l < /tmp/_vh_bug.txt | tr -d ' ') 条 | 修复版失败 $(wc -l < /tmp/_vh_fix.txt | tr -d ' ') 条"
echo; echo "✅ 真检出（只在 bug 版失败）:"
comm -23 /tmp/_vh_bug.txt /tmp/_vh_fix.txt | sed 's/^/   /'
echo; echo "🔴 把 bug 固化成规范（只在修复版失败，必须删掉）:"
comm -13 /tmp/_vh_bug.txt /tmp/_vh_fix.txt | sed 's/^/   /'
echo; echo "⚠️  误报（两版都失败，期望值可能写错）: $(comm -12 /tmp/_vh_bug.txt /tmp/_vh_fix.txt | wc -l | tr -d ' ') 条"
comm -12 /tmp/_vh_bug.txt /tmp/_vh_fix.txt | head -10 | sed 's/^/   /'
