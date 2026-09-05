# -*- coding: utf-8 -*-
"""
pypinyin.contrib.tone_convert —— 基于「特征维度矩阵 + 两两交叉(pairwise)」设计的测试

所有期望值均由 SPEC.md 的文档描述 + 《汉语拼音方案》的标调/拼写规范推导得出，
未参考任何实现代码、issue、changelog 或运行结果。

================================================================================
第一步：输入特征维度表
================================================================================

D1  输入风格
    D1.a NORMAL          zhong / shang / lve
    D1.b TONE            zhōng（调号标在字母上）
    D1.c TONE2           zho1ng（数字紧跟带调字母）
    D1.d TONE3           zhong1（数字在音节末尾）

D2  声母类型
    D2.a 零声母（a/e/o 开头）      ān, ér, ǒu, ǎi
    D2.b 单字母声母                b l n j q x g s
    D2.c 双字母声母                zh ch sh
    D2.d y/w 开头（严格拼音方案中不是声母，只是 i/u/ü 行的书写形式）

D3  韵母结构
    D3.a 单韵母                    a o e i u ü
    D3.b 带韵头的复韵母            ia ua üe iao uai üan
    D3.c 带韵尾 i/u/o 的复韵母     ai ei ao ou
    D3.d 鼻韵尾 -n                 an en in ün uan
    D3.e 鼻韵尾 -ng                ang eng ong ing iong
    D3.f 特殊韵母 er
    D3.g 舌尖元音 i（zhi/chi/shi/ri/zi/ci/si）
    D3.h 缩写韵母 iu/ui/un（本体为 iou/uei/uen）
    D3.i 无元音音节                ń ḿ

D4  声调所在位置（相对于整个音节）
    D4.a 第一个字母                ān a1n / ér e2r / ǒu o3u
    D4.b 中间字母                  zhōng zho1ng / xiǎo xia3o / jūn ju1n
    D4.c 最后一个字母              nǐ ni3 / liù liu4 / lǜ lv4

D5  ü 的书写形式
    D5.a 字面 ü                    lǜ, lüè, nǚ
    D5.b 字面 v                    lv4, lve4, nv3
    D5.c j/q/x/y 后写作 u（实为 ü）ju, qu, xue, jun, yu, yuan, yun, yue
    D5.d 不含 ü                    zhong, shang

D6  声调值
    D6.1 阴平 1        D6.2 阳平 2      D6.3 上声 3      D6.4 去声 4
    D6.0 轻声（TONE 风格无任何标记；TONE2/TONE3 中可选用数字 5 表示）

D7  v_to_u（布尔维度，出现在 to_normal / to_tone2 / to_tone3 / to_finals* / tone*_to_* 中）
    D7.F False → 结果用 v 表示 ü
    D7.T True  → 结果用 ü

D8  neutral_tone_with_five（布尔维度）
    D8.F False → 轻声不带数字
    D8.T True  → 轻声用 5 标记
    D8.L 旧参数 neutral_tone_with_5 经 **kwargs 传入，且优先级高于 neutral_tone_with_five

D9  strict（布尔维度，出现在 to_initials / to_finals* 中）
    D9.T True  → 严格遵照《汉语拼音方案》：y/w 非声母；iu/ui/un 还原为 iou/uei/uen；
                 j/q/x/y 后的 u 还原为 ü
    D9.F False → 宽松：y/w 视为声母；iu/ui/un 保持缩写；j/q/x/y 后的 u 保持 u

D10 是否属于缩写韵母 iu/ui/un
    D10.Y 是（liu gui lun you wei wen）
    D10.N 否

================================================================================
第二步：两两交叉一览（共 22 组，逐组在下方标注）
================================================================================
C01 D1×D4   输入风格 × 声调位置
C02 D1×D5   输入风格 × ü 书写形式
C03 D1×D6   输入风格 × 声调值
C04 D4×D6   声调位置 × 声调值
C05 D4×D7   声调位置 × v_to_u
C06 D4×D8   声调位置 × 轻声 5           ← 高危：5 该插在哪个字母后
C07 D5×D7   ü 书写形式 × v_to_u         ← 高危：j/q/x 后的 u 不应被 v_to_u 影响
C08 D5×D8   ü 书写形式 × 轻声 5
C09 D5×D9   ü 书写形式 × strict         ← 高危：ju/yu 的韵母是 ü
C10 D9×D10  strict × 缩写韵母           ← 高危：iu→iou, ui→uei, un→uen
C11 D10×D4  缩写韵母 × 声调位置         ← 高危：iou 还原后调号应在 o 上
C12 D10×D8  缩写韵母 × 轻声 5           ← 高危：还原 + 轻声叠加
C13 D2×D9   声母类型 × strict           ← y/w 是否算声母
C14 D2×D3   声母类型 × 韵母结构
C15 D3×D4   韵母结构 × 声调位置
C16 D7×D8   v_to_u × 轻声 5
C17 D7×D9   v_to_u × strict
C18 D8×D8.L neutral_tone_with_five × 旧参数 neutral_tone_with_5（冲突覆盖）
C19 D1×D9   输入风格 × strict（finals 系列接受 4 种输入风格）
C20 D3×D9   韵母结构 × strict（er / iong / 舌尖 i）
C21 D1×D6.0 已含 5 的 TONE2/TONE3 作为输入
C22 D2×D4   声母类型 × 声调位置（零声母首字母带调）
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


# =============================================================================
# C01  D1(输入风格) × D4(声调位置)
#      三种带调风格 × 首/中/末字母带调，全部归一到 NORMAL / TONE / TONE2 / TONE3
# =============================================================================

# (TONE, TONE2, TONE3, NORMAL, 声调位置)
_C01_ROWS = [
    # D4.a 第一个字母带调
    ('ān',    'a1n',       'an1',    'an'),
    ('ér',    'e2r',       'er2',    'er'),
    ('ǒu',    'o3u',       'ou3',    'ou'),
    ('ài',    'a4i',       'ai4',    'ai'),
    # D4.b 中间字母带调
    ('zhōng', 'zho1ng',    'zhong1', 'zhong'),
    ('xiǎo',  'xia3o',     'xiao3',  'xiao'),
    ('huáng', 'hua2ng',    'huang2', 'huang'),
    ('jūn',   'ju1n',      'jun1',   'jun'),
    ('wèi',   'we4i',      'wei4',   'wei'),
    ('yòu',   'yo4u',      'you4',   'you'),
    # D4.c 最后一个字母带调
    ('nǐ',    'ni3',       'ni3',    'ni'),
    ('liù',   'liu4',      'liu4',   'liu'),
    ('guì',   'gui4',      'gui4',   'gui'),
    ('zhī',   'zhi1',      'zhi1',   'zhi'),
]


@pytest.mark.parametrize('tone, tone2, tone3, normal', _C01_ROWS)
def test_c01_to_normal_from_all_three_toned_styles(tone, tone2, tone3, normal):
    """C01: NORMAL 化结果与输入风格、声调位置都无关。"""
    assert to_normal(tone) == normal
    assert to_normal(tone2) == normal
    assert to_normal(tone3) == normal
    assert to_normal(normal) == normal


@pytest.mark.parametrize('tone, tone2, tone3, normal', _C01_ROWS)
def test_c01_to_tone_from_tone2_and_tone3(tone, tone2, tone3, normal):
    """C01: TONE2/TONE3 → TONE，调号必须落回规范位置。"""
    assert to_tone(tone2) == tone
    assert to_tone(tone3) == tone


@pytest.mark.parametrize('tone, tone2, tone3, normal', _C01_ROWS)
def test_c01_to_tone2_from_tone_and_tone3(tone, tone2, tone3, normal):
    """C01: TONE/TONE3 → TONE2，数字必须紧跟带调字母（可能在音节中间）。"""
    assert to_tone2(tone) == tone2
    assert to_tone2(tone3) == tone2


@pytest.mark.parametrize('tone, tone2, tone3, normal', _C01_ROWS)
def test_c01_to_tone3_from_tone_and_tone2(tone, tone2, tone3, normal):
    """C01: TONE/TONE2 → TONE3，数字必须移到音节末尾。"""
    assert to_tone3(tone) == tone3
    assert to_tone3(tone2) == tone3


@pytest.mark.parametrize('tone, tone2, tone3, normal', _C01_ROWS)
def test_c01_pairwise_named_converters(tone, tone2, tone3, normal):
    """C01: 具名转换函数（tone_to_* / tone2_to_* / tone3_to_*）与 to_* 结果一致。"""
    assert tone_to_normal(tone) == normal
    assert tone_to_tone2(tone) == tone2
    assert tone_to_tone3(tone) == tone3
    assert tone2_to_normal(tone2) == normal
    assert tone2_to_tone(tone2) == tone
    assert tone2_to_tone3(tone2) == tone3
    assert tone3_to_normal(tone3) == normal
    assert tone3_to_tone(tone3) == tone
    assert tone3_to_tone2(tone3) == tone2


# =============================================================================
# C02  D1(输入风格) × D5(ü 书写形式)
#      ü / v / j·q·x·y 后的 u，三种写法分别从 TONE、TONE2、TONE3 进入
# =============================================================================

@pytest.mark.parametrize('src', ['lǜ', 'lv4', 'lü4'])
def test_c02_lv_all_input_styles_to_normal(src):
    """C02: D5.a(ü) / D5.b(v) 两种写法 × TONE/TONE2/TONE3 输入，默认输出 v。"""
    assert to_normal(src) == 'lv'
    assert to_normal(src, v_to_u=True) == 'lü'


@pytest.mark.parametrize('src', ['lüè', 'lve4', 'lüe4'])
def test_c02_lue_all_input_styles(src):
    """C02: 韵母 üe（ü 在韵头、调在韵尾）× 三种输入风格。"""
    assert to_normal(src) == 'lve'
    assert to_normal(src, v_to_u=True) == 'lüe'
    assert to_tone(src) == 'lüè'
    assert to_tone2(src, v_to_u=True) == 'lüe4'
    assert to_tone3(src, v_to_u=True) == 'lüe4'


@pytest.mark.parametrize('src, expected_normal', [
    ('jūn', 'jun'), ('ju1n', 'jun'), ('jun1', 'jun'),
    ('qù', 'qu'), ('qu4', 'qu'),
    ('xué', 'xue'), ('xue2', 'xue'),
    ('yuǎn', 'yuan'), ('yua3n', 'yuan'), ('yuan3', 'yuan'),
    ('yún', 'yun'), ('yu2n', 'yun'), ('yun2', 'yun'),
])
def test_c02_u_after_jqxy_all_input_styles(src, expected_normal):
    """C02: D5.c —— j/q/x/y 后书写为 u 的 ü，整音节层面应原样保留 u。"""
    assert to_normal(src) == expected_normal


# =============================================================================
# C03 / C21  D1(输入风格) × D6(声调值，含轻声)
# =============================================================================

@pytest.mark.parametrize('tone_num', [1, 2, 3, 4])
def test_c03_all_four_tones_on_same_syllable(tone_num):
    """C03: 同一音节 ma 的四个声调 × TONE/TONE2/TONE3 三种风格互转。"""
    tone = {1: 'mā', 2: 'má', 3: 'mǎ', 4: 'mà'}[tone_num]
    tone2 = 'ma{}'.format(tone_num)
    tone3 = 'ma{}'.format(tone_num)
    assert to_tone2(tone) == tone2
    assert to_tone3(tone) == tone3
    assert to_tone(tone2) == tone
    assert to_tone(tone3) == tone
    assert to_normal(tone) == 'ma'


@pytest.mark.parametrize('tone_num', [1, 2, 3, 4])
def test_c03_four_tones_with_mid_syllable_position(tone_num):
    """C03 × C04: 四个声调 × D4.b(调在音节中部)，检验数字插入位置不随调值漂移。"""
    tone = {1: 'zhōng', 2: 'zhóng', 3: 'zhǒng', 4: 'zhòng'}[tone_num]
    assert to_tone2(tone) == 'zho{}ng'.format(tone_num)
    assert to_tone3(tone) == 'zhong{}'.format(tone_num)
    assert to_tone(to_tone2(tone)) == tone


@pytest.mark.parametrize('normal', ['shang', 'de', 'zi', 'le', 'ma'])
def test_c03_neutral_tone_default_has_no_digit(normal):
    """C03: D6.0 轻声 × 默认参数，TONE2/TONE3 都不应出现数字。"""
    assert to_tone2(normal) == normal
    assert to_tone3(normal) == normal
    assert to_normal(normal) == normal
    assert to_tone(normal) == normal


@pytest.mark.parametrize('tone2_with5, tone3_with5, normal', [
    ('sha5ng', 'shang5', 'shang'),
    ('de5', 'de5', 'de'),
    ('zi5', 'zi5', 'zi'),
    ('xia5o', 'xiao5', 'xiao'),
    ('liu5', 'liu5', 'liu'),
])
def test_c21_five_marked_neutral_as_input(tone2_with5, tone3_with5, normal):
    """C21: D6.0(带 5 的轻声) 作为输入 × D1(TONE2/TONE3)。
    轻声在 TONE 风格中没有任何调号，所以 to_tone 应还原成裸音节。"""
    assert to_normal(tone2_with5) == normal
    assert to_normal(tone3_with5) == normal
    assert to_tone(tone2_with5) == normal
    assert to_tone(tone3_with5) == normal
    assert tone2_to_tone3(tone2_with5) == tone3_with5
    assert tone3_to_tone2(tone3_with5) == tone2_with5


# =============================================================================
# C04  D4(声调位置) × D6(声调值)
# =============================================================================

@pytest.mark.parametrize('tone, tone2, tone3', [
    # 首字母带调 × 各调值
    ('āi', 'a1i', 'ai1'),
    ('ái', 'a2i', 'ai2'),
    ('ǎi', 'a3i', 'ai3'),
    ('ài', 'a4i', 'ai4'),
    # 中间字母带调 × 各调值
    ('xiāo', 'xia1o', 'xiao1'),
    ('xiáo', 'xia2o', 'xiao2'),
    ('xiǎo', 'xia3o', 'xiao3'),
    ('xiào', 'xia4o', 'xiao4'),
    # 末字母带调 × 各调值
    ('nī', 'ni1', 'ni1'),
    ('ní', 'ni2', 'ni2'),
    ('nǐ', 'ni3', 'ni3'),
    ('nì', 'ni4', 'ni4'),
])
def test_c04_tone_position_by_tone_value(tone, tone2, tone3):
    """C04: 调值变化不应改变数字插入位置。"""
    assert to_tone2(tone) == tone2
    assert to_tone3(tone) == tone3
    assert to_tone(tone2) == tone
    assert to_tone(tone3) == tone


# =============================================================================
# C05  D4(声调位置) × D7(v_to_u)
# =============================================================================

@pytest.mark.parametrize('tone, v_form_tone2, u_form_tone2, v_form_tone3, u_form_tone3', [
    # D4.c 调在末尾的 ü 本身
    ('lǜ',  'lv4',  'lü4',  'lv4',  'lü4'),
    ('nǚ',  'nv3',  'nü3',  'nv3',  'nü3'),
    ('lǘ',  'lv2',  'lü2',  'lv2',  'lü2'),
    # D4.c 调在末尾，但 ü 在韵头
    ('lüè', 'lve4', 'lüe4', 'lve4', 'lüe4'),
    ('nüè', 'nve4', 'nüe4', 'nve4', 'nüe4'),
    ('lüě', 'lve3', 'lüe3', 'lve3', 'lüe3'),
])
def test_c05_v_to_u_with_tone_position(tone, v_form_tone2, u_form_tone2,
                                       v_form_tone3, u_form_tone3):
    """C05: v_to_u 只改变 ü/v 的书写，不应改变数字位置。"""
    assert to_tone2(tone) == v_form_tone2
    assert to_tone2(tone, v_to_u=True) == u_form_tone2
    assert to_tone3(tone) == v_form_tone3
    assert to_tone3(tone, v_to_u=True) == u_form_tone3


def test_c05_v_to_u_on_mid_position_v_syllable():
    """C05: ü 在音节中部（lüè 的 ü 是韵头，调在 e 上）× v_to_u。"""
    assert to_normal('lüè') == 'lve'
    assert to_normal('lüè', v_to_u=True) == 'lüe'
    assert tone_to_normal('nüè', v_to_u=True) == 'nüe'
    assert tone_to_tone2('nüè', v_to_u=True) == 'nüe4'
    assert tone_to_tone3('nüè', v_to_u=True) == 'nüe4'


# =============================================================================
# C06  D4(声调位置) × D8(neutral_tone_with_five)   ← 高危交叉
#      轻声的 5 应当插在「若有声调则该带调的那个字母」之后
# =============================================================================

@pytest.mark.parametrize('normal, tone2_five, tone3_five', [
    # D4.a 首字母带调位
    ('ai',    'a5i',    'ai5'),
    ('ou',    'o5u',    'ou5'),
    ('an',    'a5n',    'an5'),
    ('er',    'e5r',    'er5'),
    # D4.b 中间字母带调位  ← 最容易出错
    ('shang', 'sha5ng', 'shang5'),
    ('xiao',  'xia5o',  'xiao5'),
    ('zhong', 'zho5ng', 'zhong5'),
    ('huang', 'hua5ng', 'huang5'),
    ('wei',   'we5i',   'wei5'),
    ('you',   'yo5u',   'you5'),
    ('jun',   'ju5n',   'jun5'),
    # D4.c 末字母带调位
    ('de',    'de5',    'de5'),
    ('zi',    'zi5',    'zi5'),
    ('liu',   'liu5',   'liu5'),
    ('gui',   'gui5',   'gui5'),
])
def test_c06_neutral_five_position(normal, tone2_five, tone3_five):
    """C06: 轻声 5 的落点必须遵循标调规则（有 a 标 a，无 a 标 o/e，否则标最后元音）。"""
    assert to_tone2(normal, neutral_tone_with_five=True) == tone2_five
    assert to_tone3(normal, neutral_tone_with_five=True) == tone3_five


@pytest.mark.parametrize('normal, tone2_five, tone3_five', [
    ('shang', 'sha5ng', 'shang5'),
    ('xiao',  'xia5o',  'xiao5'),
    ('de',    'de5',    'de5'),
])
def test_c06_neutral_five_via_tone_to_tone2_and_tone3(normal, tone2_five, tone3_five):
    """C06: 具名函数 tone_to_tone2/tone_to_tone3 的轻声 5 行为应与 to_* 一致。"""
    assert tone_to_tone2(normal, neutral_tone_with_five=True) == tone2_five
    assert tone_to_tone3(normal, neutral_tone_with_five=True) == tone3_five


# =============================================================================
# C07  D5(ü 书写形式) × D7(v_to_u)   ← 高危交叉
#      j/q/x/y 后的 u 在正字法上就写作 u，v_to_u 不应把它变成 ü
# =============================================================================

@pytest.mark.parametrize('tone, tone2, tone3', [
    ('jūn', 'ju1n', 'jun1'),
    ('jǔ',  'ju3',  'ju3'),
    ('qù',  'qu4',  'qu4'),
    ('xué', 'xue2', 'xue2'),
    ('yuè', 'yue4', 'yue4'),
    ('yuǎn', 'yua3n', 'yuan3'),
    ('yún', 'yu2n', 'yun2'),
    ('yǔ',  'yu3',  'yu3'),
])
def test_c07_u_after_jqxy_unaffected_by_v_to_u(tone, tone2, tone3):
    """C07: 整音节风格下，j/q/x/y 后的 u 无论 v_to_u 取何值都保持 u。"""
    assert to_tone2(tone) == tone2
    assert to_tone2(tone, v_to_u=True) == tone2
    assert to_tone3(tone) == tone3
    assert to_tone3(tone, v_to_u=True) == tone3


@pytest.mark.parametrize('src, v_out, u_out', [
    ('lǜ', 'lv', 'lü'),
    ('lv4', 'lv', 'lü'),
    ('lü4', 'lv', 'lü'),
    ('nv3', 'nv', 'nü'),
    ('lve4', 'lve', 'lüe'),
])
def test_c07_literal_v_and_u_umlaut_both_respond_to_v_to_u(src, v_out, u_out):
    """C07: D5.a(ü) 与 D5.b(v) 两种写法在 v_to_u 下应收敛到同一结果。"""
    assert to_normal(src) == v_out
    assert to_normal(src, v_to_u=True) == u_out


def test_c07_v_to_u_does_not_touch_plain_u():
    """C07: D5.d —— 不含 ü 的音节，v_to_u 必须完全无副作用。"""
    assert to_tone2('zhōng', v_to_u=True) == 'zho1ng'
    assert to_tone3('huáng', v_to_u=True) == 'huang2'
    assert to_normal('wǔ', v_to_u=True) == 'wu'
    assert to_normal('gǔ', v_to_u=True) == 'gu'


# =============================================================================
# C08  D5(ü 书写形式) × D8(轻声 5)
# =============================================================================

@pytest.mark.parametrize('normal_in, tone2_five_v, tone2_five_u', [
    ('lv',  'lv5',  'lü5'),
    ('lü',  'lv5',  'lü5'),
    ('nv',  'nv5',  'nü5'),
    ('lve', 'lve5', 'lüe5'),
    ('lüe', 'lve5', 'lüe5'),
])
def test_c08_umlaut_with_neutral_five(normal_in, tone2_five_v, tone2_five_u):
    """C08: ü/v 写法 × 轻声 5（TONE2 与 TONE3 在此都落在末字母后，应一致）。"""
    assert to_tone2(normal_in, neutral_tone_with_five=True) == tone2_five_v
    assert to_tone2(normal_in, neutral_tone_with_five=True, v_to_u=True) == tone2_five_u
    assert to_tone3(normal_in, neutral_tone_with_five=True) == tone2_five_v
    assert to_tone3(normal_in, neutral_tone_with_five=True, v_to_u=True) == tone2_five_u


def test_c08_u_after_jqxy_with_neutral_five():
    """C08: D5.c(j/q/x 后的 u) × 轻声 5，5 仍按标调规则落位且 u 不变形。"""
    assert to_tone2('jun', neutral_tone_with_five=True) == 'ju5n'
    assert to_tone3('jun', neutral_tone_with_five=True) == 'jun5'
    assert to_tone2('xue', neutral_tone_with_five=True) == 'xue5'
    assert to_tone3('xue', neutral_tone_with_five=True) == 'xue5'
    assert to_tone2('yuan', neutral_tone_with_five=True) == 'yua5n'
    assert to_tone3('yuan', neutral_tone_with_five=True) == 'yuan5'


# =============================================================================
# C09  D5(ü 书写形式) × D9(strict)   ← 高危交叉
#      ju/qu/xu/yu/yuan/yun/yue 的韵母本体是 ü 行韵母
# =============================================================================

@pytest.mark.parametrize('src, strict_v, strict_u, loose', [
    ('jūn',  'vn',  'ün',  'un'),
    ('qún',  'vn',  'ün',  'un'),
    ('xūn',  'vn',  'ün',  'un'),
    ('yún',  'vn',  'ün',  'un'),
    ('jǔ',   'v',   'ü',   'u'),
    ('qù',   'v',   'ü',   'u'),
    ('xǔ',   'v',   'ü',   'u'),
    ('yǔ',   'v',   'ü',   'u'),
    ('xué',  've',  'üe',  'ue'),
    ('yuè',  've',  'üe',  'ue'),
    ('yuǎn', 'van', 'üan', 'uan'),
    ('juǎn', 'van', 'üan', 'uan'),
])
def test_c09_finals_of_u_written_umlaut_by_strict(src, strict_v, strict_u, loose):
    """C09: strict=True 时 j/q/x/y 后的 u 应还原为 ü 行韵母；strict=False 保持 u。"""
    assert to_finals(src, strict=True) == strict_v
    assert to_finals(src, strict=True, v_to_u=True) == strict_u
    assert to_finals(src, strict=False) == loose


@pytest.mark.parametrize('src, strict_v, strict_u', [
    ('lǜ',  'v',  'ü'),
    ('nǚ',  'v',  'ü'),
    ('lüè', 've', 'üe'),
    ('nüè', 've', 'üe'),
])
def test_c09_finals_of_literal_umlaut_is_strict_independent(src, strict_v, strict_u):
    """C09: D5.a —— l/n 后本就写 ü，strict 与否韵母都是 ü 行。"""
    assert to_finals(src, strict=True) == strict_v
    assert to_finals(src, strict=False) == strict_v
    assert to_finals(src, strict=True, v_to_u=True) == strict_u
    assert to_finals(src, strict=False, v_to_u=True) == strict_u


def test_c09_finals_tone_of_umlaut_finals():
    """C09 × C15: ü 行韵母 × 带调 FINALS_TONE 风格。"""
    assert to_finals_tone('jūn', strict=True) == 'ǖn'
    assert to_finals_tone('jūn', strict=False) == 'ūn'
    assert to_finals_tone('qù', strict=True) == 'ǜ'
    assert to_finals_tone('qù', strict=False) == 'ù'
    assert to_finals_tone('xué', strict=True) == 'üé'
    assert to_finals_tone('xué', strict=False) == 'ué'
    assert to_finals_tone('lǜ') == 'ǜ'
    assert to_finals_tone('lüè') == 'üè'


def test_c09_finals_tone2_tone3_of_umlaut_finals():
    """C09 × C05: ü 行韵母 × TONE2/TONE3 数字落点 × v_to_u。"""
    assert to_finals_tone2('jūn', strict=True) == 'v1n'
    assert to_finals_tone2('jūn', strict=True, v_to_u=True) == 'ü1n'
    assert to_finals_tone3('jūn', strict=True) == 'vn1'
    assert to_finals_tone3('jūn', strict=True, v_to_u=True) == 'ün1'
    assert to_finals_tone2('jūn', strict=False) == 'u1n'
    assert to_finals_tone3('jūn', strict=False) == 'un1'
    assert to_finals_tone2('yuǎn', strict=True) == 'va3n'
    assert to_finals_tone2('yuǎn', strict=True, v_to_u=True) == 'üa3n'
    assert to_finals_tone3('yuǎn', strict=True) == 'van3'
    assert to_finals_tone2('lüè') == 've4'
    assert to_finals_tone2('lüè', v_to_u=True) == 'üe4'
    assert to_finals_tone3('lüè') == 've4'


# =============================================================================
# C10  D9(strict) × D10(缩写韵母 iu/ui/un)   ← 高危交叉
#      《汉语拼音方案》：iou/uei/uen 前面加声母时写成 iu/ui/un
# =============================================================================

@pytest.mark.parametrize('src, strict_final, loose_final', [
    ('liù',  'iou', 'iu'),
    ('jiǔ',  'iou', 'iu'),
    ('guì',  'uei', 'ui'),
    ('shuì', 'uei', 'ui'),
    ('lún',  'uen', 'un'),
    ('cūn',  'uen', 'un'),
    ('zhǔn', 'uen', 'un'),
])
def test_c10_abbreviated_finals_restored_when_strict(src, strict_final, loose_final):
    """C10: strict=True 还原 iou/uei/uen；strict=False 保留缩写。"""
    assert to_finals(src, strict=True) == strict_final
    assert to_finals(src, strict=False) == loose_final


@pytest.mark.parametrize('src, strict_final, loose_final', [
    ('yǒu', 'iou', 'ou'),
    ('wèi', 'uei', 'ei'),
    ('wèn', 'uen', 'en'),
])
def test_c10_zero_initial_abbreviated_finals(src, strict_final, loose_final):
    """C10 × C13: 缩写韵母 × y/w 开头。strict 下 y/w 不是声母，整体属 iou/uei/uen。"""
    assert to_finals(src, strict=True) == strict_final
    assert to_finals(src, strict=False) == loose_final


# =============================================================================
# C11  D10(缩写韵母) × D4(声调位置)   ← 高危交叉
#      缩写形式里调号标在末字母（liù/guì），还原成 iou/uei 后按规则应落在 o/e 上
# =============================================================================

@pytest.mark.parametrize('src, strict_tone, loose_tone', [
    ('liù',  'iòu', 'iù'),
    ('jiǔ',  'iǒu', 'iǔ'),
    ('guì',  'uèi', 'uì'),
    ('lún',  'uén', 'ún'),
    ('yǒu',  'iǒu', 'ǒu'),
    ('wèi',  'uèi', 'èi'),
])
def test_c11_finals_tone_position_after_restore(src, strict_tone, loose_tone):
    """C11: 还原为 iou/uei/uen 后，调号应落在主要元音 o/e 上。"""
    assert to_finals_tone(src, strict=True) == strict_tone
    assert to_finals_tone(src, strict=False) == loose_tone


@pytest.mark.parametrize('src, strict_t2, strict_t3, loose_t2, loose_t3', [
    ('liù', 'io4u', 'iou4', 'iu4', 'iu4'),
    ('jiǔ', 'io3u', 'iou3', 'iu3', 'iu3'),
    ('guì', 'ue4i', 'uei4', 'ui4', 'ui4'),
    ('lún', 'ue2n', 'uen2', 'u2n', 'un2'),
    ('yǒu', 'io3u', 'iou3', 'o3u', 'ou3'),
    ('wèi', 'ue4i', 'uei4', 'e4i', 'ei4'),
])
def test_c11_finals_tone2_tone3_after_restore(src, strict_t2, strict_t3,
                                              loose_t2, loose_t3):
    """C11: 还原后 TONE2 数字紧跟 o/e，TONE3 数字仍在末尾。"""
    assert to_finals_tone2(src, strict=True) == strict_t2
    assert to_finals_tone3(src, strict=True) == strict_t3
    assert to_finals_tone2(src, strict=False) == loose_t2
    assert to_finals_tone3(src, strict=False) == loose_t3


def test_c11_whole_syllable_keeps_abbreviated_spelling():
    """C11: 整音节风格不做韵母还原，liù 的 TONE2 仍是 liu4 而非 lio4u。"""
    assert to_tone2('liù') == 'liu4'
    assert to_tone3('liù') == 'liu4'
    assert to_tone2('guì') == 'gui4'
    assert to_tone2('lún') == 'lu2n'
    assert to_tone3('lún') == 'lun2'


# =============================================================================
# C12  D10(缩写韵母) × D8(轻声 5)   ← 高危交叉
# =============================================================================

@pytest.mark.parametrize('src, strict_t2, strict_t3, loose_t2, loose_t3', [
    ('liu', 'io5u', 'iou5', 'iu5', 'iu5'),
    ('gui', 'ue5i', 'uei5', 'ui5', 'ui5'),
    ('lun', 'ue5n', 'uen5', 'u5n', 'un5'),
])
def test_c12_abbreviated_finals_with_neutral_five(src, strict_t2, strict_t3,
                                                  loose_t2, loose_t3):
    """C12: 韵母还原 + 轻声 5 叠加，5 的落点应与实调时一致。"""
    assert to_finals_tone2(src, strict=True, neutral_tone_with_five=True) == strict_t2
    assert to_finals_tone3(src, strict=True, neutral_tone_with_five=True) == strict_t3
    assert to_finals_tone2(src, strict=False, neutral_tone_with_five=True) == loose_t2
    assert to_finals_tone3(src, strict=False, neutral_tone_with_five=True) == loose_t3


@pytest.mark.parametrize('src, strict_final, loose_final', [
    ('liu', 'iou', 'iu'),
    ('gui', 'uei', 'ui'),
    ('lun', 'uen', 'un'),
])
def test_c12_abbreviated_finals_without_five(src, strict_final, loose_final):
    """C12: 同样输入但 neutral_tone_with_five=False，不应出现任何数字。"""
    assert to_finals_tone2(src, strict=True) == strict_final
    assert to_finals_tone3(src, strict=True) == strict_final
    assert to_finals_tone2(src, strict=False) == loose_final
    assert to_finals_tone3(src, strict=False) == loose_final


# =============================================================================
# C13  D2(声母类型) × D9(strict)
#      严格拼音方案中 y/w 不是声母
# =============================================================================

@pytest.mark.parametrize('src, strict_initial, loose_initial', [
    # D2.c 双字母声母：strict 无差别
    ('zhōng', 'zh', 'zh'),
    ('chī',   'ch', 'ch'),
    ('shàng', 'sh', 'sh'),
    # D2.b 单字母声母：strict 无差别
    ('jūn',   'j',  'j'),
    ('lǜ',    'l',  'l'),
    ('gěi',   'g',  'g'),
    # D2.a 零声母：两者都为空
    ('ān',    '',   ''),
    ('ér',    '',   ''),
    ('ǒu',    '',   ''),
    # D2.d y/w 开头：strict 下不算声母
    ('yǒu',   '',   'y'),
    ('yī',    '',   'y'),
    ('yuè',   '',   'y'),
    ('wǔ',    '',   'w'),
    ('wèi',   '',   'w'),
    ('wǎng',  '',   'w'),
])
def test_c13_initials_by_strict(src, strict_initial, loose_initial):
    """C13: to_initials 在 strict 两种取值下对不同声母类型的处理。"""
    assert to_initials(src, strict=True) == strict_initial
    assert to_initials(src, strict=False) == loose_initial


@pytest.mark.parametrize('src, strict_final, loose_final', [
    ('yī',   'i',    'i'),
    ('yā',   'ia',   'a'),
    ('yē',   'ie',   'e'),
    ('yān',  'ian',  'an'),
    ('yīn',  'in',   'in'),
    ('yīng', 'ing',  'ing'),
    ('yòng', 'iong', 'ong'),
    ('yáng', 'iang', 'ang'),
    ('wū',   'u',    'u'),
    ('wā',   'ua',   'a'),
    ('wǒ',   'uo',   'o'),
    ('wāi',  'uai',  'ai'),
    ('wán',  'uan',  'an'),
    ('wǎng', 'uang', 'ang'),
])
def test_c13_finals_of_y_w_syllables_by_strict(src, strict_final, loose_final):
    """C13 × C14: y/w 开头音节 × strict —— strict 下 y/w 是 i/u 行韵母的书写形式。"""
    assert to_finals(src, strict=True) == strict_final
    assert to_finals(src, strict=False) == loose_final


# =============================================================================
# C14  D2(声母类型) × D3(韵母结构)
# =============================================================================

@pytest.mark.parametrize('src, initial, final', [
    # D2.c 双字母声母 × D3.g 舌尖元音 i
    ('zhī',   'zh', 'i'),
    ('chí',   'ch', 'i'),
    ('shì',   'sh', 'i'),
    # D2.b 单字母声母 × D3.g
    ('zì',    'z',  'i'),
    ('sì',    's',  'i'),
    ('rì',    'r',  'i'),
    # D2.a 零声母 × D3.d/D3.e 鼻韵尾
    ('ān',    '',   'an'),
    ('ēn',    '',   'en'),
    ('áng',   '',   'ang'),
    # D2.a 零声母 × D3.c 复韵母
    ('ǎi',    '',   'ai'),
    ('ōu',    '',   'ou'),
    ('ào',    '',   'ao'),
    # D2.a 零声母 × D3.f er
    ('ér',    '',   'er'),
    ('èr',    '',   'er'),
    # D2.c 双字母声母 × D3.b 带韵头的复韵母
    ('zhuāng', 'zh', 'uang'),
    ('chuǎi',  'ch', 'uai'),
    # D2.b 单字母声母 × D3.e -ng
    ('xiōng',  'x',  'iong'),
    ('bīng',   'b',  'ing'),
])
def test_c14_initial_and_final_split(src, initial, final):
    """C14: 声母类型 × 韵母结构的切分（strict=True）。"""
    assert to_initials(src, strict=True) == initial
    assert to_finals(src, strict=True) == final


# =============================================================================
# C15  D3(韵母结构) × D4(声调位置)
# =============================================================================

@pytest.mark.parametrize('src, ft, ft2, ft3', [
    # D3.a 单韵母，调在唯一元音上
    ('nǐ',     'ǐ',    'i3',    'i3'),
    ('bù',     'ù',    'u4',    'u4'),
    # D3.b 带韵头复韵母，调在中间（有 a 标 a）
    ('xiǎo',   'iǎo',  'ia3o',  'iao3'),
    ('zhuāng', 'uāng', 'ua1ng', 'uang1'),
    ('huái',   'uái',  'ua2i',  'uai2'),
    # D3.b 带韵头，无 a 则标 o/e
    ('xiōng',  'iōng', 'io1ng', 'iong1'),
    ('lüè',    'üè',   've4',   've4'),
    # D3.c 带韵尾，调在首字母
    ('ǎi',     'ǎi',   'a3i',   'ai3'),
    ('ōu',     'ōu',   'o1u',   'ou1'),
    # D3.d/e 鼻韵尾，调在元音上而非鼻音上
    ('zhōng',  'ōng',  'o1ng',  'ong1'),
    ('shàng',  'àng',  'a4ng',  'ang4'),
    ('bīng',   'īng',  'i1ng',  'ing1'),
    # D3.f er
    ('ér',     'ér',   'e2r',   'er2'),
    # D3.g 舌尖元音 i
    ('zhī',    'ī',    'i1',    'i1'),
])
def test_c15_finals_styles_by_structure_and_position(src, ft, ft2, ft3):
    """C15: 韵母结构 × 声调位置，三种 FINALS 带调风格。"""
    assert to_finals_tone(src, strict=True) == ft
    assert to_finals_tone2(src, strict=True) == ft2
    assert to_finals_tone3(src, strict=True) == ft3


def test_c15_no_vowel_syllables():
    """C15: D3.i 无元音音节（ń/ḿ）× 声调，数字只能落在唯一的辅音字母后。"""
    assert to_normal('ń') == 'n'
    assert to_tone2('ń') == 'n2'
    assert to_tone3('ń') == 'n2'
    assert to_tone('n2') == 'ń'
    assert to_normal('ḿ') == 'm'
    assert to_tone2('ḿ') == 'm2'
    assert to_tone3('ḿ') == 'm2'


# =============================================================================
# C16  D7(v_to_u) × D8(neutral_tone_with_five)
# =============================================================================

@pytest.mark.parametrize('v_to_u, five, expected_t2, expected_t3', [
    (False, False, 'lv',  'lv'),
    (False, True,  'lv5', 'lv5'),
    (True,  False, 'lü',  'lü'),
    (True,  True,  'lü5', 'lü5'),
])
def test_c16_v_to_u_times_neutral_five_full_matrix(v_to_u, five, expected_t2, expected_t3):
    """C16: v_to_u × neutral_tone_with_five 的 2×2 全组合（轻声的 lü）。"""
    assert to_tone2('lü', v_to_u=v_to_u, neutral_tone_with_five=five) == expected_t2
    assert to_tone3('lü', v_to_u=v_to_u, neutral_tone_with_five=five) == expected_t3


@pytest.mark.parametrize('v_to_u, five, expected_t2, expected_t3', [
    (False, False, 'lve',  'lve'),
    (False, True,  'lve5', 'lve5'),
    (True,  False, 'lüe',  'lüe'),
    (True,  True,  'lüe5', 'lüe5'),
])
def test_c16_v_to_u_times_neutral_five_on_lue(v_to_u, five, expected_t2, expected_t3):
    """C16: 同一 2×2 组合，但 ü 位于韵头、5 应落在韵尾 e 之后。"""
    assert to_tone2('lve', v_to_u=v_to_u, neutral_tone_with_five=five) == expected_t2
    assert to_tone3('lve', v_to_u=v_to_u, neutral_tone_with_five=five) == expected_t3


# =============================================================================
# C17  D7(v_to_u) × D9(strict)
# =============================================================================

@pytest.mark.parametrize('strict, v_to_u, expected', [
    (True,  False, 'v'),
    (True,  True,  'ü'),
    (False, False, 'u'),
    (False, True,  'u'),
])
def test_c17_finals_of_ju_strict_times_v_to_u(strict, v_to_u, expected):
    """C17: strict × v_to_u 的 2×2 全组合。
    strict=False 时韵母本就是 u（不是 v），v_to_u 应无影响。"""
    assert to_finals('jǔ', strict=strict, v_to_u=v_to_u) == expected


@pytest.mark.parametrize('strict, v_to_u, expected', [
    (True,  False, 'vn'),
    (True,  True,  'ün'),
    (False, False, 'un'),
    (False, True,  'un'),
])
def test_c17_finals_of_yun_strict_times_v_to_u(strict, v_to_u, expected):
    """C17 × C13: y 开头 + ü 行韵母 + 鼻韵尾，strict × v_to_u 全组合。"""
    assert to_finals('yún', strict=strict, v_to_u=v_to_u) == expected


@pytest.mark.parametrize('strict', [True, False])
@pytest.mark.parametrize('v_to_u, expected', [(False, 've'), (True, 'üe')])
def test_c17_finals_of_lue_is_strict_independent(strict, v_to_u, expected):
    """C17: l 后本就写 ü，两个 strict 取值下 v_to_u 行为必须一致。"""
    assert to_finals('lüè', strict=strict, v_to_u=v_to_u) == expected


# =============================================================================
# C18  D8(neutral_tone_with_five) × D8.L(旧参数 neutral_tone_with_5)
#      文档：传入 neutral_tone_with_5 时将覆盖 neutral_tone_with_five 的值
# =============================================================================

def test_c18_legacy_kwarg_alone_enables_five():
    """C18: 只传旧参数 neutral_tone_with_5=True。"""
    assert to_tone2('shang', neutral_tone_with_5=True) == 'sha5ng'
    assert to_tone3('shang', neutral_tone_with_5=True) == 'shang5'
    assert tone_to_tone2('shang', neutral_tone_with_5=True) == 'sha5ng'
    assert tone_to_tone3('shang', neutral_tone_with_5=True) == 'shang5'


def test_c18_legacy_kwarg_overrides_new_kwarg_true_over_false():
    """C18: neutral_tone_with_five=False 但 neutral_tone_with_5=True → 旧参数胜出。"""
    assert to_tone2('shang', neutral_tone_with_five=False,
                    neutral_tone_with_5=True) == 'sha5ng'
    assert to_tone3('shang', neutral_tone_with_five=False,
                    neutral_tone_with_5=True) == 'shang5'


def test_c18_legacy_kwarg_overrides_new_kwarg_false_over_true():
    """C18: neutral_tone_with_five=True 但 neutral_tone_with_5=False → 旧参数胜出。"""
    assert to_tone2('shang', neutral_tone_with_five=True,
                    neutral_tone_with_5=False) == 'shang'
    assert to_tone3('shang', neutral_tone_with_five=True,
                    neutral_tone_with_5=False) == 'shang'
    assert tone_to_tone2('shang', neutral_tone_with_five=True,
                         neutral_tone_with_5=False) == 'shang'


def test_c18_legacy_kwarg_crossed_with_v_to_u():
    """C18 × C16: 旧参数 × v_to_u。"""
    assert to_tone2('lü', neutral_tone_with_5=True) == 'lv5'
    assert to_tone2('lü', neutral_tone_with_5=True, v_to_u=True) == 'lü5'
    assert to_tone3('lü', neutral_tone_with_5=True, v_to_u=True) == 'lü5'


def test_c18_legacy_kwarg_crossed_with_mid_tone_position():
    """C18 × C06: 旧参数 × 中部落调位置。"""
    assert to_tone2('xiao', neutral_tone_with_5=True) == 'xia5o'
    assert to_tone2('jun', neutral_tone_with_5=True) == 'ju5n'
    assert to_tone3('xiao', neutral_tone_with_5=True) == 'xiao5'


# =============================================================================
# C19  D1(输入风格) × D9(strict)
#      to_initials / to_finals* 声明接受 NORMAL/TONE/TONE2/TONE3 四种输入
# =============================================================================

@pytest.mark.parametrize('src', ['zhōng', 'zho1ng', 'zhong1', 'zhong'])
def test_c19_to_initials_accepts_all_four_styles(src):
    """C19: 四种输入风格 × strict 两取值，声母提取结果一致。"""
    assert to_initials(src, strict=True) == 'zh'
    assert to_initials(src, strict=False) == 'zh'


@pytest.mark.parametrize('src', ['yǒu', 'yo3u', 'you3', 'you'])
def test_c19_to_initials_y_across_styles(src):
    """C19 × C13: y 开头 × 四种输入风格 × strict。"""
    assert to_initials(src, strict=True) == ''
    assert to_initials(src, strict=False) == 'y'


@pytest.mark.parametrize('src', ['zhōng', 'zho1ng', 'zhong1', 'zhong'])
def test_c19_to_finals_accepts_all_four_styles(src):
    """C19: 四种输入风格 → 同一个 NORMAL 韵母。"""
    assert to_finals(src, strict=True) == 'ong'
    assert to_finals(src, strict=False) == 'ong'


@pytest.mark.parametrize('src', ['liù', 'liu4'])
def test_c19_to_finals_strict_restore_across_styles(src):
    """C19 × C10: TONE 与 TONE2/TONE3 输入（liu4 两者同形）都应触发 iou 还原。"""
    assert to_finals(src, strict=True) == 'iou'
    assert to_finals(src, strict=False) == 'iu'
    assert to_finals_tone(src, strict=True) == 'iòu'
    assert to_finals_tone2(src, strict=True) == 'io4u'
    assert to_finals_tone3(src, strict=True) == 'iou4'


@pytest.mark.parametrize('src', ['zhōng', 'zho1ng', 'zhong1'])
def test_c19_finals_tone_styles_across_input_styles(src):
    """C19: 三种带调输入风格 → 同一 FINALS_TONE / FINALS_TONE2 / FINALS_TONE3。"""
    assert to_finals_tone(src) == 'ōng'
    assert to_finals_tone2(src) == 'o1ng'
    assert to_finals_tone3(src) == 'ong1'


@pytest.mark.parametrize('src', ['lüè', 'lve4', 'lüe4'])
def test_c19_finals_of_umlaut_across_styles(src):
    """C19 × C02 × C07: ü/v 三种写法的输入 × FINALS 系列 × v_to_u。"""
    assert to_finals(src) == 've'
    assert to_finals(src, v_to_u=True) == 'üe'
    assert to_finals_tone(src) == 'üè'
    assert to_finals_tone2(src, v_to_u=True) == 'üe4'
    assert to_finals_tone3(src, v_to_u=True) == 'üe4'


def test_c19_finals_from_normal_input_with_neutral_five():
    """C19 × C06: NORMAL 输入 × FINALS_TONE2/3 × 轻声 5。"""
    assert to_finals_tone2('shang', neutral_tone_with_five=True) == 'a5ng'
    assert to_finals_tone3('shang', neutral_tone_with_five=True) == 'ang5'
    assert to_finals_tone2('xiao', neutral_tone_with_five=True) == 'ia5o'
    assert to_finals_tone3('xiao', neutral_tone_with_five=True) == 'iao5'
    assert to_finals_tone2('de', neutral_tone_with_five=True) == 'e5'


# =============================================================================
# C20  D3(韵母结构) × D9(strict)
# =============================================================================

@pytest.mark.parametrize('src, strict_final, loose_final', [
    # D3.f er —— 零声母，strict 与否都是 er
    ('ér',   'er',   'er'),
    ('èr',   'er',   'er'),
    # D3.g 舌尖元音 i —— strict 与否都是 i
    ('zhī',  'i',    'i'),
    ('sì',   'i',    'i'),
    # D3.e iong —— y 开头时 strict 才是 iong
    ('yòng', 'iong', 'ong'),
    ('xiōng', 'iong', 'iong'),
    # D3.d in/ing —— y 开头时两者恰好相同
    ('yīn',  'in',   'in'),
    ('yīng', 'ing',  'ing'),
    # D3.a 单韵母 —— 零声母
    ('ā',    'a',    'a'),
    ('ò',    'o',    'o'),
    ('è',    'e',    'e'),
])
def test_c20_final_structure_by_strict(src, strict_final, loose_final):
    """C20: 各类韵母结构在 strict 两个取值下的表现。"""
    assert to_finals(src, strict=True) == strict_final
    assert to_finals(src, strict=False) == loose_final


def test_c20_er_finals_tone_styles():
    """C20 × C15: er 的带调 FINALS 风格，调号在 e 上，r 是韵尾。"""
    assert to_finals_tone('ér') == 'ér'
    assert to_finals_tone2('ér') == 'e2r'
    assert to_finals_tone3('ér') == 'er2'
    assert to_finals_tone2('èr') == 'e4r'
    assert to_finals_tone3('èr') == 'er4'


# =============================================================================
# C22  D2(声母类型) × D4(声调位置)
# =============================================================================

@pytest.mark.parametrize('tone, tone2, tone3', [
    # D2.a 零声母 × D4.a 首字母带调
    ('ān',  'a1n',  'an1'),
    ('ér',  'e2r',  'er2'),
    ('ǒu',  'o3u',  'ou3'),
    ('àng', 'a4ng', 'ang4'),
    ('ǎi',  'a3i',  'ai3'),
    ('ō',   'o1',   'o1'),
    # D2.d y/w 开头 × D4.b 中间带调
    ('yòu',  'yo4u',  'you4'),
    ('wèi',  'we4i',  'wei4'),
    ('wén',  'we2n',  'wen2'),
    ('yīng', 'yi1ng', 'ying1'),
    ('wǎng', 'wa3ng', 'wang3'),
    ('yuǎn', 'yua3n', 'yuan3'),
    # D2.d y/w 开头 × D4.c 末字母带调
    ('wǔ',  'wu3',  'wu3'),
    ('wǒ',  'wo3',  'wo3'),
    ('yī',  'yi1',  'yi1'),
    ('yuè', 'yue4', 'yue4'),
    # D2.c 双字母声母 × D4.b
    ('zhuāng', 'zhua1ng', 'zhuang1'),
    ('chuǎi',  'chua3i',  'chuai3'),
])
def test_c22_initial_type_times_tone_position(tone, tone2, tone3):
    """C22: 声母长度/类型不应影响数字插入点（应由韵母的标调规则决定）。"""
    assert to_tone2(tone) == tone2
    assert to_tone3(tone) == tone3
    assert to_tone(tone2) == tone
    assert to_tone(tone3) == tone
    assert to_normal(tone) == to_normal(tone3)


# =============================================================================
# 往返一致性（跨维度的整体约束，不依赖单点期望值）
# =============================================================================

_ROUNDTRIP_TONE = [
    'zhōng', 'xiǎo', 'huáng', 'liù', 'guì', 'lún', 'nǐ', 'ér', 'ān', 'ǒu',
    'lǜ', 'nǚ', 'lüè', 'nüè', 'jūn', 'qù', 'xué', 'yuè', 'yuǎn', 'yún',
    'wǔ', 'wèi', 'yòu', 'zhī', 'sì', 'ǎi', 'shàng', 'xiōng', 'bīng', 'zhuāng',
]


@pytest.mark.parametrize('tone', _ROUNDTRIP_TONE)
def test_roundtrip_tone_tone2_tone(tone):
    """TONE → TONE2 → TONE 必须回到原值（覆盖 D2×D3×D4×D5 的组合样本）。"""
    assert to_tone(to_tone2(tone)) == tone
    assert tone2_to_tone(tone_to_tone2(tone)) == tone


@pytest.mark.parametrize('tone', _ROUNDTRIP_TONE)
def test_roundtrip_tone_tone3_tone(tone):
    """TONE → TONE3 → TONE 必须回到原值。"""
    assert to_tone(to_tone3(tone)) == tone
    assert tone3_to_tone(tone_to_tone3(tone)) == tone


@pytest.mark.parametrize('tone', _ROUNDTRIP_TONE)
def test_roundtrip_tone2_tone3_tone2(tone):
    """TONE2 ↔ TONE3 互转必须可逆。"""
    t2 = to_tone2(tone)
    t3 = to_tone3(tone)
    assert tone2_to_tone3(t2) == t3
    assert tone3_to_tone2(t3) == t2


@pytest.mark.parametrize('tone', _ROUNDTRIP_TONE)
def test_normal_is_style_invariant(tone):
    """四条路径得到的 NORMAL 必须一致（v_to_u 两个取值分别自洽）。"""
    t2 = to_tone2(tone)
    t3 = to_tone3(tone)
    assert to_normal(tone) == to_normal(t2) == to_normal(t3)
    assert (to_normal(tone, v_to_u=True)
            == to_normal(t2, v_to_u=True)
            == to_normal(t3, v_to_u=True))


@pytest.mark.parametrize('tone', _ROUNDTRIP_TONE)
def test_initials_plus_finals_reconstruct_normal(tone):
    """C13 × C09: strict=False 下声母 + 韵母应拼回 NORMAL 音节的字面拼写。
    （v_to_u=True 让 ü 保持 ü，避免与 NORMAL 默认的 v 写法冲突。）"""
    normal = to_normal(tone, v_to_u=True)
    initial = to_initials(tone, strict=False)
    final = to_finals(tone, strict=False, v_to_u=True)
    assert initial + final == normal
