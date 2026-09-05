# AI 测试工作台 · 实验记录

> **AI 能不能发现真实开源项目里、当时没被发现的 bug？**
> 一个可复现的对照实验。数据难看也照实放。

---

## TL;DR

让 AI 在**完全盲测**条件下（不给 issue、不给修复代码、禁止联网）为 pypinyin 的
`_tone_convert.py` 生成测试用例，然后检验它能否发现三周后才被修复的真实 bug（[issue #290](https://github.com/mozillazg/python-pinyin/issues/290)）。

| 结果 | 数值 |
|---|---|
| AI 生成用例 | 84 个测试函数 / 426 个参数化用例 / 979 行 |
| 语法可执行率 | 100% |
| **发现真 bug** | ❌ **0 个** |
| 误报（期望值写错） | 7 个 |
| 🔴 **把 bug 固化成规范** | **2 个** |
| 变异杀伤率 · AI | **81.1%** (30/37) |
| 变异杀伤率 · 项目自带 141 个测试 | **56.8%** (21/37) |

**一句话结论**：AI 生成的测试覆盖面明显更强（+24.3pp），但**一个 bug 都没抓到**，
还把 bug 写成了期望值——如果当回归套件用，维护者真正的修复会被判定为「回归失败」。

**根因**：AI 的期望值是从**代码**推导的，不是从**意图**推导的。
它测的是「代码做了什么」，而 bug 的定义恰恰是「代码做的 ≠ 应该做的」。这是结构性盲区。

---

## 实验设计

### 被测对象

| 项 | 值 |
|---|---|
| 项目 | [pypinyin](https://github.com/mozillazg/python-pinyin) · MIT · 5.3k★ |
| 模块 | `pypinyin/style/_tone_convert.py` |
| **实验 commit** | [`a8878ec`](https://github.com/mozillazg/python-pinyin/commit/a8878ec0fce00466a2799349b39e6718e4972195) (2022-12-24) — bug 仍存在 |
| 修复 commit | [`05eacb3`](https://github.com/mozillazg/python-pinyin/commit/05eacb3b52ae500618103bff22154e81b86943bd) (2023-01-14) — "Fixed #290" |

**Bug 本质**：正则字符类漏了 `ü`

```diff
- RE_TONE2 = re.compile(r'([aeoiuvnmê])([1-5])$')
+ RE_TONE2 = re.compile(r'([aeoiuvnmêü])([1-5])$')
```

已验证：在 `a8878ec` 上，issue 描述的 7 个 case 全部复现。
**同时，项目自带的 141 个测试在该版本上全部通过**——维护者自己的测试套件也没抓到。

### 双轨测量

**轨道 A · 时间旅行** — AI 只看 bug 版源码，能否命中 issue #290
**轨道 B · 变异测试** — 注入 37 个单点变异，统计杀伤率，与项目自带测试对照

### 盲测纪律

- ❌ 不告诉 AI 有 bug ❌ 不提 issue / `ü` / 「边界」等引导词
- ❌ 不给修复后代码 ❌ 禁止联网检索该项目
- ✅ 只给：模块源码 + 该版本 docstring
- ✅ prompt 与原始输出全部存档于 [`runs/`](runs/)

---

## 关键发现

### 1. AI 把 bug 写成了规范

```python
# AI 生成的断言（bug 版通过，修复版失败）
assert to_tone3('sha5ng') == 'shang5'   # ← bug 行为
# 修复后的正确行为
to_tone3('sha5ng') == 'shang'
```

### 2. AI 看到了根因位置，却判成了「设计如此」

生成方在自评风险时写道：

> "`to_tone2`/`to_tone3` 对含 `ü` 输入的处理依赖 `RE_TONE3` 的 `[a-zê]` **不匹配 `ü`** 这一细节"

它**准确定位了引发 bug 的那个正则**，但把它理解为既定行为，而不是缺陷。

### 3. 覆盖率高 ≠ 能发现 bug

| | 项目自带 | AI 生成 |
|---|---|---|
| 用例数 | 141 | 419 |
| 变异杀伤率 | 56.8% | **81.1%** ⬆ |
| 发现真 bug | ❌ | ❌ |
| 把 bug 写成规范 | — | 🔴 2 处 |

---

## 复现

```bash
git clone https://github.com/manonglaowang/ai-test-workbench.git
cd ai-test-workbench

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 拉取被测项目并切到 bug 版
bash harness/setup_target.sh bug

# 轨道 A：跑 AI 生成的用例
.venv/bin/python -m pytest runs/run01_blind/test_generated.py -q
# 预期：7 failed, 419 passed

# 切到修复版再跑，验证那 7 个是误报而非真 bug
bash harness/setup_target.sh fix
.venv/bin/python -m pytest runs/run01_blind/test_generated.py -q
# 预期：9 failed, 417 passed  ← 多出的 2 个就是「被固化的 bug」

# 轨道 B：变异测试对照
bash harness/setup_target.sh bug
.venv/bin/python harness/mutate.py \
  --target targets/pypinyin/pypinyin/style/_tone_convert.py \
  --tests  targets/pypinyin/tests/contrib/test_tone_convert.py \
  --python .venv/bin/python --label baseline
# 预期：56.8%
```

---

## 目录

```
docs/实验协议.md      跑之前定死的协议（指标不许事后加）
harness/mutate.py     变异测试引擎，13 个算子，零依赖
harness/setup_target.sh
runs/run01_blind/     盲测 prompt + AI 生成的 979 行用例
results/              三份原始数据 + 结论
```

## run02：给规格而不是源码（已完成）

唯一变量换成输入材料，结果见 [results/run02_结果.md](results/run02_结果.md)。

| 指标 | run01 给源码 | run02 给规格 |
|---|---|---|
| 命中真 bug | ❌ 0 | ❌ 0 |
| 误报 | 7 | **2** ⬇ |
| 把 bug 固化成规范 | 🔴 2 | ✅ **0** |
| 变异杀伤率 | 81.1% | 81.1% |

**修正了 run01 的结论。** 真正原因不是「期望值来自代码」，而是**组合覆盖为零**：

| | 含 ü/v 输入 | 含轻声 5 输入 | **两者同时** |
|---|---|---|---|
| run01 | 42 种 | 6 种 | **0** |
| run02 | 52 种 | 9 种 | **0** |

而 issue #290 的触发条件正是二者**同时出现**（`lün5`）。

> **AI 生成测试的盲区不在深度，在维度交叉。**
> 它能把每个特征维度铺得很宽，但不会主动构造特征之间的组合。
> 变异测试注入的是单点变异，正好落在 AI 擅长的单维射程内——
> 所以杀伤率 81.1% 和「抓不到 bug」并不矛盾，两者考的不是同一件事。

## run03：显式要求「维度交叉」（已完成）

详见 [results/run03_结果.md](results/run03_结果.md)。

| 指标 | run01 源码 | run02 规格 | run03 规格+矩阵 |
|---|---|---|---|
| 命中真 bug | ❌ 0 | ❌ 0 | ❌ **0** |
| 误报 | 7 | 2 | **17** ⬆ |
| bug 固化 | 🔴 2 | ✅ 0 | ✅ 0 |
| 变异杀伤率 | 81.1% | 81.1% | 51.4%* |
| **ü + 轻声5 交叉输入** | 0 | 0 | **6** ✅ |

\* 排除误报后测试集变小，存在混淆因素，不能直接理解为覆盖更差。

**矩阵指令有效但不够**：它成功让 AI 生成了 `lv5` `lü5` 这类交叉输入（0→6），
这些输入也确实触发 bug（`to_tone2('lv5')` 两版行为不同）——
**但 AI 只把它们用作断言的期望值，从未用作输入。**

三轮「把自带 5 的拼音作为输入」的调用次数：run01=0，run02=6（无一含 ü），run03=**0**。

> **最终盲区：AI 会枚举特征的取值，被要求时也能枚举取值的交叉，
> 但不会枚举「同一特征进入系统的不同路径」。**
>
> 轻声 5 有两条进入路径——由参数生成（`neutral_tone_with_five=True`）
> 和由输入携带（`'lv5'`）。三轮 AI 都只想到第一条。
> 而 issue #290 的根因正则只在**解析输入**时被调用，只有第二条路径能触发。
>
> 解析类 bug 最爱藏在这里：输出侧生成逻辑和输入侧解析逻辑通常是两套代码。

## 后续计划

- [ ] run04：补「特征进入方向」指令，验证能否命中
- [ ] run03：换 cachetools 做对照，验证结论是否跨项目成立
- [ ] 把「规格→用例→脚本→归因」沉淀成可复用 Skills

---

## 关于

**码农老王（王祥）| 在职高级软件质量保障工程师 · 深圳**
消费电子 / AI 硬件方向 · 嵌入式与设备类自动化测试 · CI/CD

公众号「**码农老王聊AI**」——只写自己跑通过的。

MIT License
