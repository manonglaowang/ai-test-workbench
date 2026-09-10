"""
cachetools 黑盒测试用例（仅依据 SPEC.md 的签名/文档 + MutableMapping 契约设计）
================================================================================

期望值来源声明
--------------
本文件所有断言的期望值均来自：
  (a) collections.abc.MutableMapping 的通用契约（len/iter/contains/get/pop/
      setdefault/popitem/clear/== 的相互一致性）；
  (b) SPEC.md 中的文档字符串字面含义（"first inserted" / "least recently used" /
      "least frequently used" / "per-item time-to-live" / "not already expired" /
      "The current size of the cache" / "Return the size of a cache element's value"）；
  (c) 容量语义的自明不变式：currsize == 各条目 size 之和，且 currsize <= maxsize。
不是来自任何实现代码（未阅读实现、未看 git 历史、未联网）。


================================================================================
第一步：输入特征维度表
================================================================================

D1  容器类型
    Cache | FIFOCache | LFUCache | LRUCache | RRCache | TTLCache | TLRUCache
    （前 6 个无时间语义或时间可禁用；后 2 个有时间语义）

D2  maxsize（容量）
    0（特殊：零容量） | 1（特殊：插一个就满） | 2~5（会发生淘汰） | 很大（永不淘汰）

D3  条目 size 的计算方式（getsizeof）
    None（默认，每条目恒为 1）
    | 常量函数（size 与数据无关，由参数决定）
    | 数据相关函数 len（size 由数据自带）
    | 返回 0 的函数（特殊：零尺寸条目）
    | 返回值 > maxsize（特殊：条目过大）
    | 由类继承覆写（而非构造参数传入）
    | 结果随外部状态/值 mutate 而改变（写入后才变化）

D4  键的新旧
    全新键 | 已存在的键再赋值 | 已被淘汰后重新插入的键 | 已过期的键再赋值
    | 相等但不同对象的键（1 / 1.0 / True） | 不可哈希的键（TypeError）

D5  值的特殊性
    普通值 | None（与"缺失"混淆） | 可变对象（写入后被 mutate） | 空容器（size 0）

D6  时间推进（仅 TTL/TLRU）
    不推进 | 推进到 < 过期时刻 | 推进到 == 过期时刻（边界） | 推进到 > 过期时刻
    | 各条目写入时刻不同导致过期时刻不同

D7  ttl / ttu 参数
    ttl = 0（特殊：立即过期） | ttl 正常 | ttl 极大（等价永不过期）
    ttu 恒定偏移 | ttu 按 key 不同 | ttu 返回过去/当前时刻（特殊：插入即过期）
    | ttu 在两次写同一 key 之间被改小 / 改大

D8  施加的操作
    __setitem__ | __getitem__ | get | __contains__ | __delitem__ | pop |
    setdefault | popitem | clear | len | iter | update | keys/values/items | ==

D9  淘汰触发方式
    不触发 | 按条目数触发 | 按 size 触发（可能一次淘汰多条）
    | 对已存在键赋更大值触发 | 过期回收腾出空间

D10 其他构造参数
    RRCache.choice（默认 random.choice | 自定义确定性函数）
    TTL/TLRU 的 timer（默认 time.monotonic | 自定义可控 Clock 对象）


================================================================================
第二步：两两交叉（重点：两个"本身就是特殊情况"的取值叠加）
================================================================================
交叉矩阵（每个单元格至少 1 个用例，标 ★ 者为"特殊×特殊"）：

  D1 × D2      : 7 种容器 × {0, 1, 2, 大}            ★ 任意容器 × maxsize=0
  D2 × D3      : maxsize=0 × getsizeof→0             ★ 零容量装零尺寸条目
                 maxsize=n × size 恰好 == maxsize    ★ 条目正好占满
                 maxsize=n × size >  maxsize         ★ 条目过大 → ValueError
  D3 × D4      : size 恰好 == maxsize × 对同键再赋同尺寸值 ★（自我淘汰陷阱）
                 size 变大 / 变小 × 已存在键          ★（currsize 增减账）
                 size > maxsize   × 已存在键          ★（异常时不得破坏原条目）
  D4 × D5      : 已存在键 × 值为 None
                 相等键 1/True × currsize 记账
  D3 × D5      : getsizeof=len × 写入后 mutate 值     ★（size 应按写入时记账）
  D2 × D8      : maxsize=0 × setdefault               ★（插入失败应抛 ValueError）
                 空缓存 × popitem/pop/del             ★（KeyError）
  D6 × D7      : ttl=0 × 任何写入                     ★（立即过期）
                 ttu 返回过去时刻 × 插入               ★（插入即过期）
                 推进到 == 过期时刻                    ★（边界：TTL 为半开区间）
  D6 × D4      : 过期键 × 再赋值（应刷新寿命）
                 过期键 × setdefault（应插新值而非返回陈旧值）
                 过期键 × pop(default) / del
  D6 × D9      : 整个缓存全过期后再插入（过期回收应腾出空间，而非报错/超容）
  D6 × D8      : 过期条目对 len/iter/contains/==/popitem 均不可见
  D1 × D9      : FIFO/LRU/LFU/RR 对"读过一次"的反应各不相同（同一操作序列，
                 4 种容器给出 4 种不同的淘汰结果）
  D2 × D6      : maxsize=1 × TTL 过期
  D10 × D9     : 自定义 choice × 淘汰（并检查 choice 收到的是当前键集合）


================================================================================
第三步（重点）：每个特征"进入系统的路径"—— 路径 A（构造参数） vs 路径 B（数据/后续操作）
================================================================================

特征 F1「条目 size 不为 1」
  路径 A: 构造时 getsizeof=常量函数（尺寸由参数决定，与数据无关）
          -> test_size_from_constant_getsizeof_param_pathA
  路径 B: 构造时 getsizeof=len，尺寸由写入的数据自身决定
          -> test_size_from_data_len_pathB
  路径 B': 子类覆写 getsizeof（不走构造参数，走类属性查找）
          -> test_size_from_subclass_override_pathB

特征 F2「缓存已满 / 需要淘汰」
  路径 A: 构造 maxsize=1（或 0），结构上一插就满
          -> test_full_by_construction_maxsize_one_pathA
  路径 B: maxsize 较大，靠后续插入把它填满
          -> test_full_by_insertions_pathB

特征 F3「条目过大（size > maxsize）」
  路径 A: 构造时 getsizeof 恒返回大值，第一次写入即过大
          -> test_oversized_on_first_insert_pathA
  路径 B: 先写入合法值，之后对同一个已存在的键改写为过大的值
          -> test_oversized_on_overwrite_existing_key_pathB（异常后原条目必须完好）

特征 F4「currsize 变化」
  路径 A: 由插入新键产生
          -> 各 size 用例
  路径 B: 由对已存在键改写（变大/变小）、删除、淘汰、过期回收、clear 产生
          -> test_currsize_shrinks_on_overwrite_with_smaller_value_pathB
             test_currsize_grows_on_overwrite_with_larger_value_pathB
             test_currsize_after_expire_pathB

特征 F5「条目已过期」
  路径 A: 构造参数决定 —— TTLCache(ttl=0) / TLRUCache(ttu 返回当前或过去时刻)
          -> test_ttl_zero_everything_expires_immediately_pathA
             test_tlru_ttu_in_the_past_item_never_visible_pathA
  路径 B: 构造参数正常，靠 timer 推进（写入之后属性才变化）
          -> test_ttl_expires_after_clock_advance_pathB
             test_tlru_expires_by_insertion_time_difference_pathB

特征 F6「同一条目的过期时刻不同」
  路径 A: ttu 函数按 key 返回不同寿命（参数决定）
          -> test_tlru_per_key_ttu_pathA
  路径 B: 同一个 ttu 函数，但插入时刻不同 / 对已存在键再赋值重算 ttu
          -> test_tlru_expires_by_insertion_time_difference_pathB
             test_tlru_overwrite_shortens_lifetime_pathB
             test_tlru_overwrite_extends_lifetime_pathB

特征 F7「LRU 近期性 / LFU 频度」
  路径 A: 由插入顺序（首次写入）建立
          -> test_lru_popitem_returns_least_recently_inserted_pathA
             test_lfu_popitem_by_read_frequency_pathA
  路径 B: 由后续读操作（__getitem__/get/setdefault）或对同键再赋值改变
          -> test_lru_getitem_refreshes_recency_pathB
             test_lru_get_refreshes_recency_pathB
             test_lru_setdefault_refreshes_recency_pathB
             test_lru_overwrite_refreshes_recency_pathB
             test_lfu_overwrite_keeps_frequency_pathB
             test_lfu_counter_reset_after_eviction_pathB

特征 F8「值的尺寸在写入之后才改变」
  路径 B 专属（无法由参数产生）
          -> test_size_recorded_at_write_time_not_reread_pathB

特征 F9「键已存在」
  路径 A: 无（键的存在只能由数据产生）
  路径 B: 同键二次写入 / 相等但不同对象的键 / 淘汰后重新插入 / 过期后重新插入
          -> test_overwrite_existing_key_does_not_grow_cache_pathB
             test_equal_keys_1_true_are_the_same_entry_pathB
             test_ttl_overwrite_refreshes_expiry_pathB

特征 F10「容器为空」
  路径 A: 刚构造
  路径 B: 全部删除 / clear() / 全部过期后
          -> test_empty_cache_contract / test_clear_then_reusable_pathB
             test_ttl_popitem_when_all_expired_raises_pathB

约定：用例名后缀 pathA / pathB 标注该用例走的是哪条路径；未标注者为不区分路径的
      通用契约/交叉用例。
"""

import random

import pytest

from cachetools import Cache, FIFOCache, LFUCache, LRUCache, RRCache, TTLCache, TLRUCache


# =============================================================================
# 测试工具（不使用 mock；timer 为自写的可控可调用对象）
# =============================================================================

NEVER = 10 ** 9  # 足够大的 ttl，使 TTL/TLRU 在通用用例中等价于"永不过期"

SENTINEL = object()


class Clock:
    """确定性时钟：一个可调用对象，只有显式 advance 才会前进。"""

    def __init__(self, start=0.0):
        self.now = float(start)

    def __call__(self):
        return self.now

    def advance(self, delta):
        self.now += delta
        return self.now


class RecordingChoice:
    """确定性的 RRCache.choice，同时记录每次被调用时收到的候选键集合。"""

    def __init__(self, pick=None):
        self.calls = []
        self._pick = pick or (lambda seq: seq[0])

    def __call__(self, seq):
        seq = list(seq)
        self.calls.append(list(seq))
        return self._pick(seq)


def never_ttu(key, value, now):
    """TLRU 的 ttu：返回条目的绝对过期时刻（"time to use"）。"""
    return now + NEVER


def make(kind, maxsize, getsizeof=None, clock=None):
    """用统一签名构造 7 种容器；有时间语义的两种被配置成"永不过期"。"""
    if kind is TTLCache:
        return TTLCache(maxsize, NEVER, timer=clock or Clock(), getsizeof=getsizeof)
    if kind is TLRUCache:
        return TLRUCache(maxsize, never_ttu, timer=clock or Clock(), getsizeof=getsizeof)
    if kind is RRCache:
        return RRCache(maxsize, choice=lambda seq: list(seq)[0], getsizeof=getsizeof)
    return kind(maxsize, getsizeof=getsizeof)


ALL_KINDS = [Cache, FIFOCache, LFUCache, LRUCache, RRCache, TTLCache, TLRUCache]
TIMED_KINDS = [TTLCache, TLRUCache]


def kind_id(kind):
    return kind.__name__


kinds = pytest.mark.parametrize("kind", ALL_KINDS, ids=kind_id)
timed_kinds = pytest.mark.parametrize("kind", TIMED_KINDS, ids=kind_id)


def make_timed(kind, maxsize, span, clock, getsizeof=None):
    """构造一个"条目写入后存活 span 个时间单位"的 TTL / TLRU 缓存。"""
    if kind is TTLCache:
        return TTLCache(maxsize, span, timer=clock, getsizeof=getsizeof)
    return TLRUCache(
        maxsize, lambda k, v, now: now + span, timer=clock, getsizeof=getsizeof
    )


def snapshot(cache):
    """按 MutableMapping 契约取当前可见内容（不依赖迭代顺序）。"""
    return {k: cache[k] for k in list(cache)}


# =============================================================================
# 组 0：MutableMapping 通用契约  (D1 × D8)
# =============================================================================


@kinds
def test_empty_cache_contract(kind):
    """D1 × D10(空容器，路径 A：刚构造)：空容器下所有读操作的契约。"""
    c = make(kind, 2)
    assert len(c) == 0
    assert c.currsize == 0
    assert c.maxsize == 2
    assert list(c) == []
    assert list(c.keys()) == []
    assert list(c.values()) == []
    assert list(c.items()) == []
    assert ("x" in c) is False
    assert c.get("x") is None
    assert c.get("x", "dflt") == "dflt"
    assert c.pop("x", "dflt") == "dflt"
    assert c == {}
    assert not c
    with pytest.raises(KeyError):
        c["x"]
    with pytest.raises(KeyError):
        del c["x"]
    with pytest.raises(KeyError):
        c.pop("x")
    with pytest.raises(KeyError):
        c.popitem()


@kinds
def test_single_insert_roundtrip(kind):
    """D1 × D8：一次写入后，所有读视图必须一致。"""
    c = make(kind, 3)
    c["a"] = 1
    assert c["a"] == 1
    assert c.get("a") == 1
    assert "a" in c
    assert len(c) == 1
    assert c.currsize == 1  # 默认 getsizeof 每条目算 1
    assert list(c) == ["a"]
    assert list(c.keys()) == ["a"]
    assert list(c.values()) == [1]
    assert list(c.items()) == [("a", 1)]
    assert c == {"a": 1}
    assert bool(c) is True


@kinds
def test_mapping_views_and_update_and_equality(kind):
    """D8：update() / 视图 / == 必须与逐条写入等价。"""
    c = make(kind, 10)
    c.update({"a": 1, "b": 2})
    c.update([("c", 3)])
    assert snapshot(c) == {"a": 1, "b": 2, "c": 3}
    assert len(c) == 3
    assert c.currsize == 3
    assert set(c.keys()) == {"a", "b", "c"}
    assert sorted(c.values()) == [1, 2, 3]
    assert set(c.items()) == {("a", 1), ("b", 2), ("c", 3)}
    assert c == {"a": 1, "b": 2, "c": 3}
    assert c != {"a": 1, "b": 2}


@kinds
def test_delete_semantics(kind):
    """D8 × D4：删除后条目消失、currsize 回退、重复删除报 KeyError。"""
    c = make(kind, 4)
    c["a"] = 1
    c["b"] = 2
    del c["a"]
    assert "a" not in c
    assert len(c) == 1
    assert c.currsize == 1
    assert snapshot(c) == {"b": 2}
    with pytest.raises(KeyError):
        del c["a"]
    del c["b"]
    assert len(c) == 0
    assert c.currsize == 0


@kinds
def test_pop_semantics(kind):
    """D8：pop 返回值并移除；缺失键按 default/KeyError 两种约定。"""
    c = make(kind, 4)
    c["a"] = 1
    assert c.pop("a") == 1
    assert "a" not in c
    assert len(c) == 0
    assert c.currsize == 0
    assert c.pop("a", "dflt") == "dflt"
    with pytest.raises(KeyError):
        c.pop("a")


@kinds
def test_setdefault_new_key_inserts_pathA_and_existing_key_keeps_value_pathB(kind):
    """D8 × D4：setdefault 对新键 = 插入；对已存在键 = 只读不覆盖（路径 B）。"""
    c = make(kind, 4)
    assert c.setdefault("a", 1) == 1        # 新键：插入并返回默认值
    assert c["a"] == 1
    assert len(c) == 1
    assert c.setdefault("a", 999) == 1      # 已存在键（路径 B）：返回旧值
    assert c["a"] == 1                      # 且不得被覆盖
    assert len(c) == 1
    assert c.currsize == 1


@kinds
def test_none_value_is_distinguishable_from_missing(kind):
    """D5 特殊值 None × D8：None 值不得与"键不存在"混淆。"""
    c = make(kind, 4)
    c["a"] = None
    assert "a" in c
    assert len(c) == 1
    assert c["a"] is None
    assert c.get("a", SENTINEL) is None      # 命中，返回 None 而非 default
    assert c.get("missing", SENTINEL) is SENTINEL
    assert c == {"a": None}
    assert c.pop("a", SENTINEL) is None
    assert len(c) == 0


@kinds
def test_none_key_is_a_valid_key(kind):
    """D4 特殊键：None 是合法的可哈希键。"""
    c = make(kind, 4)
    c[None] = "v"
    assert None in c
    assert c[None] == "v"
    assert list(c) == [None]
    del c[None]
    assert None not in c


@kinds
def test_unhashable_key_raises_typeerror(kind):
    """D4 特殊键：不可哈希键必须抛 TypeError，且不得留下残留状态。"""
    c = make(kind, 4)
    with pytest.raises(TypeError):
        c[["a"]] = 1
    assert len(c) == 0
    assert c.currsize == 0
    with pytest.raises(TypeError):
        c[["a"]]


@kinds
def test_equal_keys_1_true_are_the_same_entry_pathB(kind):
    """D4 × D9（路径 B：已存在键由"相等对象"引入）：1 / 1.0 / True 是同一个键。"""
    c = make(kind, 4)
    c[1] = "int"
    c[1.0] = "float"      # 覆盖，不是新条目
    c[True] = "bool"      # 仍是同一个键
    assert len(c) == 1
    assert c.currsize == 1
    assert c[1] == "bool"
    assert c[1.0] == "bool"
    assert c[True] == "bool"


@kinds
def test_overwrite_existing_key_does_not_grow_cache_pathB(kind):
    """F9 路径 B：对已存在键再赋值 —— 走的是"更新"而非"插入"代码路径。"""
    c = make(kind, 4)
    c["a"] = 1
    c["a"] = 2
    c["a"] = 3
    assert c["a"] == 3
    assert len(c) == 1
    assert c.currsize == 1
    assert snapshot(c) == {"a": 3}


@kinds
def test_clear_then_reusable_pathB(kind):
    """F10 路径 B（由 clear 产生空容器）：clear 后容器必须能正常继续使用。"""
    c = make(kind, 3)
    for k in "abc":
        c[k] = k.upper()
    c.clear()
    assert len(c) == 0
    assert c.currsize == 0
    assert list(c) == []
    assert c == {}
    with pytest.raises(KeyError):
        c.popitem()
    # 重新灌满，容量与内容都必须正确
    for k in "xyz":
        c[k] = k.upper()
    assert len(c) == 3
    assert c.currsize == 3
    assert snapshot(c) == {"x": "X", "y": "Y", "z": "Z"}
    assert c.maxsize == 3


# =============================================================================
# 组 1：maxsize 的特殊取值  (D2 × D1 × D3)
# =============================================================================


@kinds
def test_maxsize_zero_rejects_unit_sized_value(kind):
    """★ D2=0 × D3=默认：size 1 > maxsize 0 → ValueError，且缓存保持为空。"""
    c = make(kind, 0)
    assert c.maxsize == 0
    with pytest.raises(ValueError):
        c["a"] = 1
    assert len(c) == 0
    assert c.currsize == 0
    assert "a" not in c


@kinds
def test_maxsize_zero_with_zero_sized_values_accepts_everything(kind):
    """★★ 特殊×特殊：零容量 × 零尺寸条目 —— size 0 不超过 maxsize 0，应可插入。"""
    c = make(kind, 0, getsizeof=lambda v: 0)
    c["a"] = 1
    c["b"] = 2
    c["c"] = 3
    assert len(c) == 3
    assert c.currsize == 0
    assert snapshot(c) == {"a": 1, "b": 2, "c": 3}
    assert c.currsize <= c.maxsize


@kinds
def test_maxsize_zero_setdefault_raises_valueerror(kind):
    """★ D2=0 × D8=setdefault：setdefault 必须真的尝试插入，因此抛 ValueError。"""
    c = make(kind, 0)
    with pytest.raises(ValueError):
        c.setdefault("a", 1)
    assert len(c) == 0
    assert "a" not in c


@kinds
def test_full_by_construction_maxsize_one_pathA(kind):
    """F2 路径 A：由构造参数 maxsize=1 直接产生"满"这一特征。"""
    c = make(kind, 1)
    c["a"] = 1
    assert len(c) == 1
    c["b"] = 2
    assert len(c) == 1
    assert c.currsize == 1
    assert c.currsize <= c.maxsize
    assert snapshot(c) == {"b": 2}  # 只剩最后写入的那个（唯一能满足容量的结果）


@kinds
def test_full_by_insertions_pathB(kind):
    """F2 路径 B：maxsize=3，靠后续插入把它填满并触发淘汰。"""
    c = make(kind, 3)
    for i in range(10):
        c["k%d" % i] = i
        assert len(c) <= 3
        assert c.currsize <= c.maxsize
    assert len(c) == 3
    assert c.currsize == 3
    assert "k9" in c              # 刚写入的必须在
    assert c["k9"] == 9
    for k in list(c):             # 不得残留幽灵键
        assert c[k] == int(k[1:])


@kinds
def test_maxsize_one_overwrite_same_key_pathB(kind):
    """★ D2=1 × F9 路径 B：容量为 1 时反复写同一个键不应把自己淘汰掉。"""
    c = make(kind, 1)
    for i in range(5):
        c["a"] = i
        assert len(c) == 1
        assert c["a"] == i
        assert c.currsize == 1


@kinds
def test_large_maxsize_never_evicts(kind):
    """D2=大：容量充足时不得发生任何淘汰。"""
    c = make(kind, 1000)
    for i in range(200):
        c[i] = i * i
    assert len(c) == 200
    assert c.currsize == 200
    for i in range(200):
        assert c[i] == i * i


# =============================================================================
# 组 2：getsizeof / 条目尺寸 —— 路径 A vs 路径 B  (F1, F3, F4, F8)
# =============================================================================


def test_default_getsizeof_is_one_for_any_value():
    """D3 默认：文档"Return the size of a cache element's value"，默认每条目算 1。"""
    assert Cache.getsizeof(object()) == 1
    assert Cache.getsizeof("a very long string") == 1
    assert Cache.getsizeof(None) == 1
    c = Cache(10)
    assert c.getsizeof([1, 2, 3]) == 1


@kinds
def test_size_from_constant_getsizeof_param_pathA(kind):
    """F1 路径 A：尺寸由构造参数决定（与数据无关的常量函数）。"""
    c = make(kind, 6, getsizeof=lambda v: 2)
    assert c.getsizeof("whatever") == 2
    c["a"] = "x"
    assert c.currsize == 2
    c["b"] = "yyyyyy"
    assert c.currsize == 4      # 与值长度无关，仍是 2
    c["c"] = None
    assert c.currsize == 6
    assert len(c) == 3
    c["d"] = "z"                # 已满，必须淘汰一条才装得下
    assert c.currsize == 6
    assert len(c) == 3
    assert c.currsize <= c.maxsize
    assert c["d"] == "z"


@kinds
def test_size_from_data_len_pathB(kind):
    """F1 路径 B：尺寸由写入的数据自身决定（getsizeof=len）。"""
    c = make(kind, 6, getsizeof=len)
    c["a"] = "x"        # 1
    c["b"] = "yy"       # 2
    assert c.currsize == 3
    assert len(c) == 2
    c["c"] = "zzz"      # 3 -> 恰好占满
    assert c.currsize == 6
    assert len(c) == 3
    assert c.currsize <= c.maxsize
    # 各条目尺寸之和必须等于 currsize
    assert c.currsize == sum(len(v) for v in snapshot(c).values())


def test_size_from_subclass_override_pathB():
    """F1 路径 B'：getsizeof 由子类覆写（类属性查找路径），而非构造参数传入。"""

    class LenLRUCache(LRUCache):
        def getsizeof(self, value):
            return len(value)

    c = LenLRUCache(5)
    assert c.getsizeof("abcd") == 4
    c["a"] = "ab"
    c["b"] = "cde"
    assert c.currsize == 5
    assert len(c) == 2
    c["c"] = "f"            # 需要腾出 1 -> 淘汰最久未用的 "a"
    assert "a" not in c
    assert snapshot(c) == {"b": "cde", "c": "f"}
    assert c.currsize == 4


def test_size_from_subclass_override_on_base_cache_pathB():
    """F1 路径 B'：直接子类化 Cache 覆写 getsizeof（文档给出的扩展点）。"""

    class LenCache(Cache):
        def getsizeof(self, value):
            return len(value)

    c = LenCache(4)
    c["a"] = "abc"
    assert c.currsize == 3
    assert c.getsizeof("abcd") == 4
    del c["a"]
    assert c.currsize == 0


@kinds
def test_oversized_on_first_insert_pathA(kind):
    """F3 路径 A：构造参数使得任何值的 size 都 > maxsize → 首次写入即 ValueError。"""
    c = make(kind, 3, getsizeof=lambda v: 10)
    with pytest.raises(ValueError):
        c["a"] = 1
    assert len(c) == 0
    assert c.currsize == 0
    assert "a" not in c


@kinds
def test_oversized_on_overwrite_existing_key_pathB(kind):
    """★ F3 路径 B：先写入合法值，再把同一个已存在的键改写为过大的值。

    契约：写入失败（ValueError）不得破坏容器 —— 原条目及 currsize 必须完好。
    """
    c = make(kind, 3, getsizeof=len)
    c["a"] = "xx"
    assert c.currsize == 2
    with pytest.raises(ValueError):
        c["a"] = "xxxx"          # size 4 > maxsize 3
    assert "a" in c
    assert c["a"] == "xx"        # 旧值必须还在
    assert len(c) == 1
    assert c.currsize == 2       # 记账不得被污染
    c["b"] = "y"                 # 容器仍可正常使用
    assert c.currsize == 3
    assert snapshot(c) == {"a": "xx", "b": "y"}


@kinds
def test_size_exactly_maxsize_then_overwrite_same_size_pathB(kind):
    """★★ 特殊×特殊：条目 size 恰好 == maxsize × 对同键再赋同尺寸值。

    契约：更新自身不应先把自己淘汰掉（更不能因此变成空容器）。
    """
    c = make(kind, 3, getsizeof=len)
    c["a"] = "xxx"
    assert c.currsize == 3
    assert len(c) == 1
    c["a"] = "yyy"                # 同尺寸覆盖
    assert len(c) == 1
    assert c["a"] == "yyy"
    assert c.currsize == 3


@kinds
def test_currsize_grows_on_overwrite_with_larger_value_pathB(kind):
    """★ F4 路径 B：对已存在键写更大的值，必须重新记账并腾出空间。"""
    c = make(kind, 4, getsizeof=len)
    c["a"] = "x"
    c["b"] = "y"
    assert c.currsize == 2
    c["a"] = "xxxx"               # 由 1 变成 4，总量必须 <= 4
    assert c["a"] == "xxxx"
    assert c.currsize == 4
    assert c.currsize <= c.maxsize
    assert len(c) == 1            # 4 已占满，"b" 必须被淘汰
    assert "b" not in c


@kinds
def test_currsize_shrinks_on_overwrite_with_smaller_value_pathB(kind):
    """★ F4 路径 B：对已存在键写更小的值，currsize 必须回落（否则空间会漏掉）。"""
    c = make(kind, 4, getsizeof=len)
    c["a"] = "xxx"
    assert c.currsize == 3
    c["a"] = "x"
    assert c.currsize == 1
    c["b"] = "yyy"                # 1 + 3 = 4，正好装得下，不应触发淘汰
    assert len(c) == 2
    assert c.currsize == 4
    assert snapshot(c) == {"a": "x", "b": "yyy"}


@kinds
def test_zero_sized_value_mixed_with_normal_sizes(kind):
    """★ D3 零尺寸 × 正常尺寸混合：空值不占空间，也不该被记成 1。"""
    c = make(kind, 2, getsizeof=len)
    c["e1"] = ""
    c["e2"] = ""
    assert c.currsize == 0
    assert len(c) == 2
    c["a"] = "xx"
    assert c.currsize == 2
    assert c["a"] == "xx"
    assert len(c) == 3            # 0 + 2 <= 2，无需淘汰任何条目
    assert c.currsize <= c.maxsize


@kinds
def test_size_recorded_at_write_time_not_reread_pathB(kind):
    """★ F8 路径 B（写入之后属性才变化）：值被 mutate 后，记账必须仍能自洽。

    契约：删除全部条目后 currsize 必须回到 0（尺寸应按写入时记录，
    而不是删除时对已变形的值重新计算）。
    """
    c = make(kind, 10, getsizeof=len)
    v = ["a"]
    c["k"] = v
    assert c.currsize == 1
    v.append("b")                 # 写入之后值变大了
    v.append("c")
    assert len(c["k"]) == 3
    del c["k"]
    assert c.currsize == 0
    assert len(c) == 0


@kinds
def test_getsizeof_depending_on_external_state_pathB(kind):
    """★ F8 路径 B：getsizeof 的结果在写入之后被外部状态改变。"""
    state = {"size": 1}
    c = make(kind, 10, getsizeof=lambda v: state["size"])
    c["a"] = "v"
    assert c.currsize == 1
    state["size"] = 5             # 写入后尺寸函数的行为变了
    del c["a"]
    assert c.currsize == 0        # 仍必须精确回到 0
    assert len(c) == 0


@kinds
def test_size_based_eviction_removes_multiple_items(kind):
    """★ D9：一次插入按 size 淘汰多条（不是只淘汰一条）。"""
    c = make(kind, 6, getsizeof=len)
    c["a"] = "xx"
    c["b"] = "yy"
    c["c"] = "zz"
    assert c.currsize == 6
    assert len(c) == 3
    c["big"] = "wwwww"            # size 5，必须腾出至少 5 -> 至少淘汰 2 条
    assert c["big"] == "wwwww"
    assert c.currsize <= 6
    assert len(c) <= 2
    assert c.currsize == sum(len(v) for v in snapshot(c).values())


# =============================================================================
# 组 3：popitem 的通用契约  (D1 × D8 × D9)
# =============================================================================


@kinds
def test_popitem_removes_a_live_pair_and_updates_accounting(kind):
    """D8：popitem 返回的必须是当前真实存在的 (key, value)，并正确扣减记账。"""
    c = make(kind, 3, getsizeof=len)
    c["a"] = "x"
    c["b"] = "yy"
    c["c"] = ""
    before = snapshot(c)
    before_size = c.currsize
    k, v = c.popitem()
    assert k in before
    assert v == before[k]          # 不得返回陈旧的值
    assert k not in c
    assert len(c) == 2
    assert c.currsize == before_size - len(v)
    assert c.currsize == sum(len(x) for x in snapshot(c).values())


@kinds
def test_popitem_drains_cache_without_repeats(kind):
    """D8 × F10：连续 popitem 应把容器排空且不重复返回同一个键。"""
    c = make(kind, 5)
    expected = {"a": 1, "b": 2, "c": 3, "d": 4}
    for k, v in expected.items():
        c[k] = v
    got = {}
    for _ in range(4):
        k, v = c.popitem()
        assert k not in got
        got[k] = v
    assert got == expected
    assert len(c) == 0
    assert c.currsize == 0
    with pytest.raises(KeyError):
        c.popitem()


@kinds
def test_popitem_after_overwrite_returns_current_value_pathB(kind):
    """F9 路径 B × D8：覆盖写之后 popitem 不得返回被覆盖掉的旧值。"""
    c = make(kind, 2)
    c["a"] = "old"
    c["b"] = "b"
    c["a"] = "new"
    pairs = dict([c.popitem(), c.popitem()])
    assert pairs == {"a": "new", "b": "b"}


# =============================================================================
# 组 4：各淘汰策略的专属语义  (D1 × D9，同一操作序列 × 不同容器 = 不同结果)
# =============================================================================


def test_fifo_popitem_returns_first_inserted_pathA():
    """FIFO 文档："Remove and return the (key, value) pair first inserted"。
    F7 路径 A：顺序完全由插入建立。"""
    c = FIFOCache(3)
    c["a"] = 1
    c["b"] = 2
    c["c"] = 3
    assert c.popitem() == ("a", 1)
    assert c.popitem() == ("b", 2)
    assert c.popitem() == ("c", 3)


def test_fifo_eviction_ignores_reads_pathB():
    """★ D1 对比：FIFO 与 LRU 的分水岭 —— 读操作不得改变 FIFO 淘汰顺序。"""
    c = FIFOCache(2)
    c["a"] = 1
    c["b"] = 2
    assert c["a"] == 1        # 读 a（路径 B：后续操作）
    assert c["a"] == 1
    c["c"] = 3                # 满了，按"最先插入"淘汰 a
    assert "a" not in c
    assert snapshot(c) == {"b": 2, "c": 3}


def test_fifo_overwrite_keeps_entry_consistent_pathB():
    """F9 路径 B × FIFO：对已存在键再赋值后，容器内容与记账仍须自洽。

    注：SPEC 未定义"再赋值是否重置插入时刻"，故此处只断言无歧义的部分：
    值被更新、条目数不变、popitem 能把两条都取出且值正确。
    """
    c = FIFOCache(2)
    c["a"] = 1
    c["b"] = 2
    c["a"] = 11
    assert len(c) == 2
    assert c.currsize == 2
    assert c["a"] == 11
    pairs = dict([c.popitem(), c.popitem()])
    assert pairs == {"a": 11, "b": 2}
    assert len(c) == 0


def test_fifo_order_restarts_after_clear_pathB():
    """★ F10 路径 B：clear 之后 FIFO 的内部顺序结构必须一并重置。"""
    c = FIFOCache(2)
    c["a"] = 1
    c["b"] = 2
    c.clear()
    c["x"] = 10
    c["y"] = 20
    assert c.popitem() == ("x", 10)


def test_fifo_reinsert_after_eviction_pathB():
    """F9 路径 B：被淘汰的键重新插入后，应作为"新插入"参与排序。"""
    c = FIFOCache(2)
    c["a"] = 1
    c["b"] = 2
    c["c"] = 3          # 淘汰 a，剩 b, c
    assert "a" not in c
    c["a"] = 4          # a 重新插入，淘汰 b
    assert "b" not in c
    assert snapshot(c) == {"c": 3, "a": 4}
    assert c.popitem() == ("c", 3)


def test_lru_popitem_returns_least_recently_used_pathA():
    """LRU 文档："least recently used"。F7 路径 A：仅由插入顺序决定。"""
    c = LRUCache(3)
    c["a"] = 1
    c["b"] = 2
    c["c"] = 3
    assert c.popitem() == ("a", 1)
    assert c.popitem() == ("b", 2)


def test_lru_getitem_refreshes_recency_pathB():
    """F7 路径 B：__getitem__ 是一次"使用"，必须刷新近期性。"""
    c = LRUCache(2)
    c["a"] = 1
    c["b"] = 2
    assert c["a"] == 1        # a 变成最近使用
    c["c"] = 3                # 淘汰最久未用的 b
    assert "b" not in c
    assert snapshot(c) == {"a": 1, "c": 3}


def test_lru_get_refreshes_recency_pathB():
    """F7 路径 B：get() 同样是一次读取使用。"""
    c = LRUCache(2)
    c["a"] = 1
    c["b"] = 2
    assert c.get("a") == 1
    c["c"] = 3
    assert "b" not in c
    assert "a" in c


def test_lru_setdefault_on_existing_key_refreshes_recency_pathB():
    """F7 路径 B：setdefault 命中已有键 = 读取该值 = 一次使用。"""
    c = LRUCache(2)
    c["a"] = 1
    c["b"] = 2
    assert c.setdefault("a", 999) == 1
    c["c"] = 3
    assert "b" not in c
    assert snapshot(c) == {"a": 1, "c": 3}


def test_lru_overwrite_refreshes_recency_pathB():
    """★ F7 路径 B：对已存在键写入也是一次"使用"，应刷新近期性。"""
    c = LRUCache(2)
    c["a"] = 1
    c["b"] = 2
    c["a"] = 11               # 写 a
    c["c"] = 3                # 淘汰最久未用的 b
    assert "b" not in c
    assert snapshot(c) == {"a": 11, "c": 3}


def test_lru_contains_does_not_count_as_use():
    """D8 × LRU：成员测试不读取值，按 LRU 常规语义不算"使用"。"""
    c = LRUCache(2)
    c["a"] = 1
    c["b"] = 2
    assert ("a" in c) is True
    c["c"] = 3
    assert "a" not in c       # a 仍是最久未用者
    assert snapshot(c) == {"b": 2, "c": 3}


def test_lru_iteration_does_not_count_as_use():
    """D8 × LRU：遍历键不涉及取值，不应改变淘汰顺序。"""
    c = LRUCache(2)
    c["a"] = 1
    c["b"] = 2
    assert set(c) == {"a", "b"}
    c["c"] = 3
    assert "a" not in c


def test_lru_size_based_eviction_frees_least_recently_used_first():
    """★ D3 × D9 × LRU：按 size 淘汰时也必须从最久未用者开始。"""
    c = LRUCache(6, getsizeof=len)
    c["a"] = "aa"
    c["b"] = "bb"
    c["c"] = "cc"
    assert c["a"] == "aa"          # a 最近使用；顺序 b < c < a
    c["d"] = "dddd"                # 需要 4，先淘汰 b 再淘汰 c
    assert "b" not in c
    assert "c" not in c
    assert snapshot(c) == {"a": "aa", "d": "dddd"}
    assert c.currsize == 6


def test_lru_order_restarts_after_clear_pathB():
    """F10 路径 B：clear 后 LRU 顺序结构必须重置。"""
    c = LRUCache(2)
    c["a"] = 1
    c["b"] = 2
    assert c["a"] == 1
    c.clear()
    c["x"] = 10
    c["y"] = 20
    assert c.popitem() == ("x", 10)


def test_lfu_popitem_by_read_frequency_pathA():
    """LFU 文档："least frequently used"。F7 路径 A + 路径 B（读频度）。"""
    c = LFUCache(3)
    c["a"] = 1
    c["b"] = 2
    c["c"] = 3
    for _ in range(3):
        assert c["a"] == 1
    assert c["b"] == 2
    # c 从未被读取 -> 最不常用
    assert c.popitem() == ("c", 3)
    assert c.popitem() == ("b", 2)
    assert c.popitem() == ("a", 1)


def test_lfu_eviction_drops_least_frequently_used_pathB():
    """F7 路径 B：读取次数由后续操作决定谁被淘汰。"""
    c = LFUCache(2)
    c["a"] = 1
    c["b"] = 2
    assert c["a"] == 1
    assert c["a"] == 1
    assert c["b"] == 2
    c["c"] = 3                # b 的读取次数少于 a -> 淘汰 b
    assert "b" not in c
    assert snapshot(c) == {"a": 1, "c": 3}


def test_lfu_get_counts_as_use_pathB():
    """F7 路径 B：get() 也是一次使用，应计入频度。"""
    c = LFUCache(2)
    c["a"] = 1
    c["b"] = 2
    for _ in range(3):
        assert c.get("a") == 1
    c["c"] = 3
    assert "b" not in c
    assert "a" in c


def test_lfu_overwrite_keeps_frequency_pathB():
    """★ F7 路径 B：对已存在键再赋值不得把它的使用频度清零。"""
    c = LFUCache(2)
    c["a"] = 1
    c["b"] = 2
    for _ in range(3):
        assert c["a"] == 1
    c["a"] = 11               # 覆盖写（路径 B）
    c["c"] = 3                # 仍应淘汰从未被读过的 b
    assert "b" not in c
    assert snapshot(c) == {"a": 11, "c": 3}


def test_lfu_counter_reset_after_eviction_pathB():
    """★ F9 路径 B：键被删除后重新插入，旧的频度计数不得残留。"""
    c = LFUCache(2)
    c["a"] = 1
    for _ in range(10):
        assert c["a"] == 1    # a 积累了很高的频度
    del c["a"]
    c["b"] = 2
    c["a"] = 100              # a 重新插入 -> 频度应从头计
    assert c["b"] == 2        # b 被读过一次，a 一次也没有
    c["c"] = 3
    assert "a" not in c       # 应淘汰重新插入且未被使用的 a
    assert snapshot(c) == {"b": 2, "c": 3}


def test_lfu_frequency_resets_after_clear_pathB():
    """F10 路径 B：clear 之后频度统计必须一并清空。"""
    c = LFUCache(2)
    c["a"] = 1
    for _ in range(5):
        assert c["a"] == 1
    c.clear()
    c["a"] = 1
    c["b"] = 2
    assert c["b"] == 2        # 现在 b 比 a 常用
    c["z"] = 26
    assert "a" not in c
    assert snapshot(c) == {"b": 2, "z": 26}


def test_rr_choice_property_and_custom_choice_pathA():
    """D10 路径 A：choice 由构造参数注入，并被用于淘汰。"""
    picker = RecordingChoice(pick=lambda seq: sorted(seq)[0])
    c = RRCache(2, choice=picker)
    assert c.choice is picker
    c["b"] = 2
    c["c"] = 3
    assert picker.calls == []          # 未满，不应调用 choice
    c["a"] = 1                         # 满了，choice 从当前键中挑 -> "b"
    assert len(picker.calls) == 1
    assert sorted(picker.calls[0]) == ["b", "c"]   # 收到的必须是当前键集合
    assert "b" not in c
    assert snapshot(c) == {"c": 3, "a": 1}


def test_rr_popitem_uses_choice():
    """D10 × D8：popitem 文档为"随机一对"，注入确定性 choice 后结果可断言。"""
    c = RRCache(3, choice=lambda seq: sorted(seq)[-1])
    c["a"] = 1
    c["b"] = 2
    c["c"] = 3
    assert c.popitem() == ("c", 3)
    assert c.popitem() == ("b", 2)
    assert len(c) == 1


def test_rr_default_choice_still_respects_capacity():
    """D10 路径 A（默认参数 random.choice）：随机策略下容量约束仍须成立。"""
    c = RRCache(3)
    for i in range(50):
        c[i] = i
        assert len(c) <= 3
        assert c.currsize <= c.maxsize
    assert len(c) == 3
    for k in list(c):
        assert c[k] == k


# =============================================================================
# 组 5：TTLCache —— 时间特征的路径 A / 路径 B  (D6 × D7 × D4 × D8)
# =============================================================================


def test_ttl_property_and_basic_liveness():
    """D7：ttl 属性回读；未到期条目正常可见。"""
    clock = Clock()
    c = TTLCache(4, 10, timer=clock)
    assert c.ttl == 10
    assert c.maxsize == 4
    c["a"] = 1
    clock.advance(9)
    assert c["a"] == 1
    assert "a" in c
    assert len(c) == 1


def test_ttl_expires_after_clock_advance_pathB():
    """★ F5 路径 B：构造参数正常，条目写入之后才因时间推进而过期。"""
    clock = Clock()
    c = TTLCache(4, 10, timer=clock)
    c["a"] = 1
    clock.advance(11)
    assert "a" not in c
    assert len(c) == 0
    assert list(c) == []
    assert c.get("a") is None
    assert c.get("a", SENTINEL) is SENTINEL
    assert c == {}
    with pytest.raises(KeyError):
        c["a"]


def test_ttl_zero_everything_expires_immediately_pathA():
    """★★ F5 路径 A（特殊参数 ttl=0）× 任意写入：条目立刻不可见。"""
    clock = Clock()
    c = TTLCache(2, 0, timer=clock)
    assert c.ttl == 0
    c["a"] = 1
    assert "a" not in c
    assert len(c) == 0
    assert c.get("a", SENTINEL) is SENTINEL
    with pytest.raises(KeyError):
        c["a"]
    with pytest.raises(KeyError):
        c.popitem()
    for i in range(10):          # 反复写入也不应堆积
        c["k%d" % i] = i
    assert len(c) == 0
    assert list(c) == []


def test_ttl_zero_repeated_overwrite_of_same_key_pathB():
    """★★ 特殊×特殊：ttl=0 × 对同一个键反复覆盖写（路径 B）。"""
    clock = Clock()
    c = TTLCache(1, 0, timer=clock)
    for i in range(5):
        c["a"] = i
        assert "a" not in c
        assert len(c) == 0
    assert c.currsize <= c.maxsize


def test_ttl_boundary_exactly_at_expiry_time():
    """★ D6 边界：条目在 [t0, t0+ttl) 内有效，t0+ttl 时刻起过期。"""
    clock = Clock()
    c = TTLCache(4, 10, timer=clock)
    c["a"] = 1
    clock.advance(9.999)
    assert c["a"] == 1            # 仍在有效期内
    clock.advance(0.001)          # 正好 t0 + ttl
    assert "a" not in c
    assert len(c) == 0


def test_ttl_per_item_expiry_by_insertion_time_pathB():
    """F6 路径 B：同一个 ttl，因写入时刻不同而产生不同的过期时刻。"""
    clock = Clock()
    c = TTLCache(4, 10, timer=clock)
    c["a"] = 1
    clock.advance(5)
    c["b"] = 2
    clock.advance(6)              # t=11：a 已过期（10），b 未过期（15）
    assert "a" not in c
    assert "b" in c
    assert len(c) == 1
    assert list(c) == ["b"]
    assert c == {"b": 2}
    assert snapshot(c) == {"b": 2}


def test_ttl_overwrite_refreshes_expiry_pathB():
    """★ F9+F5 路径 B：对已存在键再赋值，寿命应从新的写入时刻重新计算。"""
    clock = Clock()
    c = TTLCache(4, 10, timer=clock)
    c["a"] = 1
    clock.advance(8)
    c["a"] = 2                    # 新的过期时刻 = 18
    clock.advance(5)              # t=13，若未刷新则早已过期
    assert "a" in c
    assert c["a"] == 2
    clock.advance(6)              # t=19 > 18
    assert "a" not in c


def test_ttl_read_does_not_refresh_expiry():
    """D6 × D8：TTL 是"存活时间"而非"空闲超时"，读取不得续命。"""
    clock = Clock()
    c = TTLCache(4, 10, timer=clock)
    c["a"] = 1
    clock.advance(8)
    assert c["a"] == 1            # 读一次
    clock.advance(3)              # t=11 > 10
    assert "a" not in c


def test_ttl_expired_key_pop_and_delete_and_setdefault_pathB():
    """★ D6 × D4/D8：过期键在 pop / del / setdefault 眼里等同于"不存在"。"""
    clock = Clock()
    c = TTLCache(4, 10, timer=clock)
    c["a"] = 1
    c["b"] = 2
    clock.advance(11)
    assert c.pop("a", SENTINEL) is SENTINEL
    with pytest.raises(KeyError):
        c.pop("b")
    with pytest.raises(KeyError):
        del c["a"]
    assert c.setdefault("a", 99) == 99     # 必须插入新值，而不是返回陈旧值
    assert c["a"] == 99
    assert len(c) == 1


def test_ttl_expire_returns_expired_pairs_pathB():
    """D8：expire() 文档 —— 移除过期条目并返回过期的 (key, value) 序列。"""
    clock = Clock()
    c = TTLCache(4, 10, timer=clock)
    c["a"] = 1
    clock.advance(5)
    c["b"] = 2
    clock.advance(6)                        # t=11
    expired = list(c.expire())
    assert expired == [("a", 1)]
    assert len(c) == 1
    assert snapshot(c) == {"b": 2}
    assert list(c.expire()) == []           # 幂等：第二次没有新的过期条目
    assert len(c) == 1


def test_ttl_expire_with_explicit_time_argument_pathA():
    """D8 路径 A（由参数引入"当前时间"）：expire(time) 用给定时刻判定过期。"""
    clock = Clock()
    c = TTLCache(4, 10, timer=clock)
    c["a"] = 1
    clock.advance(2)
    c["b"] = 2
    assert list(c.expire(5)) == []          # 5 < 10，都没过期
    assert len(c) == 2
    expired = list(c.expire(11))            # a 过期于 10，b 过期于 12
    assert expired == [("a", 1)]
    assert len(c) == 1
    assert "b" in c
    assert clock.now == 2                   # expire(time) 不应触碰真实 timer


def test_ttl_currsize_after_expire_pathB():
    """★ F4 路径 B：过期回收后 currsize 必须与剩余条目尺寸之和一致。"""
    clock = Clock()
    c = TTLCache(10, 10, timer=clock, getsizeof=len)
    c["a"] = "xx"
    clock.advance(5)
    c["b"] = "yyy"
    assert c.currsize == 5
    clock.advance(6)
    assert list(c.expire()) == [("a", "xx")]
    assert c.currsize == 3
    assert c.currsize == sum(len(v) for v in snapshot(c).values())


def test_ttl_expired_entries_free_space_for_new_items_pathB():
    """★ D6 × D9 路径 B：整缓存过期后再插入 —— 过期回收应腾出空间。"""
    clock = Clock()
    c = TTLCache(2, 10, timer=clock)
    c["a"] = 1
    c["b"] = 2
    assert len(c) == 2
    clock.advance(11)
    c["c"] = 3
    assert len(c) == 1
    assert c.currsize == 1
    assert snapshot(c) == {"c": 3}
    c["d"] = 4
    assert len(c) == 2
    assert snapshot(c) == {"c": 3, "d": 4}


def test_ttl_popitem_skips_expired_items_pathB():
    """★ D6 × D8：popitem 文档 —— "最久未用且尚未过期"的那一对。"""
    clock = Clock()
    c = TTLCache(4, 10, timer=clock)
    c["a"] = 1
    clock.advance(5)
    c["b"] = 2
    clock.advance(6)                # t=11，a 已过期
    assert c.popitem() == ("b", 2)  # 不得返回已过期的 a
    assert len(c) == 0


def test_ttl_popitem_when_all_expired_raises_pathB():
    """★ F10 路径 B：全部过期 == 空容器，popitem 必须 KeyError。"""
    clock = Clock()
    c = TTLCache(4, 10, timer=clock)
    c["a"] = 1
    c["b"] = 2
    clock.advance(11)
    with pytest.raises(KeyError):
        c.popitem()
    assert len(c) == 0


def test_ttl_is_lru_bounded_by_maxsize():
    """D1 文档："LRU Cache implementation with per-item TTL" —— 容量维度按 LRU。"""
    clock = Clock()
    c = TTLCache(2, NEVER, timer=clock)
    c["a"] = 1
    c["b"] = 2
    assert c["a"] == 1              # a 最近使用
    c["c"] = 3
    assert "b" not in c
    assert snapshot(c) == {"a": 1, "c": 3}


def test_ttl_maxsize_one_with_expiry():
    """★ D2=1 × D6：容量 1 与过期两种特殊情况叠加。"""
    clock = Clock()
    c = TTLCache(1, 10, timer=clock)
    c["a"] = 1
    clock.advance(11)
    assert len(c) == 0
    c["b"] = 2                      # 过期条目不应占着唯一的名额
    assert snapshot(c) == {"b": 2}
    assert c.currsize == 1


def test_ttl_clear_then_reusable_pathB():
    """F10 路径 B：clear 之后过期结构必须重置且容器可继续使用。"""
    clock = Clock()
    c = TTLCache(2, 10, timer=clock)
    c["a"] = 1
    c.clear()
    assert len(c) == 0
    assert c.currsize == 0
    clock.advance(100)
    c["b"] = 2
    assert snapshot(c) == {"b": 2}
    clock.advance(11)
    assert len(c) == 0


def test_ttl_len_iter_contains_agree_on_partial_expiry():
    """★ D6 × D8：部分过期时，len / iter / contains / items 必须口径一致。"""
    clock = Clock()
    c = TTLCache(10, 10, timer=clock)
    for i in range(5):
        c["k%d" % i] = i
        clock.advance(3)            # 写入时刻 0,3,6,9,12；过期时刻 10,13,16,19,22
    # 此时 t = 15：k0(10)、k1(13) 已过期
    assert clock.now == 15
    keys = list(c)
    assert set(keys) == {"k2", "k3", "k4"}
    assert len(c) == 3
    assert len(keys) == len(c)
    assert all(k in c for k in keys)
    assert dict(c.items()) == {"k2": 2, "k3": 3, "k4": 4}
    assert c == {"k2": 2, "k3": 3, "k4": 4}


# =============================================================================
# 组 6：TLRUCache —— ttu 的路径 A / 路径 B  (D7 × D6 × D4)
# =============================================================================


def test_tlru_ttu_property_and_call_signature_pathA():
    """D10/D7 路径 A：ttu 由构造参数注入，按 (key, value, now) 计算绝对过期时刻。"""
    calls = []
    clock = Clock()

    def ttu(key, value, now):
        calls.append((key, value, now))
        return now + 10

    c = TLRUCache(4, ttu, timer=clock)
    assert c.ttu is ttu
    c["a"] = 1
    assert calls == [("a", 1, 0.0)]
    clock.advance(4)
    c["b"] = 2
    assert calls[-1] == ("b", 2, 4.0)
    clock.advance(7)                 # t=11：a 过期（10），b 未过期（14）
    assert "a" not in c
    assert c["b"] == 2


def test_tlru_per_key_ttu_pathA():
    """★ F6 路径 A：不同的键由 ttu 参数给出不同寿命。"""
    clock = Clock()
    c = TLRUCache(4, lambda k, v, now: now + (2 if k == "short" else 100), timer=clock)
    c["short"] = 1
    c["long"] = 2
    clock.advance(3)
    assert "short" not in c
    assert c["long"] == 2
    assert len(c) == 1


def test_tlru_expires_by_insertion_time_difference_pathB():
    """F6 路径 B：同一个 ttu 函数，寿命差异完全由写入时刻（数据操作）产生。"""
    clock = Clock()
    c = TLRUCache(4, lambda k, v, now: now + 10, timer=clock)
    c["a"] = 1
    clock.advance(6)
    c["b"] = 2
    clock.advance(5)                 # t=11：a 过期（10），b 未过期（16）
    assert "a" not in c
    assert "b" in c
    assert len(c) == 1


def test_tlru_ttu_depends_on_value_pathB():
    """F6 路径 B：寿命由写入的数据自身决定（ttu 读取 value）。"""
    clock = Clock()
    c = TLRUCache(4, lambda k, v, now: now + v["ttl"], timer=clock)
    c["a"] = {"ttl": 2}
    c["b"] = {"ttl": 50}
    clock.advance(3)
    assert "a" not in c
    assert c["b"] == {"ttl": 50}


def test_tlru_ttu_in_the_past_item_never_visible_pathA():
    """★★ F5 路径 A（特殊参数）：ttu 返回过去时刻 —— 条目插入即过期。"""
    clock = Clock(100)
    c = TLRUCache(4, lambda k, v, now: now - 1, timer=clock)
    c["a"] = 1
    assert "a" not in c
    assert len(c) == 0
    assert c.get("a", SENTINEL) is SENTINEL
    with pytest.raises(KeyError):
        c["a"]
    with pytest.raises(KeyError):
        c.popitem()


def test_tlru_ttu_equal_now_is_already_expired_pathA():
    """★ D6 边界 × 路径 A：ttu 返回"当前时刻"即已到期（有效区间半开）。"""
    clock = Clock(50)
    c = TLRUCache(4, lambda k, v, now: now, timer=clock)
    c["a"] = 1
    assert "a" not in c
    assert len(c) == 0


def test_tlru_expired_insert_does_not_disturb_live_items_pathB():
    """★ 特殊×特殊：插入一个"生下来就过期"的条目，不应影响已有的存活条目。"""
    clock = Clock()
    lifetimes = {"live": 100, "dead": -1}
    c = TLRUCache(4, lambda k, v, now: now + lifetimes[k], timer=clock)
    c["live"] = 1
    c["dead"] = 2
    assert "dead" not in c
    assert c["live"] == 1
    assert len(c) == 1
    assert snapshot(c) == {"live": 1}


def test_tlru_overwrite_shortens_lifetime_pathB():
    """★★ F6 路径 B：对已存在键再赋值时 ttu 必须重算 —— 这次是把寿命改短。"""
    clock = Clock()
    lifetimes = {"a": 100}
    c = TLRUCache(4, lambda k, v, now: now + lifetimes[k], timer=clock)
    c["a"] = 1                       # 过期时刻 100
    clock.advance(10)
    lifetimes["a"] = 5
    c["a"] = 2                       # 重算后过期时刻应为 15
    assert c["a"] == 2
    clock.advance(6)                 # t=16 > 15
    assert "a" not in c
    assert len(c) == 0


def test_tlru_overwrite_extends_lifetime_pathB():
    """★ F6 路径 B：对已存在键再赋值把寿命改长。"""
    clock = Clock()
    lifetimes = {"a": 2}
    c = TLRUCache(4, lambda k, v, now: now + lifetimes[k], timer=clock)
    c["a"] = 1                       # 过期时刻 2
    clock.advance(1)
    lifetimes["a"] = 100
    c["a"] = 2                       # 重算后过期时刻应为 101
    clock.advance(5)                 # t=6，若沿用旧过期时刻则已消失
    assert "a" in c
    assert c["a"] == 2


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


def test_tlru_read_does_not_extend_lifetime():
    """D6 × D8：ttu 是"可用到某时刻"，读取不重算过期时刻。"""
    clock = Clock()
    c = TLRUCache(4, lambda k, v, now: now + 10, timer=clock)
    c["a"] = 1
    clock.advance(8)
    assert c["a"] == 1
    clock.advance(3)                 # t=11 > 10
    assert "a" not in c


def test_tlru_expire_returns_expired_pairs_and_updates_currsize_pathB():
    """D8 × F4 路径 B：expire() 返回过期对，并把 currsize 结清。"""
    clock = Clock()
    c = TLRUCache(10, lambda k, v, now: now + 10, timer=clock, getsizeof=len)
    c["a"] = "xx"
    clock.advance(4)
    c["b"] = "yyy"
    assert c.currsize == 5
    clock.advance(7)                 # t=11：a(10) 过期，b(14) 未过期
    expired = list(c.expire())
    assert expired == [("a", "xx")]
    assert c.currsize == 3
    assert snapshot(c) == {"b": "yyy"}
    assert list(c.expire()) == []


def test_tlru_expire_with_explicit_time_argument_pathA():
    """D8 路径 A：expire(time) 使用外部给定的时刻。"""
    clock = Clock()
    c = TLRUCache(10, lambda k, v, now: now + 10, timer=clock)
    c["a"] = 1
    clock.advance(3)
    c["b"] = 2
    assert list(c.expire(9)) == []
    assert len(c) == 2
    assert list(c.expire(11)) == [("a", 1)]
    assert len(c) == 1
    assert clock.now == 3


def test_tlru_popitem_skips_expired_items_pathB():
    """★ D6 × D8：popitem 文档 —— "最久未用且尚未过期"。"""
    clock = Clock()
    c = TLRUCache(4, lambda k, v, now: now + 10, timer=clock)
    c["a"] = 1
    clock.advance(6)
    c["b"] = 2
    clock.advance(5)                 # t=11：a 过期
    assert c.popitem() == ("b", 2)
    assert len(c) == 0


def test_tlru_is_lru_bounded_by_maxsize():
    """D1 文档："Time aware LRU" —— 容量维度仍按最近使用淘汰。"""
    clock = Clock()
    c = TLRUCache(2, never_ttu, timer=clock)
    c["a"] = 1
    c["b"] = 2
    assert c["a"] == 1
    c["c"] = 3
    assert "b" not in c
    assert snapshot(c) == {"a": 1, "c": 3}


def test_tlru_expired_entries_free_space_for_new_items_pathB():
    """★ D6 × D9 路径 B：过期条目不应长期占用容量。"""
    clock = Clock()
    c = TLRUCache(2, lambda k, v, now: now + 10, timer=clock)
    c["a"] = 1
    c["b"] = 2
    clock.advance(11)
    c["c"] = 3
    assert len(c) == 1
    assert c.currsize == 1
    c["d"] = 4
    assert snapshot(c) == {"c": 3, "d": 4}
    assert c.currsize == 2


# =============================================================================
# 组 7：时间语义容器的通用交叉（两种 timed 容器共用同一批断言）
# =============================================================================


@timed_kinds
def test_timed_expired_entry_is_invisible_to_every_read_operation_pathB(kind):
    """D1(timed) × D6 × D8 全交叉：过期条目对所有读操作一律不可见。"""
    clock = Clock()
    c = make_timed(kind, 4, 10, clock)
    c["a"] = 1
    c["b"] = 2
    clock.advance(11)
    assert len(c) == 0
    assert list(c) == []
    assert list(c.keys()) == []
    assert list(c.items()) == []
    assert list(c.values()) == []
    assert ("a" in c) is False
    assert c.get("a", SENTINEL) is SENTINEL
    assert c == {}
    assert not c
    with pytest.raises(KeyError):
        c["a"]


@timed_kinds
def test_timed_expiry_with_getsizeof_keeps_accounting_consistent_pathB(kind):
    """★ D3 × D6 交叉：带 getsizeof 时，过期回收后的记账必须自洽。"""
    clock = Clock()
    c = make_timed(kind, 12, 10, clock, getsizeof=len)
    c["a"] = "xxxx"
    clock.advance(6)
    c["b"] = "yy"
    clock.advance(5)                # t=11：a 过期
    list(c.expire())
    assert len(c) == 1
    assert c.currsize == 2
    assert c.currsize == sum(len(v) for v in snapshot(c).values())
    c["c"] = "zzzzz"
    assert c.currsize == 7
    assert c.currsize <= c.maxsize


@timed_kinds
def test_timed_zero_sized_expired_items_pathB(kind):
    """★★ 特殊×特殊：零尺寸条目 × 过期。"""
    clock = Clock()
    c = make_timed(kind, 0, 10, clock, getsizeof=lambda v: 0)
    c["a"] = 1
    assert len(c) == 1
    assert c.currsize == 0
    clock.advance(11)
    assert len(c) == 0
    assert c.currsize == 0


@timed_kinds
def test_timed_expire_removes_nothing_when_nothing_expired(kind):
    """D8：未到期时 expire() 必须返回空且不动内容。"""
    clock = Clock()
    c = make_timed(kind, 4, 10, clock)
    c["a"] = 1
    c["b"] = 2
    clock.advance(3)
    assert list(c.expire()) == []
    assert len(c) == 2
    assert snapshot(c) == {"a": 1, "b": 2}
    assert c.currsize == 2


@timed_kinds
def test_timed_reinsert_expired_key_pathB(kind):
    """★ F9+F5 路径 B：键过期后再插入，应成为一个全新的存活条目。"""
    clock = Clock()
    c = make_timed(kind, 4, 10, clock)
    c["a"] = 1
    clock.advance(11)
    assert "a" not in c
    c["a"] = 2
    assert c["a"] == 2
    assert len(c) == 1
    assert c.currsize == 1
    clock.advance(9)
    assert c["a"] == 2              # 新寿命从重新插入时刻起算
    clock.advance(2)
    assert "a" not in c


@timed_kinds
def test_timed_delete_live_item_then_expiry_of_others_pathB(kind):
    """D8 × D6：显式删除与到期回收混用后，容器状态仍须一致。"""
    clock = Clock()
    c = make_timed(kind, 4, 10, clock)
    c["a"] = 1
    c["b"] = 2
    c["c"] = 3
    del c["b"]
    assert len(c) == 2
    assert c.currsize == 2
    clock.advance(11)
    assert len(c) == 0
    assert list(c) == []
    assert sorted(list(c.expire())) == [("a", 1), ("c", 3)]  # 已删除的 b 不得再出现
    assert c.currsize == 0


@timed_kinds
def test_timed_never_expiring_behaves_like_plain_cache(kind):
    """D7 × D6：ttl/ttu 极大 + 时间大幅推进，条目不得丢失。"""
    clock = Clock()
    c = make_timed(kind, 5, NEVER, clock)
    for i in range(5):
        c[i] = i
    clock.advance(NEVER - 1)
    assert len(c) == 5
    assert snapshot(c) == {i: i for i in range(5)}
    assert list(c.expire()) == []


# =============================================================================
# 组 8：跨维度综合不变式（混合工作负载）
# =============================================================================


@kinds
def test_capacity_and_accounting_invariants_under_mixed_workload(kind):
    """D1 × D2 × D3 × D4 × D8 × D9 综合：随机但确定性的混合操作序列。

    不变式（任何时刻都必须成立）：
      1. currsize <= maxsize
      2. len(cache) == 可迭代键的个数，且每个键都能取到值
      3. currsize == 各条目 getsizeof(value) 之和
    """
    rng = random.Random(20240517)
    c = make(kind, 8, getsizeof=len)
    keys = ["k%d" % i for i in range(12)]
    values = ["", "a", "bb", "ccc", "dddd"]
    for step in range(300):
        op = rng.randrange(10)
        k = rng.choice(keys)
        if op < 5:
            c[k] = rng.choice(values)
        elif op == 5:
            c.get(k)
        elif op == 6:
            k in c
        elif op == 7:
            c.pop(k, None)
        elif op == 8:
            c.setdefault(k, "a")
        else:
            if len(c):
                c.popitem()
        assert c.currsize <= c.maxsize, "step %d" % step
        listed = list(c)
        assert len(listed) == len(c), "step %d" % step
        assert len(set(listed)) == len(listed), "step %d" % step
        total = 0
        for key in listed:
            total += len(c[key])
        assert total == c.currsize, "step %d" % step
    c.clear()
    assert len(c) == 0
    assert c.currsize == 0


@timed_kinds
def test_timed_invariants_under_mixed_workload_with_advancing_clock_pathB(kind):
    """★ D6 路径 B 综合：时钟持续推进下的混合负载不变式。"""
    rng = random.Random(987654321)
    clock = Clock()
    c = make_timed(kind, 8, 25, clock, getsizeof=len)
    keys = ["k%d" % i for i in range(10)]
    values = ["", "a", "bb", "ccc"]
    for step in range(300):
        op = rng.randrange(8)
        k = rng.choice(keys)
        if op < 4:
            c[k] = rng.choice(values)
        elif op == 4:
            c.get(k)
        elif op == 5:
            c.pop(k, None)
        elif op == 6:
            list(c.expire())
        else:
            if len(c):
                c.popitem()
        clock.advance(rng.choice([0, 0, 1, 3, 9]))
        assert c.currsize <= c.maxsize, "step %d" % step
        listed = list(c)
        assert len(listed) == len(c), "step %d" % step
        for key in listed:
            assert key in c, "step %d" % step
            c[key]
    clock.advance(1000)
    assert len(c) == 0
    assert list(c) == []
    list(c.expire())
    assert c.currsize == 0


@kinds
def test_no_stale_keys_after_heavy_eviction(kind):
    """D9：大量淘汰后不得留下"能被迭代到却取不出值"的幽灵键。"""
    c = make(kind, 4)
    for i in range(100):
        c["k%d" % i] = i
    listed = list(c)
    assert len(listed) == 4
    assert len(c) == 4
    for k in listed:
        assert k in c
        assert c[k] == int(k[1:])
    assert c.currsize == 4
    assert dict(c.items()) == {k: int(k[1:]) for k in listed}
