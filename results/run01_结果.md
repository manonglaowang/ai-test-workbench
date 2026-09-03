# run01 实验结果

被测：pypinyin `_tone_convert.py` @ `a8878ec`（bug 版）
生成方：全新上下文 agent，盲测协议（不给 issue、不给修复码、禁止联网）
日期：2026-09-03

## 产出规模

| 项 | 值 |
|---|---|
| 测试文件行数 | 979 |
| test 函数数 | 84 |
| 参数化后用例总数 | 426 |
| 语法可执行率 | 100%（426/426 全部被 pytest 收集） |

## 轨道 A：能不能发现真 bug

**结论：没有。0 命中。**

| 判定项 | 结果 |
|---|---|
| bug 版跑测 | 7 failed / 419 passed |
| **修复版跑测** | **9 failed / 417 passed** |
| 命中 issue #290 | ❌ **0 个** |
| 误报（期望值写错） | **7 个**（修复版上照样失败，证明与 bug 无关） |
| **把 bug 固化成规范** | 🔴 **2 个** |

### 最反直觉的发现：AI 把 bug 写成了期望值

```python
# AI 生成的断言
assert to_tone3('sha5ng') == 'shang5'      # bug 版行为
# 修复后正确行为
to_tone3('sha5ng') == 'shang'
```

这 2 个用例在 bug 版是绿的，在修复版变红。
**如果把这套测试当回归套件，维护者真正的修复会被判定为「回归失败」。**

### AI 其实"看到"了 bug 位置，但判成了设计

生成方在自评风险时写道：

> "`to_tone2`/`to_tone3` 对含 `ü` 输入的处理依赖 `RE_TONE3` 的 `[a-zê]` **不匹配 `ü`** 这一细节"

它准确定位了根因所在的正则，但把它理解为**既定行为**，而不是缺陷。

## 轨道 B：变异测试杀伤率

75 个有效变异体，同一份源码。

| 测试集 | 用例数 | 杀死 | 杀伤率 |
|---|---|---|---|
| 项目自带（维护者写的） | 141 | 35 | **46.7%** |
| AI 生成（排除 7 个误报后） | 419 | 49 | **65.3%** |

**AI 高出 18.6 个百分点。**

## 核心矛盾

| | 项目自带 | AI 生成 |
|---|---|---|
| 变异杀伤率 | 46.7% | **65.3%** ⬆ |
| 发现真 bug | ❌ 没有 | ❌ 没有 |
| 把 bug 写成规范 | — | 🔴 2 处 |

**覆盖率更高，但一样没抓到 bug；而且还把 bug 固化了。**

根因：**AI 的期望值是从代码推导出来的，不是从意图推导的。**
它测的是「代码做了什么」，不是「代码应该做什么」。
代码与意图不一致的地方——也就是 bug 所在——恰恰是这种方法的盲区。

## 对「人搭环境，AI 处理用例脚本」的验证

数据支持这个分工，但**必须加一条**：

- ✅ AI 适合做覆盖面（杀伤率 65.3% vs 46.7%，实打实的提升）
- 🔴 AI 不能独立定义「正确行为」——期望值必须来自规格文档或人，不能来自被测代码本身
- 🔴 人工评审不是流程摆设，是**防止 bug 被固化成规范**的唯一防线

## 复现

```bash
git clone <repo> && cd ai-test-workbench
python3 -m venv .venv && .venv/bin/pip install pytest pytest-cov
bash harness/setup_target.sh          # clone pypinyin 并 checkout 到 a8878ec
.venv/bin/python -m pytest runs/run01_blind/test_generated.py
.venv/bin/python harness/mutate.py --target targets/pypinyin/pypinyin/style/_tone_convert.py \
  --tests targets/pypinyin/tests/contrib/test_tone_convert.py --label baseline
```
