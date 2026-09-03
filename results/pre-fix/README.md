# 修复前的原始数据（保留作为不可复现问题的证据）

这几份是变异引擎修复**之前**跑出来的，同一实验四次得到四个不同结果：

| 文件 | 杀伤率 |
|---|---|
| mutation_baseline_owntests.json | 46.7% |
| mutation_recheck.json | 49.3% |
| mutation_hashseed_1.json | 48.0% |
| mutation_hashseed_2.json | 49.3% |
| （另有干净 clone 复现） | 50.7% |

两个根因见 [../run01_结果.md](../run01_结果.md) 附录：
1. 变异了 docstring（等价变异体，占了一半）
2. `.pyc` 缓存复用（同大小 + 同秒写入 → 跑的不是当前变异体）

修复后稳定在 56.8%（连跑三次一致，见 `../mutation_det_*.json`）。

**保留这些文件是为了让「不可复现」这件事本身可复现。**
