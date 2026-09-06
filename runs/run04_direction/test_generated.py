# -*- coding: utf-8 -*-
"""
pypinyin.contrib.tone_convert 的规格驱动测试

期望值全部由《汉语拼音方案》/ 拼音标注规范 + SPEC.md 的文档描述推导，
不依赖任何实现代码。

================================================================================
第一步：输入的特征维度表
================================================================================

D1  目标风格（由调用哪个函数决定）
      NORMAL / TONE / TONE2 / TONE3 / INITIALS / FINALS /
      FINALS_TONE / FINALS_TONE2 / FINALS_TONE3

D2  源风格（由传入字符串自带，函数必须自己识别）
      NORMAL(zhong) / TONE(zhōng) / TONE2(zho1ng) / TONE3(zhong1)

D3  音节结构
      声母+韵母(zhong) / 零声母(ai, an, er, ā) /
      y 起头(yi, yan, yuan, yong) / w 起头(wu, wo, wan, wen) /
      整体认读 zhi chi shi ri zi ci si

D4  韵母类型
      单韵母(a o e i u ü) / 复韵母(ai ao ou ia ie ua uo üe iou uei) /
      鼻韵母(an en ang eng ong ian iang uan uang uen üan ün iong)

D5  韵尾（决定 TONE2 的数字是否落在词中而非词尾）
      开尾(hao -> ha3o) / -i -u 尾(ai, ou) / -n 尾(jin -> ji1n) / -ng 尾(zhong -> zho1ng) / -r(er -> e2r)

D6  声调符号落在第几个字母（a > o > e > i/u/ü；iu 标 u；ui 标 i；单韵母标自身）
      首字母(ha3o) / 中间字母(zho1ng, hua2ng) / 末字母(gui1, liu2, lve4)

D7  ü 的书写形式（这是一个"多形态"维度）
      写作 ü(lüè, lüe4) / 写作 v(lve4, lv4) /
      j q x y 之后按正词法写作 u(ju, qu, xu, yu, yuan, jun) —— 实为 ü

D8  声调取值
      1 / 2 / 3 / 4 / 轻声（无调号）

D9  轻声的书写形式
      不写数字(shang, de) / 写 5 且在 TONE2 位置(sha5ng) / 写 5 且在末尾(shang5)

D10 布尔参数
      v_to_u          : False(输出用 v) / True(输出用 ü)
      neutral_tone_with_five : False(轻声不写数字) / True(轻声写 5)
      neutral_tone_with_5    : 老参数，传入时覆盖 neutral_tone_with_five
      strict          : True(严格按《汉语拼音方案》拆声母韵母) / False(按书写形式拆)

D11 输入合法性边界
      空串 / 已经是目标风格（幂等）

================================================================================
第二步：维度两两交叉（重点是"两个特殊情况叠加"）
================================================================================
交叉举例（下面测试全部覆盖）：
  D2 × D7   自带数字的串里同时自带 v          ('lv4', 'nve4', 'ju1n')
  D2 × D9   自带数字的串里数字恰好是 5        ('sha5ng', 'shang5')
  D7 × D9   同一个串里同时有 v 和 5           ('lv5', 'nve5')
  D7 × D10  自带 v/ü 的输入 × v_to_u 两种取值
  D9 × D10  自带 5 的输入 × neutral_tone_with_five 两种取值
  D7 × strict  j/q/x/y 后的 u × strict=True   ('jūn' -> ün, 'yuán' -> üan)
  D2 × strict  自带数字的输入 × iou/uei/uen 还原 ('liu2' -> iou)
  D5 × D6   -ng 尾且调号在中间字母（zho1ng / hua2ng / jia3ng）
  D3 × strict  y/w 起头 × strict（y/w 不是声母，yan 的韵母是 ian）

================================================================================
第三步：每个特征"进入函数的路径"
================================================================================
路径 A = 该特征由参数控制、在**输出**里被生成（走"生成"逻辑）
路径 B = 该特征已存在于**传入的字符串**里，函数必须识别并处理（走"解析"逻辑）

  特征                       路径 A（参数产生）                      路径 B（输入自带）
  -------------------------- --------------------------------------- --------------------------------------
  ü 写成 ü                   v_to_u=True                             输入串本身就是 'lüe4' / 'lü4'
  ü 写成 v                   v_to_u=False（默认）                    输入串本身就是 'lve4' / 'lv4' / 'lv5'
  ü 写成 u（jqxy 后）        —（无参数可产生）                       输入串是 'jūn' / 'ju1n' / 'yuan2'
  轻声用 5 标                neutral_tone_with_five=True             输入串本身就是 'sha5ng' / 'shang5'
  轻声不用 5 标              neutral_tone_with_five=False（默认）    输入串本身就是 'shang' / 'de'
  声调数字在词中(TONE2)      to_tone2(...) 生成                      输入串本身就是 'zho1ng' / 'e4r'
  声调数字在词尾(TONE3)      to_tone3(...) 生成                      输入串本身就是 'zhong1' / 'er4'
  声调符号(TONE)             to_tone(...) 生成                       输入串本身就是 'zhōng'
  iou/uei/uen 完整形式       strict=True 生成                        —（输入一般写缩写 iu/ui/un）
  无声母(y/w 不算声母)       strict=True                             输入串是 'yu' / 'wo'

每个测试函数名后缀标注 _path_a / _path_b / _path_ab（两条路径交叉）。
================================================================================
第四步：测试
================================================================================
"""
import pytest

from pypinyin.contrib.tone_convert import (
    to_normal,
    to_tone,
    to_tone2,
    to_tone3,
    to_initials,
    to_finals,
    to_finals_tone,
    to_finals_tone2,
    to_finals_tone3,
    tone_to_normal,
    tone_to_tone2,
    tone_to_tone3,
    tone2_to_normal,
    tone2_to_tone,
    tone2_to_tone3,
    tone3_to_normal,
    tone3_to_tone,
    tone3_to_tone2,
)

# ---------------------------------------------------------------------------
# 主音节表：同一个音节的四种风格写法（覆盖 D3/D4/D5/D6/D8）
# 字段: (TONE, TONE2_v, TONE3_v, NORMAL_v, NORMAL_u, TONE2_u, TONE3_u)
#   *_v  = v_to_u=False 时应有的写法（ü 写成 v）
#   *_u  = v_to_u=True  时应有的写法（ü 写成 ü）
# ---------------------------------------------------------------------------
SYLLABLES = [
    # 声母 + -ng 尾，调号在中间字母
    ('zhōng',  'zho1ng',  'zhong1',  'zhong',  'zhong',  'zho1ng',  'zhong1'),
    # 声母 + 复韵母，调号在首字母
    ('hǎo',    'ha3o',    'hao3',    'hao',    'hao',    'ha3o',    'hao3'),
    # iu：调号标在 u（末字母），TONE2 与 TONE3 写法相同
    ('liú',    'liu2',    'liu2',    'liu',    'liu',    'liu2',    'liu2'),
    # ui：调号标在 i（末字母）
    ('guī',    'gui1',    'gui1',    'gui',    'gui',    'gui1',    'gui1'),
    # 三合韵母 iang，调号在 a（中间）
    ('jiǎng',  'jia3ng',  'jiang3',  'jiang',  'jiang',  'jia3ng',  'jiang3'),
    # 三合韵母 uang，调号在 a（中间）
    ('huáng',  'hua2ng',  'huang2',  'huang',  'huang',  'hua2ng',  'huang2'),
    # -n 尾，调号在中间
    ('jīn',    'ji1n',    'jin1',    'jin',    'jin',    'ji1n',    'jin1'),
    # 零声母 er，-r 尾
    ('ér',     'e2r',     'er2',     'er',     'er',     'e2r',     'er2'),
    # 零声母复韵母
    ('ǎi',     'a3i',     'ai3',     'ai',     'ai',     'a3i',     'ai3'),
    # 零声母单韵母
    ('ā',      'a1',      'a1',      'a',      'a',      'a1',      'a1'),
    ('è',      'e4',      'e4',      'e',      'e',      'e4',      'e4'),
    # w 起头
    ('wǒ',     'wo3',     'wo3',     'wo',     'wo',     'wo3',     'wo3'),
    ('wēn',    'we1n',    'wen1',    'wen',    'wen',    'we1n',    'wen1'),
    # y 起头，jqxy 后的 u 实为 ü（D7 第三形态）
    ('yuán',   'yua2n',   'yuan2',   'yuan',   'yuan',   'yua2n',   'yuan2'),
    ('jūn',    'ju1n',    'jun1',    'jun',    'jun',    'ju1n',    'jun1'),
    ('xuě',    'xue3',    'xue3',    'xue',    'xue',    'xue3',    'xue3'),
    # 整体认读音节
    ('zhī',    'zhi1',    'zhi1',    'zhi',    'zhi',    'zhi1',    'zhi1'),
    ('sì',     'si4',     'si4',     'si',     'si',     'si4',     'si4'),
    # 真 ü（D7 前两形态）
    ('lǜ',     'lv4',     'lv4',     'lv',     'lü',     'lü4',     'lü4'),
    ('nǚ',     'nv3',     'nv3',     'nv',     'nü',     'nü3',     'nü3'),
    ('lüè',    'lve4',    'lve4',    'lve',    'lüe',    'lüe4',    'lüe4'),
    ('nüè',    'nve4',    'nve4',    'nve',    'nüe',    'nüe4',    'nüe4'),
    # 轻声（D8 轻声 / D9 不写数字）
    ('shang',  'shang',   'shang',   'shang',  'shang',  'shang',   'shang'),
    ('de',     'de',      'de',      'de',     'de',     'de',      'de'),
]

TONE_IDX, T2V_IDX, T3V_IDX, NV_IDX, NU_IDX, T2U_IDX, T3U_IDX = range(7)


def _cases(*idx):
    return [tuple(row[i] for i in idx) for row in SYLLABLES]


# ===========================================================================
# 组 1  通用 to_* 函数：源风格由输入数据自带（全部是路径 B —— 解析逻辑）
# ===========================================================================

@pytest.mark.parametrize('tone, expected', _cases(TONE_IDX, NV_IDX))
def test_to_normal_from_tone_input_path_b(tone, expected):
    """路径 B：输入自带 TONE 风格的调号，函数须识别并去掉。"""
    assert to_normal(tone) == expected


@pytest.mark.parametrize('tone2, expected', _cases(T2V_IDX, NV_IDX))
def test_to_normal_from_tone2_input_path_b(tone2, expected):
    """路径 B：输入自带 TONE2 风格（数字在词中）。"""
    assert to_normal(tone2) == expected


@pytest.mark.parametrize('tone3, expected', _cases(T3V_IDX, NV_IDX))
def test_to_normal_from_tone3_input_path_b(tone3, expected):
    """路径 B：输入自带 TONE3 风格（数字在词尾）。"""
    assert to_normal(tone3) == expected


@pytest.mark.parametrize('tone2, expected', _cases(T2V_IDX, TONE_IDX))
def test_to_tone_from_tone2_input_path_b(tone2, expected):
    assert to_tone(tone2) == expected


@pytest.mark.parametrize('tone3, expected', _cases(T3V_IDX, TONE_IDX))
def test_to_tone_from_tone3_input_path_b(tone3, expected):
    assert to_tone(tone3) == expected


@pytest.mark.parametrize('tone, expected', _cases(TONE_IDX, T2V_IDX))
def test_to_tone2_from_tone_input_path_b(tone, expected):
    assert to_tone2(tone) == expected


@pytest.mark.parametrize('tone3, expected', _cases(T3V_IDX, T2V_IDX))
def test_to_tone2_from_tone3_input_path_b(tone3, expected):
    assert to_tone2(tone3) == expected


@pytest.mark.parametrize('tone, expected', _cases(TONE_IDX, T3V_IDX))
def test_to_tone3_from_tone_input_path_b(tone, expected):
    assert to_tone3(tone) == expected


@pytest.mark.parametrize('tone2, expected', _cases(T2V_IDX, T3V_IDX))
def test_to_tone3_from_tone2_input_path_b(tone2, expected):
    assert to_tone3(tone2) == expected


# ===========================================================================
# 组 2  专用 xxx_to_yyy 函数（源风格固定，仍是路径 B 的解析）
# ===========================================================================

@pytest.mark.parametrize('tone, expected', _cases(TONE_IDX, NV_IDX))
def test_tone_to_normal_path_b(tone, expected):
    assert tone_to_normal(tone) == expected


@pytest.mark.parametrize('tone, expected', _cases(TONE_IDX, T2V_IDX))
def test_tone_to_tone2_path_b(tone, expected):
    assert tone_to_tone2(tone) == expected


@pytest.mark.parametrize('tone, expected', _cases(TONE_IDX, T3V_IDX))
def test_tone_to_tone3_path_b(tone, expected):
    assert tone_to_tone3(tone) == expected


@pytest.mark.parametrize('tone2, expected', _cases(T2V_IDX, NV_IDX))
def test_tone2_to_normal_path_b(tone2, expected):
    assert tone2_to_normal(tone2) == expected


@pytest.mark.parametrize('tone2, expected', _cases(T2V_IDX, TONE_IDX))
def test_tone2_to_tone_path_b(tone2, expected):
    assert tone2_to_tone(tone2) == expected


@pytest.mark.parametrize('tone2, expected', _cases(T2V_IDX, T3V_IDX))
def test_tone2_to_tone3_path_b(tone2, expected):
    assert tone2_to_tone3(tone2) == expected


@pytest.mark.parametrize('tone3, expected', _cases(T3V_IDX, NV_IDX))
def test_tone3_to_normal_path_b(tone3, expected):
    assert tone3_to_normal(tone3) == expected


@pytest.mark.parametrize('tone3, expected', _cases(T3V_IDX, TONE_IDX))
def test_tone3_to_tone_path_b(tone3, expected):
    assert tone3_to_tone(tone3) == expected


@pytest.mark.parametrize('tone3, expected', _cases(T3V_IDX, T2V_IDX))
def test_tone3_to_tone2_path_b(tone3, expected):
    assert tone3_to_tone2(tone3) == expected


# ===========================================================================
# 组 3  特征「ü」
#   路径 A：由 v_to_u 参数在输出里产生
#   路径 B：ü / v 已经写在输入串里，函数必须识别
# ===========================================================================

@pytest.mark.parametrize('tone, expected', _cases(TONE_IDX, NU_IDX))
def test_to_normal_v_to_u_path_a(tone, expected):
    """路径 A：输入是 TONE 风格（写 ü），由 v_to_u=True 决定输出保留 ü。"""
    assert to_normal(tone, v_to_u=True) == expected


@pytest.mark.parametrize('tone, expected', _cases(TONE_IDX, T2U_IDX))
def test_to_tone2_v_to_u_path_a(tone, expected):
    assert to_tone2(tone, v_to_u=True) == expected


@pytest.mark.parametrize('tone, expected', _cases(TONE_IDX, T3U_IDX))
def test_to_tone3_v_to_u_path_a(tone, expected):
    assert to_tone3(tone, v_to_u=True) == expected


@pytest.mark.parametrize('tone, expected', _cases(TONE_IDX, NU_IDX))
def test_tone_to_normal_v_to_u_path_a(tone, expected):
    assert tone_to_normal(tone, v_to_u=True) == expected


@pytest.mark.parametrize('tone, expected', _cases(TONE_IDX, T2U_IDX))
def test_tone_to_tone2_v_to_u_path_a(tone, expected):
    assert tone_to_tone2(tone, v_to_u=True) == expected


@pytest.mark.parametrize('tone, expected', _cases(TONE_IDX, T3U_IDX))
def test_tone_to_tone3_v_to_u_path_a(tone, expected):
    assert tone_to_tone3(tone, v_to_u=True) == expected


# --- 路径 B：输入串自带 v ---------------------------------------------------
# 'lv4' / 'nve4' 这类写法在 TONE2 与 TONE3 下相同（调号本就落在末字母上），
# 但函数仍必须把 v 当作 ü 来解析。

V_INPUT_TO_TONE = [
    ('lv4',   'lǜ'),
    ('nv3',   'nǚ'),
    ('lve4',  'lüè'),
    ('nve4',  'nüè'),
    ('lv2',   'lǘ'),
    ('nv2',   'nǘ'),
]


@pytest.mark.parametrize('src, expected', V_INPUT_TO_TONE)
def test_to_tone_from_v_input_path_b(src, expected):
    """路径 B：输入自带 v（代表 ü），转 TONE 时必须还原成带调号的 ü。"""
    assert to_tone(src) == expected


@pytest.mark.parametrize('src, expected', V_INPUT_TO_TONE)
def test_tone2_to_tone_from_v_input_path_b(src, expected):
    assert tone2_to_tone(src) == expected


@pytest.mark.parametrize('src, expected', V_INPUT_TO_TONE)
def test_tone3_to_tone_from_v_input_path_b(src, expected):
    assert tone3_to_tone(src) == expected


@pytest.mark.parametrize('src, expected_v, expected_u', [
    ('lv4',   'lv',   'lü'),
    ('nv3',   'nv',   'nü'),
    ('lve4',  'lve',  'lüe'),
    ('nve4',  'nve',  'nüe'),
])
def test_to_normal_from_v_input_path_ab(src, expected_v, expected_u):
    """路径 A×B：v 由输入自带，输出形式由 v_to_u 参数决定。"""
    assert to_normal(src) == expected_v
    assert to_normal(src, v_to_u=True) == expected_u


@pytest.mark.parametrize('src, expected_v, expected_u', [
    ('lü4',   'lv',   'lü'),
    ('nü3',   'nv',   'nü'),
    ('lüe4',  'lve',  'lüe'),
    ('nüe4',  'nve',  'nüe'),
])
def test_to_normal_from_u_umlaut_input_path_ab(src, expected_v, expected_u):
    """路径 A×B：输入串自带的是 ü 而不是 v，v_to_u=False 时必须转写成 v。"""
    assert to_normal(src) == expected_v
    assert to_normal(src, v_to_u=True) == expected_u


@pytest.mark.parametrize('src, expected', [
    ('lü4',   'lǜ'),
    ('nü3',   'nǚ'),
    ('lüe4',  'lüè'),
    ('nüe4',  'nüè'),
])
def test_to_tone_from_u_umlaut_input_path_b(src, expected):
    """路径 B：输入自带 ü + 数字，转 TONE。"""
    assert to_tone(src) == expected


@pytest.mark.parametrize('src, expected_v, expected_u', [
    ('lv4',   'lv4',   'lü4'),
    ('lü4',   'lv4',   'lü4'),
    ('nve4',  'nve4',  'nüe4'),
    ('nüe4',  'nve4',  'nüe4'),
])
def test_tone2_to_tone3_v_forms_path_ab(src, expected_v, expected_u):
    """路径 A×B：D7 的两种输入形态 × v_to_u 两种取值（2×2 交叉）。"""
    assert tone2_to_tone3(src) == expected_v
    assert tone2_to_tone3(src, v_to_u=True) == expected_u


@pytest.mark.parametrize('src, expected_v, expected_u', [
    ('lv4',   'lv4',   'lü4'),
    ('lü4',   'lv4',   'lü4'),
    ('nve4',  'nve4',  'nüe4'),
    ('nüe4',  'nve4',  'nüe4'),
])
def test_tone3_to_tone2_v_forms_path_ab(src, expected_v, expected_u):
    assert tone3_to_tone2(src) == expected_v
    assert tone3_to_tone2(src, v_to_u=True) == expected_u


def test_jqxy_u_stays_u_in_whole_syllable_path_b():
    """j/q/x/y 后的 u 虽然读 ü，但整音节风格里按正词法仍写 u，不应变成 v/ü。"""
    assert to_tone2('jú') == 'ju2'
    assert to_tone2('jú', v_to_u=True) == 'ju2'
    assert to_tone3('qù') == 'qu4'
    assert to_normal('xū') == 'xu'
    assert to_normal('yǔ', v_to_u=True) == 'yu'
    assert to_tone('ju2') == 'jú'
    assert to_tone('jun1') == 'jūn'
    assert to_tone('yua2n') == 'yuán'


# ===========================================================================
# 组 4  特征「轻声用 5 标记」
#   路径 A：由 neutral_tone_with_five / neutral_tone_with_5 参数产生
#   路径 B：输入串里已经带着 5（'sha5ng' 或 'shang5'）
# ===========================================================================

NEUTRAL_SYLLABLES = [
    # (NORMAL/TONE 无调写法, TONE2 带5, TONE3 带5)
    ('shang', 'sha5ng', 'shang5'),
    ('de',    'de5',    'de5'),
    ('le',    'le5',    'le5'),
    ('zi',    'zi5',    'zi5'),
    ('men',   'me5n',   'men5'),
    ('tou',   'to5u',   'tou5'),
]


@pytest.mark.parametrize('plain, t2_five, t3_five', NEUTRAL_SYLLABLES)
def test_to_tone2_neutral_five_path_a(plain, t2_five, t3_five):
    """路径 A：轻声的 5 由参数产生。"""
    assert to_tone2(plain) == plain
    assert to_tone2(plain, neutral_tone_with_five=True) == t2_five


@pytest.mark.parametrize('plain, t2_five, t3_five', NEUTRAL_SYLLABLES)
def test_to_tone3_neutral_five_path_a(plain, t2_five, t3_five):
    assert to_tone3(plain) == plain
    assert to_tone3(plain, neutral_tone_with_five=True) == t3_five


@pytest.mark.parametrize('plain, t2_five, t3_five', NEUTRAL_SYLLABLES)
def test_tone_to_tone2_neutral_five_path_a(plain, t2_five, t3_five):
    assert tone_to_tone2(plain) == plain
    assert tone_to_tone2(plain, neutral_tone_with_five=True) == t2_five


@pytest.mark.parametrize('plain, t2_five, t3_five', NEUTRAL_SYLLABLES)
def test_tone_to_tone3_neutral_five_path_a(plain, t2_five, t3_five):
    assert tone_to_tone3(plain) == plain
    assert tone_to_tone3(plain, neutral_tone_with_five=True) == t3_five


def test_neutral_tone_with_5_legacy_kwarg_path_a():
    """路径 A：老参数 neutral_tone_with_5 应覆盖 neutral_tone_with_five。"""
    assert to_tone2('shang', neutral_tone_with_5=True) == 'sha5ng'
    assert to_tone3('shang', neutral_tone_with_5=True) == 'shang5'
    assert tone_to_tone2('shang', neutral_tone_with_5=True) == 'sha5ng'
    assert tone_to_tone3('shang', neutral_tone_with_5=True) == 'shang5'
    # 老参数覆盖新参数：新参数 True 但老参数 False -> 不加 5
    assert to_tone2('shang', neutral_tone_with_five=True,
                    neutral_tone_with_5=False) == 'shang'
    assert to_tone3('shang', neutral_tone_with_five=True,
                    neutral_tone_with_5=False) == 'shang'
    # 老参数覆盖新参数：新参数 False 但老参数 True -> 加 5
    assert to_tone2('shang', neutral_tone_with_five=False,
                    neutral_tone_with_5=True) == 'sha5ng'
    assert to_tone3('shang', neutral_tone_with_five=False,
                    neutral_tone_with_5=True) == 'shang5'


# --- 路径 B：5 由输入串自带 -------------------------------------------------

@pytest.mark.parametrize('plain, t2_five, t3_five', NEUTRAL_SYLLABLES)
def test_to_normal_from_five_input_path_b(plain, t2_five, t3_five):
    """路径 B：输入自带轻声 5，NORMAL 风格不带任何数字，5 必须被去掉。"""
    assert to_normal(t2_five) == plain
    assert to_normal(t3_five) == plain


@pytest.mark.parametrize('plain, t2_five, t3_five', NEUTRAL_SYLLABLES)
def test_to_tone_from_five_input_path_b(plain, t2_five, t3_five):
    """路径 B：TONE 风格里轻声不带调号，5 必须被去掉。"""
    assert to_tone(t2_five) == plain
    assert to_tone(t3_five) == plain


@pytest.mark.parametrize('plain, t2_five, t3_five', NEUTRAL_SYLLABLES)
def test_tone2_to_normal_from_five_input_path_b(plain, t2_five, t3_five):
    assert tone2_to_normal(t2_five) == plain


@pytest.mark.parametrize('plain, t2_five, t3_five', NEUTRAL_SYLLABLES)
def test_tone3_to_normal_from_five_input_path_b(plain, t2_five, t3_five):
    assert tone3_to_normal(t3_five) == plain


@pytest.mark.parametrize('plain, t2_five, t3_five', NEUTRAL_SYLLABLES)
def test_tone2_to_tone_from_five_input_path_b(plain, t2_five, t3_five):
    assert tone2_to_tone(t2_five) == plain


@pytest.mark.parametrize('plain, t2_five, t3_five', NEUTRAL_SYLLABLES)
def test_tone3_to_tone_from_five_input_path_b(plain, t2_five, t3_five):
    assert tone3_to_tone(t3_five) == plain


@pytest.mark.parametrize('plain, t2_five, t3_five', NEUTRAL_SYLLABLES)
def test_to_tone3_from_five_input_path_ab(plain, t2_five, t3_five):
    """路径 A×B 交叉：5 由输入自带（TONE2 位置），输出是否保留 5 由参数决定。"""
    assert to_tone3(t2_five) == plain
    assert to_tone3(t2_five, neutral_tone_with_five=True) == t3_five


@pytest.mark.parametrize('plain, t2_five, t3_five', NEUTRAL_SYLLABLES)
def test_to_tone2_from_five_input_path_ab(plain, t2_five, t3_five):
    """路径 A×B 交叉：5 由输入自带（TONE3 位置），输出是否保留 5 由参数决定。"""
    assert to_tone2(t3_five) == plain
    assert to_tone2(t3_five, neutral_tone_with_five=True) == t2_five


@pytest.mark.parametrize('plain, t2_five, t3_five', NEUTRAL_SYLLABLES)
def test_dedicated_tone2_tone3_keep_five_position_path_b(plain, t2_five, t3_five):
    """路径 B：tone2_to_tone3 / tone3_to_tone2 没有 neutral 参数，
    输入自带的 5 应原样保留，只改变数字位置。"""
    assert tone2_to_tone3(t2_five) == t3_five
    assert tone3_to_tone2(t3_five) == t2_five


# ===========================================================================
# 组 5  「ü」× 「轻声 5」两个特殊情况叠加
# ===========================================================================

@pytest.mark.parametrize('src, expected_v, expected_u', [
    ('lv5',   'lv',   'lü'),
    ('nv5',   'nv',   'nü'),
    ('lve5',  'lve',  'lüe'),
    ('nve5',  'nve',  'nüe'),
    ('lü5',   'lv',   'lü'),
    ('lüe5',  'lve',  'lüe'),
])
def test_to_normal_v_and_five_both_from_input_path_b(src, expected_v, expected_u):
    """路径 B×B：输入串同时自带 v/ü 和轻声 5，两个特殊情况叠加。"""
    assert to_normal(src) == expected_v
    assert to_normal(src, v_to_u=True) == expected_u


@pytest.mark.parametrize('src, expected', [
    ('lv5',   'lv'),
    ('nve5',  'nve'),
    ('lü5',   'lv'),
    ('lüe5',  'lve'),
])
def test_to_tone_v_and_five_both_from_input_path_b(src, expected):
    """路径 B×B：轻声无调号，v/ü 无调号时 TONE 风格保持原书写形式。"""
    assert to_tone(src) == expected


@pytest.mark.parametrize('src, plain_v, five_v, five_u', [
    ('lve',  'lve',  'lve5',  'lüe5'),
    ('nve',  'nve',  'nve5',  'nüe5'),
    ('lv',   'lv',   'lv5',   'lü5'),
])
def test_to_tone3_v_from_input_five_from_param_path_ab(src, plain_v, five_v, five_u):
    """路径 B(v 自带) × 路径 A(5 由参数产生) × 路径 A(ü 由 v_to_u 产生)：三重叠加。"""
    assert to_tone3(src) == plain_v
    assert to_tone3(src, neutral_tone_with_five=True) == five_v
    assert to_tone3(src, neutral_tone_with_five=True, v_to_u=True) == five_u


@pytest.mark.parametrize('src, expected_v, expected_u', [
    ('lv5',   'lv5',   'lü5'),
    ('lve5',  'lve5',  'lüe5'),
    ('nve5',  'nve5',  'nüe5'),
])
def test_tone2_to_tone3_v_and_five_from_input_path_ab(src, expected_v, expected_u):
    """路径 B×B×A：输入同时带 v 和 5，输出 ü 形式由参数决定，5 原样保留。"""
    assert tone2_to_tone3(src) == expected_v
    assert tone2_to_tone3(src, v_to_u=True) == expected_u


# ===========================================================================
# 组 6  to_initials —— 特征「声母」× strict × 源风格（四种风格都要能吃）
# ===========================================================================

@pytest.mark.parametrize('src', ['zhōng', 'zho1ng', 'zhong1', 'zhong'])
def test_to_initials_accepts_all_input_styles_path_b(src):
    """路径 B：同一音节的四种源风格写法，声母结果必须一致。"""
    assert to_initials(src) == 'zh'
    assert to_initials(src, strict=False) == 'zh'


@pytest.mark.parametrize('src, strict_true, strict_false', [
    # y/w 按《汉语拼音方案》不是声母
    ('yǔ',    '',   'y'),
    ('yuán',  '',   'y'),
    ('yī',    '',   'y'),
    ('wǒ',    '',   'w'),
    ('wēn',   '',   'w'),
    ('wǔ',    '',   'w'),
    # 零声母
    ('ér',    '',   ''),
    ('ā',     '',   ''),
    ('ǎi',    '',   ''),
    ('àn',    '',   ''),
    # 普通声母，strict 与否一致
    ('zhī',   'zh', 'zh'),
    ('chī',   'ch', 'ch'),
    ('shì',   'sh', 'sh'),
    ('rì',    'r',  'r'),
    ('sì',    's',  's'),
    ('jūn',   'j',  'j'),
    ('lǜ',    'l',  'l'),
    ('nüè',   'n',  'n'),
])
def test_to_initials_strict_cross(src, strict_true, strict_false):
    """D3 × strict 交叉。"""
    assert to_initials(src, strict=True) == strict_true
    assert to_initials(src, strict=False) == strict_false


@pytest.mark.parametrize('src, expected', [
    ('lv4',   'l'),
    ('lve4',  'l'),
    ('nv3',   'n'),
    ('lv5',   'l'),
    ('ju1n',  'j'),
    ('yua2n', ''),
    ('e4r',   ''),
    ('sha5ng', 'sh'),
])
def test_to_initials_from_special_inputs_path_b(src, expected):
    """路径 B：输入自带 v / 5 / 词中数字，声母切分不应被这些字符干扰。"""
    assert to_initials(src, strict=True) == expected


# ===========================================================================
# 组 7  to_finals —— 特征「韵母」× strict × v_to_u × 源风格
# ===========================================================================

@pytest.mark.parametrize('src', ['zhōng', 'zho1ng', 'zhong1', 'zhong'])
def test_to_finals_accepts_all_input_styles_path_b(src):
    assert to_finals(src) == 'ong'


@pytest.mark.parametrize('src, strict_true, strict_false', [
    # iou / uei / uen 在有声母时缩写为 iu / ui / un，strict=True 还原完整形式
    ('liú',   'iou',  'iu'),
    ('niú',   'iou',  'iu'),
    ('guī',   'uei',  'ui'),
    ('duì',   'uei',  'ui'),
    ('lún',   'uen',  'un'),
    ('cùn',   'uen',  'un'),
    # y/w 起头：strict 下按 i/u 起头的韵母还原
    ('yī',    'i',    'i'),
    ('yán',   'ian',  'an'),
    ('yīn',   'in',   'in'),
    ('yīng',  'ing',  'ing'),
    ('yòng',  'iong', 'ong'),
    ('yě',    'ie',   'e'),
    ('wǔ',    'u',    'u'),
    ('wǒ',    'uo',   'o'),
    ('wǎn',   'uan',  'an'),
    ('wēn',   'uen',  'en'),
    ('wàng',  'uang', 'ang'),
    # 整体认读音节的韵母是 i
    ('zhī',   'i',    'i'),
    ('sì',    'i',    'i'),
    # 普通音节
    ('hǎo',   'ao',   'ao'),
    ('ér',    'er',   'er'),
    ('jiǎng', 'iang', 'iang'),
    ('huáng', 'uang', 'uang'),
])
def test_to_finals_strict_cross(src, strict_true, strict_false):
    """D4/D3 × strict 交叉。"""
    assert to_finals(src, strict=True) == strict_true
    assert to_finals(src, strict=False) == strict_false


@pytest.mark.parametrize('src, strict_v, strict_u, nonstrict', [
    # j/q/x/y 之后的 u 实际是 ü：strict=True 必须还原
    ('jūn',   'vn',  'ün',  'un'),
    ('qún',   'vn',  'ün',  'un'),
    ('xùn',   'vn',  'ün',  'un'),
    ('yūn',   'vn',  'ün',  'un'),
    ('jú',    'v',   'ü',   'u'),
    ('qū',    'v',   'ü',   'u'),
    ('xǔ',    'v',   'ü',   'u'),
    ('yǔ',    'v',   'ü',   'u'),
    ('yuán',  'van', 'üan', 'uan'),
    ('juǎn',  'van', 'üan', 'uan'),
    ('xuě',   've',  'üe',  'ue'),
    ('yuè',   've',  'üe',  'ue'),
])
def test_to_finals_jqxy_u_is_umlaut_strict_cross(src, strict_v, strict_u, nonstrict):
    """D7 第三形态（jqxy 后写 u）× strict × v_to_u 三维交叉。"""
    assert to_finals(src, strict=True) == strict_v
    assert to_finals(src, strict=True, v_to_u=True) == strict_u
    assert to_finals(src, strict=False) == nonstrict
    # strict=False 时按书写形式切分，u 就是 u，v_to_u 不应把它变成 ü
    assert to_finals(src, strict=False, v_to_u=True) == nonstrict


@pytest.mark.parametrize('src, expected_v, expected_u', [
    ('lǜ',    'v',   'ü'),
    ('nǚ',    'v',   'ü'),
    ('lüè',   've',  'üe'),
    ('nüè',   've',  'üe'),
])
def test_to_finals_real_umlaut_path_ab(src, expected_v, expected_u):
    """路径 A：ü 的输出形式由 v_to_u 决定。"""
    assert to_finals(src, strict=True) == expected_v
    assert to_finals(src, strict=True, v_to_u=True) == expected_u


@pytest.mark.parametrize('src, expected_v, expected_u', [
    # 输入自带 v
    ('lv4',   'v',   'ü'),
    ('nv3',   'v',   'ü'),
    ('lve4',  've',  'üe'),
    ('nve4',  've',  'üe'),
    ('lv',    'v',   'ü'),
    ('lve',   've',  'üe'),
    # 输入自带 ü
    ('lü4',   'v',   'ü'),
    ('lüe4',  've',  'üe'),
    # 输入自带 v 且自带轻声 5（双特殊叠加）
    ('lv5',   'v',   'ü'),
    ('nve5',  've',  'üe'),
])
def test_to_finals_from_v_input_path_ab(src, expected_v, expected_u):
    """路径 B（v/ü/5 自带）× 路径 A（v_to_u 参数）。"""
    assert to_finals(src, strict=True) == expected_v
    assert to_finals(src, strict=True, v_to_u=True) == expected_u


@pytest.mark.parametrize('src, strict_true, strict_false', [
    # 输入自带 TONE2 / TONE3 数字，且需要 strict 还原 iou/uei/uen
    ('liu2',   'iou',  'iu'),
    ('gui1',   'uei',  'ui'),
    ('lu2n',   'uen',  'un'),
    ('lun2',   'uen',  'un'),
    # 输入自带数字 + jqxy 的 u 实为 ü（三重叠加）
    ('ju1n',   'vn',   'un'),
    ('jun1',   'vn',   'un'),
    ('yua2n',  'van',  'uan'),
    ('yuan2',  'van',  'uan'),
    ('xue3',   've',   'ue'),
    # 输入自带数字 + y/w 起头
    ('ya2n',   'ian',  'an'),
    ('yan2',   'ian',  'an'),
    ('we1n',   'uen',  'en'),
    ('wen1',   'uen',  'en'),
    # 输入自带轻声 5
    ('sha5ng', 'ang',  'ang'),
    ('shang5', 'ang',  'ang'),
    ('to5u',   'ou',   'ou'),
    ('tou5',   'ou',   'ou'),
])
def test_to_finals_from_numbered_input_strict_cross_path_b(src, strict_true, strict_false):
    """路径 B×D-strict：输入自带声调数字（含 5）时，韵母切分/还原仍须正确。"""
    assert to_finals(src, strict=True) == strict_true
    assert to_finals(src, strict=False) == strict_false


# ===========================================================================
# 组 8  to_finals_tone / to_finals_tone2 / to_finals_tone3
#       特征「韵母 + 声调」× 源风格 × strict × v_to_u × neutral 5
# ===========================================================================

@pytest.mark.parametrize('src', ['zhōng', 'zho1ng', 'zhong1'])
def test_to_finals_tone_accepts_all_input_styles_path_b(src):
    """路径 B：TONE / TONE2 / TONE3 三种源风格都要能还原成带调号的韵母。"""
    assert to_finals_tone(src) == 'ōng'


@pytest.mark.parametrize('src', ['zhōng', 'zho1ng', 'zhong1'])
def test_to_finals_tone2_accepts_all_input_styles_path_b(src):
    assert to_finals_tone2(src) == 'o1ng'


@pytest.mark.parametrize('src', ['zhōng', 'zho1ng', 'zhong1'])
def test_to_finals_tone3_accepts_all_input_styles_path_b(src):
    assert to_finals_tone3(src) == 'ong1'


@pytest.mark.parametrize('src, expected', [
    ('hǎo',   'ǎo'),
    ('ér',    'ér'),
    ('ǎi',    'ǎi'),
    ('ā',     'ā'),
    ('zhī',   'ī'),
    ('jiǎng', 'iǎng'),
    ('huáng', 'uáng'),
    # ü 类：to_finals_tone 无 v_to_u 参数，应输出规范的 ü
    ('lǜ',    'ǜ'),
    ('nǚ',    'ǚ'),
    ('lüè',   'üè'),
    ('xuě',   'üě'),
    ('yuè',   'üè'),
    ('yǔ',    'ǚ'),
    ('jú',    'ǘ'),
    # y/w 起头 strict 还原
    ('yán',   'ián'),
    ('wǒ',    'uǒ'),
    ('yòng',  'iòng'),
])
def test_to_finals_tone_strict(src, expected):
    assert to_finals_tone(src, strict=True) == expected


@pytest.mark.parametrize('src, expected', [
    ('hǎo',   'ao3'),
    ('ér',    'er2'),
    ('zhī',   'i1'),
    ('jiǎng', 'iang3'),
    ('huáng', 'uang2'),
    # strict 下 iu/ui/un 还原为 iou/uei/uen，TONE3 的数字一律在末尾
    ('liú',   'iou2'),
    ('guī',   'uei1'),
    ('lún',   'uen2'),
    ('yán',   'ian2'),
    ('wēn',   'uen1'),
    ('yòng',  'iong4'),
])
def test_to_finals_tone3_strict(src, expected):
    assert to_finals_tone3(src, strict=True) == expected


@pytest.mark.parametrize('src, expected_v, expected_u', [
    ('lǜ',    'v4',   'ü4'),
    ('nǚ',    'v3',   'ü3'),
    ('lüè',   've4',  'üe4'),
    ('xuě',   've3',  'üe3'),
    ('yuè',   've4',  'üe4'),
    ('jūn',   'vn1',  'ün1'),
    ('yuán',  'van2', 'üan2'),
    ('yǔ',    'v3',   'ü3'),
])
def test_to_finals_tone3_umlaut_v_to_u_path_a(src, expected_v, expected_u):
    """路径 A：ü 的输出形式由 v_to_u 决定（strict=True 下才会出现 ü）。"""
    assert to_finals_tone3(src, strict=True) == expected_v
    assert to_finals_tone3(src, strict=True, v_to_u=True) == expected_u


@pytest.mark.parametrize('src, expected_v, expected_u', [
    # 调号落在末字母，TONE2 与 TONE3 写法相同，避开标调位置歧义
    ('lǜ',    'v4',   'ü4'),
    ('lüè',   've4',  'üe4'),
    ('xuě',   've3',  'üe3'),
])
def test_to_finals_tone2_umlaut_v_to_u_path_a(src, expected_v, expected_u):
    assert to_finals_tone2(src, strict=True) == expected_v
    assert to_finals_tone2(src, strict=True, v_to_u=True) == expected_u


@pytest.mark.parametrize('src, expected', [
    ('zhōng', 'o1ng'),
    ('hǎo',   'a3o'),
    ('jiǎng', 'ia3ng'),
    ('huáng', 'ua2ng'),
    ('ér',    'e2r'),
    ('zhī',   'i1'),
])
def test_to_finals_tone2_strict(src, expected):
    assert to_finals_tone2(src, strict=True) == expected


@pytest.mark.parametrize('src, expected_tone, expected_t3', [
    # 路径 B：输入自带 v / ü
    ('lv4',   'ǜ',   'v4'),
    ('lü4',   'ǜ',   'v4'),
    ('nve4',  'üè',  've4'),
    ('nüe4',  'üè',  've4'),
    ('lv',    'ü',   'v'),
    ('lve',   'üe',  've'),
])
def test_finals_tone_from_v_input_path_b(src, expected_tone, expected_t3):
    """路径 B：韵母函数吃自带 v/ü 的输入。"""
    assert to_finals_tone(src, strict=True) == expected_tone
    assert to_finals_tone3(src, strict=True) == expected_t3


@pytest.mark.parametrize('src, expected', [
    # 路径 B：输入自带数字，且 strict 需要还原 iou/uei/uen 或 ü
    ('liu2',   'iou2'),
    ('gui1',   'uei1'),
    ('lun2',   'uen2'),
    ('lu2n',   'uen2'),
    ('ju1n',   'vn1'),
    ('jun1',   'vn1'),
    ('yua2n',  'van2'),
    ('yuan2',  'van2'),
    ('xue3',   've3'),
    ('ya2n',   'ian2'),
    ('yan2',   'ian2'),
    ('e4r',    'er4'),
    ('er4',    'er4'),
])
def test_to_finals_tone3_from_numbered_input_path_b(src, expected):
    """路径 B：输入自带声调数字 × strict 还原，双特殊叠加。"""
    assert to_finals_tone3(src, strict=True) == expected


@pytest.mark.parametrize('src, expected', [
    ('liu2',  'ioú'),
    ('gui1',  'ueī'),
])
def test_to_finals_tone_from_numbered_input_keeps_tone_letter_path_b(src, expected):
    """路径 B：strict 还原 iou/uei 时，调号仍标在原来带调的那个字母上
    （liu 的调在 u、gui 的调在 i，还原后不重新选字母）。"""
    assert to_finals_tone(src, strict=True) == expected


@pytest.mark.parametrize('plain, t2_five, t3_five, finals', [
    ('shang', 'sha5ng', 'shang5', 'ang'),
    ('de',    'de5',    'de5',    'e'),
    ('zi',    'zi5',    'zi5',    'i'),
    ('tou',   'to5u',   'tou5',   'ou'),
])
def test_finals_neutral_five_path_ab(plain, t2_five, t3_five, finals):
    """路径 A（参数产生 5） vs 路径 B（输入自带 5）。"""
    # 路径 A
    assert to_finals_tone3(plain, strict=True) == finals
    assert to_finals_tone3(plain, strict=True,
                           neutral_tone_with_five=True) == finals + '5'
    assert to_finals_tone2(plain, strict=True,
                           neutral_tone_with_five=True) == finals + '5'
    # 路径 B：输入自带 5，默认不输出 5
    assert to_finals_tone3(t2_five, strict=True) == finals
    assert to_finals_tone3(t3_five, strict=True) == finals
    # 路径 A×B：输入自带 5 且参数要求输出 5
    assert to_finals_tone3(t2_five, strict=True,
                           neutral_tone_with_five=True) == finals + '5'
    assert to_finals_tone3(t3_five, strict=True,
                           neutral_tone_with_five=True) == finals + '5'
    # TONE 风格轻声不带调号
    assert to_finals_tone(t2_five, strict=True) == finals
    assert to_finals_tone(t3_five, strict=True) == finals


@pytest.mark.parametrize('src, plain_v, five_v, five_u', [
    ('lv',   'v',  'v5',  'ü5'),
    ('lve',  've', 've5', 'üe5'),
    ('nve',  've', 've5', 'üe5'),
])
def test_finals_v_input_with_neutral_five_param_path_ab(src, plain_v, five_v, five_u):
    """三重叠加：v 自带（路径 B）× 5 由参数产生（路径 A）× ü 由参数产生（路径 A）。"""
    assert to_finals_tone3(src, strict=True) == plain_v
    assert to_finals_tone3(src, strict=True,
                           neutral_tone_with_five=True) == five_v
    assert to_finals_tone3(src, strict=True, neutral_tone_with_five=True,
                           v_to_u=True) == five_u


@pytest.mark.parametrize('src, expected_v, expected_u', [
    ('lv5',   'v',  'ü'),
    ('lve5',  've', 'üe'),
    ('nve5',  've', 'üe'),
])
def test_finals_v_and_five_both_from_input_path_b(src, expected_v, expected_u):
    """路径 B×B：输入同时自带 v 和 5。"""
    assert to_finals(src, strict=True) == expected_v
    assert to_finals(src, strict=True, v_to_u=True) == expected_u
    assert to_finals_tone3(src, strict=True) == expected_v


# ===========================================================================
# 组 9  幂等与边界（D11）
# ===========================================================================

@pytest.mark.parametrize('tone2', [row[T2V_IDX] for row in SYLLABLES])
def test_to_tone2_idempotent(tone2):
    """已经是 TONE2 风格，再转一次应保持不变。"""
    assert to_tone2(tone2) == tone2


@pytest.mark.parametrize('tone3', [row[T3V_IDX] for row in SYLLABLES])
def test_to_tone3_idempotent(tone3):
    assert to_tone3(tone3) == tone3


@pytest.mark.parametrize('tone', [row[TONE_IDX] for row in SYLLABLES])
def test_to_tone_idempotent(tone):
    assert to_tone(tone) == tone


@pytest.mark.parametrize('normal', [row[NV_IDX] for row in SYLLABLES])
def test_to_normal_idempotent(normal):
    """NORMAL 风格再转 NORMAL 应保持不变（含 'lv'、'lve' 这类 v 写法）。"""
    assert to_normal(normal) == normal


@pytest.mark.parametrize('tone, tone2, tone3', _cases(TONE_IDX, T2V_IDX, T3V_IDX))
def test_round_trip_between_tone_styles(tone, tone2, tone3):
    assert to_tone(to_tone2(tone)) == tone
    assert to_tone(to_tone3(tone)) == tone
    assert to_tone2(to_tone3(tone2)) == tone2
    assert to_tone3(to_tone2(tone3)) == tone3


@pytest.mark.parametrize('func', [to_normal, to_tone, to_tone2, to_tone3])
def test_empty_string_input(func):
    """边界：空串没有可转换的内容，应返回空串。"""
    assert func('') == ''
