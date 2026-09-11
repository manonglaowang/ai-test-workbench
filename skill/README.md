# test-gen-blindspot · Claude Code Skill

把五轮实验的结论固化成可复用的 Skill。

## 安装

```bash
cp -r skill ~/.claude/skills/test-gen-blindspot
```

或复制到 `~/.codex/skills/`（Codex）。

## 内容

| 文件 | 用途 |
|---|---|
| `SKILL.md` | 三条指令 + 实验数据 + 评审清单 + 已知边界 |
| `references/prompt-template.md` | 可直接复制的 prompt 模板 |
| `references/dimensions.md` | 维度枚举引导问题 + 路径判定清单 |
| `scripts/extract_spec.py` | 从源文件提取规格（剥掉实现），带残留自检 |
| `scripts/verify_hits.sh` | 双版本验证：真检出 / 误报 / bug固化 三分类 |
| `scripts/mutate.py` | 变异测试引擎，13 算子，零依赖 |

## 快速开始

```bash
# 1. 提取规格
python scripts/extract_spec.py src/yourmod.py -o SPEC.md

# 2. 用 references/prompt-template.md + SPEC.md 生成用例

# 3. 若验证已知 bug，双版本对照
bash scripts/verify_hits.sh tests/test_generated.py \
  "git checkout <bug版commit>" "git checkout <修复版commit>" python
```
