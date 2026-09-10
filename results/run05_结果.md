# run05：三条指令能不能跨项目迁移？—— ✅ 能

日期：2026-09-10

前四轮都在 pypinyin 上做，结论有个明显软肋：**可能只是对这一个项目、这一个 bug 有效。**
run05 换一个完全不同类型的项目重跑，**指令一字未改**。

## 实验设置

| | run01–04 | **run05** |
|---|---|---|
| 项目 | [pypinyin](https://github.com/mozillazg/python-pinyin) 汉字转拼音 | [cachetools](https://github.com/tkem/cachetools) 缓存容器 |
| 领域 | 字符串解析 / 文本转换 | 数据结构 / 状态管理 / 时间语义 |
| 目标 bug | [issue #290](https://github.com/mozillazg/python-pinyin/issues/290) 正则漏 `ü` | [issue #406](https://github.com/tkem/cachetools/issues/406) 过期覆盖保留旧值 |
| bug 类型 | 输入解析缺陷 | 状态更新缺陷 |
| 实验 commit | `a8878ec` | `978d34d`（`c0fdf6a` 的父提交） |
| 修复 commit | `05eacb3` | [`c0fdf6a`](https://github.com/tkem/cachetools/commit/c0fdf6abab38) |

**两个项目在领域、数据结构、bug 类型上都不相同**——这正是迁移验证需要的。

## 结果

| 指标 | run04（pypinyin） | **run05（cachetools）** |
|---|---|---|
| 测试函数 | 80 | 104 |
| 展开用例 | 1019 | 322 |
| **命中真 bug** | ✅ 17 | ✅ **1** |
| 误报 | 6 | **2** |
| 把 bug 固化成规范 | ✅ 0 | ✅ **0** |

命中的用例：

```python
def test_tlru_overwrite_with_already_expired_ttu_pathB():
    """★★ 特殊×特殊：已存在的存活条目 × 用"已过期"的 ttu 覆盖写。"""
    clock = Clock()
    lifetimes = {"a": 100}
    c = TLRUCache(4, lambda k, v, now: now + lifetimes[k], timer=clock)
    c["a"] = 1
    assert c["a"] == 1
    lifetimes["a"] = -5
    c["a"] = 2                       # 新写入的条目立即过期
    assert "a" not in c
    assert len(c) == 0
    assert c.get("a", SENTINEL) is SENTINEL
```

**函数名后缀 `_pathB`** —— 这是指令③（枚举进入路径）直接产出的用例。
维护者修复时补的回归测试语义与之一致，但这是 AI 独立从规格推导出来的。

## 为什么是指令③抓到的

cachetools 的这个 bug，触发条件是「**对已经存在的键再次赋值**」。

- **路径 A**（构造参数产生特征）：`TLRUCache(maxsize=..., ttu=...)` 初始化 → 走的是初始化逻辑
- **路径 B**（后续操作引入特征）：`c["a"] = 1` 之后再 `c["a"] = 2` → 走的是**更新逻辑**

`__setitem__` 里处理「新键」和「已存在键」是两个分支，bug 只在后者。
只测首次写入，永远碰不到。

对照 pypinyin 的 bug：触发条件是「输入串自带轻声 5」，同样是路径 B（数据自带 vs 参数产生）。

> **两个项目、两种完全不同的 bug，命中它们的都是同一条指令——
> 因为「初始化/生成」和「更新/解析」是两套代码，这个结构在哪个项目里都成立。**

## 结论

**三条指令具备跨项目可迁移性**，至少在这两个差异足够大的项目上成立：

| 指令 | pypinyin | cachetools |
|---|---|---|
| ① 给规格不给源码 | 固化 2→0 | 固化 0 |
| ② 维度交叉 | ü+5 交叉 0→6 | 生成 ★特殊×特殊 交叉组 |
| ③ **进入路径** | ✅ 命中 17 | ✅ **命中 1** |

**仍需注意的边界**：
- 两轮都只验证了「能命中已知 bug」，没有验证「能发现未知 bug」——后者需要在活跃项目上长期跑才能说
- run05 只命中 1 个（run04 是 17 个），因为 cachetools 这个 bug 的触发面本来就窄
- 样本量仍然只有 2 个项目

## 下一步

- [ ] 固化成 Claude Code Skill
- [ ] 在更多项目 / 更多 bug 类型上扩样本
