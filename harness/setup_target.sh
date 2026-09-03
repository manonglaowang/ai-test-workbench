#!/usr/bin/env bash
# 拉取被测项目并切到实验 commit
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="$ROOT/targets/pypinyin"
BUG_COMMIT="a8878ec0fce00466a2799349b39e6718e4972195"   # bug 仍存在
FIX_COMMIT="05eacb3b52ae500618103bff22154e81b86943bd"   # Fixed #290

mkdir -p "$ROOT/targets"
if [ ! -d "$TARGET/.git" ]; then
  echo "克隆 pypinyin..."
  git clone -q https://github.com/mozillazg/python-pinyin.git "$TARGET"
fi

MODE="${1:-bug}"
case "$MODE" in
  bug) SHA=$BUG_COMMIT; echo "→ 切到 BUG 版 (a8878ec)" ;;
  fix) SHA=$FIX_COMMIT; echo "→ 切到 修复版 (05eacb3)" ;;
  *)   echo "用法: $0 [bug|fix]"; exit 1 ;;
esac
git -C "$TARGET" checkout -q "$SHA"
git -C "$TARGET" log --oneline -1
