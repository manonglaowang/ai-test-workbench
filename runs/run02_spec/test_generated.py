# -*- coding: utf-8 -*-
"""pypinyin.contrib.tone_convert 的规格驱动测试。

本文件的所有期望值都是根据 SPEC.md 中的函数签名/文档说明，
结合《汉语拼音方案》与常见拼音标注规范推导出来的，
不参考任何实现代码 / git 历史 / issue。

术语约定（与 SPEC.md 一致）：
  NORMAL : zhong
  TONE   : zhōng     声调符号标在字母上
  TONE2  : zho1ng    数字紧跟在“带声调的那个韵母字母”后面
  TONE3  : zhong1    数字放在整个音节末尾

关键规范约定：
  * 标调位置：有 a 标 a；没有 a，o/e 择其一；iu / ui 标在后一个字母上。
    因此 TONE2 的数字位置由“标调字母”决定（hǎo -> ha3o，而不是 hao3）。
  * v 与 ü 等价书写；参数 v_to_u=True 表示输出用 ü，
    v_to_u=False（默认）表示输出用 v。
  * j/q/x 后的 ü 习惯写作 u，所以 ju/qu/xu 的“书写形式”里没有 ü，
    但按《汉语拼音方案》其韵母仍是 ü（strict=True 时体现出来）。
  * 轻声用数字 5 表示，也可以省略不标。
  * strict=True 遵照《汉语拼音方案》：y/w 不是声母，
    iu->iou、ui->uei、un->uen，ju/qu/xu->jü/qü/xü，
    yi->i、ye->ie、yu->ü、wu->u、wo->uo、yuan->üan、yun->ün、yong->iong 等。
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
# to_normal
# ---------------------------------------------------------------------------


@pytest.mark.parametrize('tone,expected', [
    ('zhōng', 'zhong'),
    ('hǎo', 'hao'),
    ('nǐ', 'ni'),
    ('ér', 'er'),
    ('ān', 'an'),
    ('yīng', 'ying'),
    ('wǒ', 'wo'),
    ('jué', 'jue'),
    ('qún', 'qun'),
    ('liù', 'liu'),
    ('guī', 'gui'),
    ('xiǎng', 'xiang'),
    ('zhuāng', 'zhuang'),
    ('yuǎn', 'yuan'),
])
def test_to_normal_from_tone_strips_tone_marks(tone, expected):
    assert to_normal(tone) == expected


@pytest.mark.parametrize('tone2,expected', [
    ('zho1ng', 'zhong'),
    ('ha3o', 'hao'),
    ('e2r', 'er'),
    ('a1n', 'an'),
    ('yi1ng', 'ying'),
    ('xia3ng', 'xiang'),
])
def test_to_normal_from_tone2_strips_tone_digits(tone2, expected):
    assert to_normal(tone2) == expected


@pytest.mark.parametrize('tone3,expected', [
    ('zhong1', 'zhong'),
    ('hao3', 'hao'),
    ('er2', 'er'),
    ('an1', 'an'),
    ('ying1', 'ying'),
    ('xiang3', 'xiang'),
])
def test_to_normal_from_tone3_strips_tone_digits(tone3, expected):
    assert to_normal(tone3) == expected


def test_to_normal_is_idempotent_on_normal_input():
    assert to_normal('zhong') == 'zhong'
    assert to_normal('shang') == 'shang'
    assert to_normal('er') == 'er'


def test_to_normal_neutral_tone_digit_five_is_dropped():
    # 轻声的 5 只是标记，NORMAL 风格里不应保留
    assert to_normal('sha5ng') == 'shang'
    assert to_normal('shang5') == 'shang'
    assert to_normal('de5') == 'de'


@pytest.mark.parametrize('pinyin,expected_v,expected_u', [
    ('lüè', 'lve', 'lüe'),
    ('lǘ', 'lv', 'lü'),
    ('nǚ', 'nv', 'nü'),
    ('nüè', 'nve', 'nüe'),
    ('lǜ', 'lv', 'lü'),
])
def test_to_normal_v_to_u_switch_on_tone_input(pinyin, expected_v, expected_u):
    assert to_normal(pinyin) == expected_v
    assert to_normal(pinyin, v_to_u=True) == expected_u


@pytest.mark.parametrize('pinyin', ['lve4', 'lüe4', 'lve', 'lüe'])
def test_to_normal_v_and_u_spellings_are_equivalent_inputs(pinyin):
    # v 和 ü 指同一个韵母，输入用哪种写法都不应影响输出
    assert to_normal(pinyin) == 'lve'
    assert to_normal(pinyin, v_to_u=True) == 'lüe'


def test_to_normal_jqx_u_is_not_turned_into_v():
    # j/q/x 后面的 ü 写作 u，NORMAL 风格保持书写形式 ju/qu/xu
    assert to_normal('jū') == 'ju'
    assert to_normal('qù') == 'qu'
    assert to_normal('xǔ') == 'xu'
    assert to_normal('jué') == 'jue'
    assert to_normal('jū', v_to_u=True) == 'ju'


# ---------------------------------------------------------------------------
# to_tone
# ---------------------------------------------------------------------------


@pytest.mark.parametrize('tone2,expected', [
    ('zho1ng', 'zhōng'),
    ('ha3o', 'hǎo'),
    ('ni3', 'nǐ'),
    ('e2r', 'ér'),
    ('a1n', 'ān'),
    ('yi1ng', 'yīng'),
    ('wo3', 'wǒ'),
    ('jue2', 'jué'),
    ('qu2n', 'qún'),
    ('liu4', 'liù'),
    ('gui1', 'guī'),
    ('xia3ng', 'xiǎng'),
    ('zhua1ng', 'zhuāng'),
    ('yua3n', 'yuǎn'),
])
def test_to_tone_from_tone2(tone2, expected):
    assert to_tone(tone2) == expected


@pytest.mark.parametrize('tone3,expected', [
    ('zhong1', 'zhōng'),
    ('hao3', 'hǎo'),
    ('ni3', 'nǐ'),
    ('er2', 'ér'),
    ('an1', 'ān'),
    ('ying1', 'yīng'),
    ('wo3', 'wǒ'),
    ('jue2', 'jué'),
    ('qun2', 'qún'),
    ('liu4', 'liù'),
    ('gui1', 'guī'),
    ('xiang3', 'xiǎng'),
    ('zhuang1', 'zhuāng'),
    ('yuan3', 'yuǎn'),
])
def test_to_tone_from_tone3(tone3, expected):
    assert to_tone(tone3) == expected


@pytest.mark.parametrize('pinyin,expected', [
    ('lve4', 'lüè'),
    ('lüe4', 'lüè'),
    ('nv3', 'nǚ'),
    ('nü3', 'nǚ'),
    ('lv2', 'lǘ'),
    ('lv4', 'lǜ'),
    ('nve4', 'nüè'),
])
def test_to_tone_restores_u_umlaut_for_v_spelling(pinyin, expected):
    # TONE 风格必须写成 ü（带调），不能保留 v
    assert to_tone(pinyin) == expected


def test_to_tone_all_four_tones_on_same_syllable():
    assert to_tone('ma1') == 'mā'
    assert to_tone('ma2') == 'má'
    assert to_tone('ma3') == 'mǎ'
    assert to_tone('ma4') == 'mà'


def test_to_tone_neutral_tone_has_no_mark():
    assert to_tone('ma5') == 'ma'
    assert to_tone('sha5ng') == 'shang'
    assert to_tone('shang5') == 'shang'


def test_to_tone_is_idempotent_on_tone_input():
    assert to_tone('zhōng') == 'zhōng'
    assert to_tone('lüè') == 'lüè'
    assert to_tone('shang') == 'shang'


# ---------------------------------------------------------------------------
# to_tone2 / to_tone3 —— 数字位置是两者的核心差异
# ---------------------------------------------------------------------------


@pytest.mark.parametrize('tone,tone2,tone3', [
    ('zhōng', 'zho1ng', 'zhong1'),
    ('hǎo', 'ha3o', 'hao3'),
    ('ér', 'e2r', 'er2'),
    ('ān', 'a1n', 'an1'),
    ('ǎi', 'a3i', 'ai3'),
    ('òu', 'o4u', 'ou4'),
    ('gěi', 'ge3i', 'gei3'),
    ('xiǎng', 'xia3ng', 'xiang3'),
    ('zhuāng', 'zhua1ng', 'zhuang1'),
    ('yīng', 'yi1ng', 'ying1'),
    ('jiǒng', 'jio3ng', 'jiong3'),
    ('guǎi', 'gua3i', 'guai3'),
    ('yuǎn', 'yua3n', 'yuan3'),
    ('qún', 'qu2n', 'qun2'),
    ('huáng', 'hua2ng', 'huang2'),
])
def test_to_tone2_and_to_tone3_digit_position_differs(tone, tone2, tone3):
    # TONE2: 数字紧跟带调字母；TONE3: 数字在音节末尾
    assert to_tone2(tone) == tone2
    assert to_tone3(tone) == tone3


@pytest.mark.parametrize('tone,expected', [
    ('nǐ', 'ni3'),
    ('wǒ', 'wo3'),
    ('jué', 'jue2'),
    ('xuě', 'xue3'),
    ('liù', 'liu4'),
    ('guī', 'gui1'),
    ('duǒ', 'duo3'),
    ('mā', 'ma1'),
])
def test_to_tone2_equals_to_tone3_when_toned_letter_is_last(tone, expected):
    # 带调字母正好在音节末尾时，两种风格结果相同
    assert to_tone2(tone) == expected
    assert to_tone3(tone) == expected


def test_to_tone2_tone_mark_on_iu_and_ui_goes_to_last_vowel():
    # 规范：iu 标在 u 上，ui 标在 i 上
    assert to_tone2('liù') == 'liu4'
    assert to_tone3('liù') == 'liu4'
    assert to_tone2('guī') == 'gui1'
    assert to_tone3('guī') == 'gui1'
    assert to_tone2('huì') == 'hui4'


def test_to_tone2_from_tone3_input():
    assert to_tone2('zhong1') == 'zho1ng'
    assert to_tone2('hao3') == 'ha3o'
    assert to_tone2('xiang3') == 'xia3ng'


def test_to_tone3_from_tone2_input():
    assert to_tone3('zho1ng') == 'zhong1'
    assert to_tone3('ha3o') == 'hao3'
    assert to_tone3('xia3ng') == 'xiang3'


def test_to_tone2_and_to_tone3_are_idempotent_on_own_style():
    assert to_tone2('zho1ng') == 'zho1ng'
    assert to_tone3('zhong1') == 'zhong1'


def test_to_tone2_neutral_tone_not_marked_by_default():
    assert to_tone2('shang') == 'shang'
    assert to_tone2('de') == 'de'
    assert to_tone3('shang') == 'shang'
    assert to_tone3('de') == 'de'


def test_to_tone2_neutral_tone_with_five_puts_5_after_main_vowel():
    assert to_tone2('shang', neutral_tone_with_five=True) == 'sha5ng'
    assert to_tone2('de', neutral_tone_with_five=True) == 'de5'
    assert to_tone2('le', neutral_tone_with_five=True) == 'le5'
    assert to_tone2('zi', neutral_tone_with_five=True) == 'zi5'
    assert to_tone2('men', neutral_tone_with_five=True) == 'me5n'


def test_to_tone3_neutral_tone_with_five_puts_5_at_the_end():
    assert to_tone3('shang', neutral_tone_with_five=True) == 'shang5'
    assert to_tone3('de', neutral_tone_with_five=True) == 'de5'
    assert to_tone3('zi', neutral_tone_with_five=True) == 'zi5'
    assert to_tone3('men', neutral_tone_with_five=True) == 'men5'


def test_to_tone2_neutral_tone_with_five_does_not_touch_toned_syllable():
    assert to_tone2('zhōng', neutral_tone_with_five=True) == 'zho1ng'
    assert to_tone3('zhōng', neutral_tone_with_five=True) == 'zhong1'


def test_to_tone2_legacy_neutral_tone_with_5_kwarg():
    assert to_tone2('shang', neutral_tone_with_5=True) == 'sha5ng'
    assert to_tone3('shang', neutral_tone_with_5=True) == 'shang5'


def test_to_tone2_legacy_kwarg_overrides_new_kwarg():
    # 文档：传入 neutral_tone_with_5 时将覆盖 neutral_tone_with_five 的值
    assert to_tone2('shang', neutral_tone_with_five=False,
                    neutral_tone_with_5=True) == 'sha5ng'
    assert to_tone2('shang', neutral_tone_with_five=True,
                    neutral_tone_with_5=False) == 'shang'
    assert to_tone3('shang', neutral_tone_with_five=False,
                    neutral_tone_with_5=True) == 'shang5'
    assert to_tone3('shang', neutral_tone_with_five=True,
                    neutral_tone_with_5=False) == 'shang'


@pytest.mark.parametrize('tone,t2_v,t2_u,t3_v,t3_u', [
    ('lüè', 'lve4', 'lüe4', 'lve4', 'lüe4'),
    ('nüè', 'nve4', 'nüe4', 'nve4', 'nüe4'),
    ('lǘ', 'lv2', 'lü2', 'lv2', 'lü2'),
    ('nǚ', 'nv3', 'nü3', 'nv3', 'nü3'),
    ('lǜ', 'lv4', 'lü4', 'lv4', 'lü4'),
])
def test_to_tone2_to_tone3_v_to_u_switch(tone, t2_v, t2_u, t3_v, t3_u):
    assert to_tone2(tone) == t2_v
    assert to_tone2(tone, v_to_u=True) == t2_u
    assert to_tone3(tone) == t3_v
    assert to_tone3(tone, v_to_u=True) == t3_u


def test_to_tone2_jqx_u_stays_u_regardless_of_v_to_u():
    # ju/qu/xu 的书写形式里没有 ü，v_to_u 不应把它改写成 v/ü
    assert to_tone2('jú') == 'ju2'
    assert to_tone2('jú', v_to_u=True) == 'ju2'
    assert to_tone3('qù') == 'qu4'
    assert to_tone3('qù', v_to_u=True) == 'qu4'
    assert to_tone3('xǔ', v_to_u=True) == 'xu3'
    assert to_tone2('juǎn') == 'jua3n'
    assert to_tone3('juǎn') == 'juan3'
    assert to_tone2('qún', v_to_u=True) == 'qu2n'


# ---------------------------------------------------------------------------
# to_initials
# ---------------------------------------------------------------------------


@pytest.mark.parametrize('pinyin,expected', [
    ('zhōng', 'zh'),
    ('chī', 'ch'),
    ('shī', 'sh'),
    ('nǐ', 'n'),
    ('lǜ', 'l'),
    ('jū', 'j'),
    ('qī', 'q'),
    ('xī', 'x'),
    ('zì', 'z'),
    ('cì', 'c'),
    ('sì', 's'),
    ('rì', 'r'),
    ('bā', 'b'),
    ('pā', 'p'),
    ('mā', 'm'),
    ('fā', 'f'),
    ('dā', 'd'),
    ('tā', 't'),
    ('gā', 'g'),
    ('kā', 'k'),
    ('hā', 'h'),
])
def test_to_initials_normal_initials(pinyin, expected):
    assert to_initials(pinyin) == expected
    assert to_initials(pinyin, strict=False) == expected


@pytest.mark.parametrize('pinyin', ['ān', 'ér', 'ō', 'ài', 'ēn'])
def test_to_initials_zero_initial_syllables(pinyin):
    assert to_initials(pinyin) == ''
    assert to_initials(pinyin, strict=False) == ''


@pytest.mark.parametrize('pinyin,nonstrict', [
    ('yīng', 'y'),
    ('yī', 'y'),
    ('yuán', 'y'),
    ('yǔ', 'y'),
    ('wǒ', 'w'),
    ('wǔ', 'w'),
    ('wēn', 'w'),
])
def test_to_initials_y_and_w_are_not_initials_in_strict_mode(pinyin, nonstrict):
    # 《汉语拼音方案》里 y/w 不是声母
    assert to_initials(pinyin, strict=True) == ''
    assert to_initials(pinyin, strict=False) == nonstrict


@pytest.mark.parametrize('pinyin', ['zhōng', 'zho1ng', 'zhong1', 'zhong'])
def test_to_initials_accepts_all_input_styles(pinyin):
    assert to_initials(pinyin) == 'zh'


# ---------------------------------------------------------------------------
# to_finals
# ---------------------------------------------------------------------------


@pytest.mark.parametrize('pinyin', ['zhōng', 'zho1ng', 'zhong1', 'zhong'])
def test_to_finals_accepts_all_input_styles(pinyin):
    assert to_finals(pinyin) == 'ong'


@pytest.mark.parametrize('pinyin,expected', [
    ('bā', 'a'),
    ('bō', 'o'),
    ('dé', 'e'),
    ('ài', 'ai'),
    ('èi', 'ei'),
    ('ào', 'ao'),
    ('ǒu', 'ou'),
    ('ān', 'an'),
    ('ēn', 'en'),
    ('āng', 'ang'),
    ('ér', 'er'),
    ('nǐ', 'i'),
    ('xiǎng', 'iang'),
    ('hǎo', 'ao'),
    ('zhī', 'i'),
    ('cí', 'i'),
    ('shì', 'i'),
])
def test_to_finals_simple_finals(pinyin, expected):
    assert to_finals(pinyin) == expected


@pytest.mark.parametrize('pinyin,strict_expected,loose_expected', [
    # iu -> iou, ui -> uei, un -> uen （strict 还原完整韵母）
    ('liù', 'iou', 'iu'),
    ('jiǔ', 'iou', 'iu'),
    ('guī', 'uei', 'ui'),
    ('huì', 'uei', 'ui'),
    ('zhǔn', 'uen', 'un'),
    ('lùn', 'uen', 'un'),
])
def test_to_finals_strict_restores_full_finals(pinyin, strict_expected,
                                               loose_expected):
    assert to_finals(pinyin, strict=True) == strict_expected
    assert to_finals(pinyin, strict=False) == loose_expected


@pytest.mark.parametrize('pinyin,strict_expected,loose_expected', [
    ('yī', 'i', 'i'),
    ('yā', 'ia', 'a'),
    ('yě', 'ie', 'e'),
    ('yǒu', 'iou', 'ou'),
    ('yīn', 'in', 'in'),
    ('yīng', 'ing', 'ing'),
    ('yòng', 'iong', 'ong'),
    ('wǔ', 'u', 'u'),
    ('wā', 'ua', 'a'),
    ('wǒ', 'uo', 'o'),
    ('wēn', 'uen', 'en'),
    ('wēng', 'ueng', 'eng'),
])
def test_to_finals_strict_handles_y_and_w_syllables(pinyin, strict_expected,
                                                    loose_expected):
    assert to_finals(pinyin, strict=True) == strict_expected
    assert to_finals(pinyin, strict=False) == loose_expected


@pytest.mark.parametrize('pinyin,strict_v,strict_u,loose', [
    # j/q/x 后的 u 实际是 ü，strict 模式应还原
    ('jū', 'v', 'ü', 'u'),
    ('qù', 'v', 'ü', 'u'),
    ('xǔ', 'v', 'ü', 'u'),
    ('jué', 've', 'üe', 'ue'),
    ('quē', 've', 'üe', 'ue'),
    ('xuě', 've', 'üe', 'ue'),
    ('juǎn', 'van', 'üan', 'uan'),
    ('qún', 'vn', 'ün', 'un'),
    ('yuè', 've', 'üe', 'ue'),
    ('yuán', 'van', 'üan', 'uan'),
    ('yūn', 'vn', 'ün', 'un'),
    ('yǔ', 'v', 'ü', 'u'),
])
def test_to_finals_strict_restores_u_umlaut_after_jqxy(pinyin, strict_v,
                                                       strict_u, loose):
    assert to_finals(pinyin, strict=True) == strict_v
    assert to_finals(pinyin, strict=True, v_to_u=True) == strict_u
    assert to_finals(pinyin, strict=False) == loose


@pytest.mark.parametrize('pinyin,expected_v,expected_u', [
    ('lüè', 've', 'üe'),
    ('nǚ', 'v', 'ü'),
    ('lǘ', 'v', 'ü'),
    ('nüè', 've', 'üe'),
    ('lve4', 've', 'üe'),
    ('lüe4', 've', 'üe'),
])
def test_to_finals_v_to_u_switch(pinyin, expected_v, expected_u):
    assert to_finals(pinyin) == expected_v
    assert to_finals(pinyin, v_to_u=True) == expected_u


# ---------------------------------------------------------------------------
# to_finals_tone / to_finals_tone2 / to_finals_tone3
# ---------------------------------------------------------------------------


@pytest.mark.parametrize('pinyin,expected', [
    ('zhōng', 'ōng'),
    ('hǎo', 'ǎo'),
    ('nǐ', 'ǐ'),
    ('ér', 'ér'),
    ('xiǎng', 'iǎng'),
    ('zhī', 'ī'),
    ('bā', 'ā'),
])
def test_to_finals_tone_keeps_tone_mark(pinyin, expected):
    assert to_finals_tone(pinyin) == expected


@pytest.mark.parametrize('pinyin', ['zhōng', 'zho1ng', 'zhong1'])
def test_to_finals_tone_accepts_all_toned_styles(pinyin):
    assert to_finals_tone(pinyin) == 'ōng'


def test_to_finals_tone_strict_moves_mark_to_restored_vowel():
    # iu -> iou，按规范调号落在 o 上；ui -> uei，调号落在 e 上
    assert to_finals_tone('liù', strict=True) == 'iòu'
    assert to_finals_tone('liù', strict=False) == 'iù'
    assert to_finals_tone('guī', strict=True) == 'uēi'
    assert to_finals_tone('guī', strict=False) == 'uī'
    assert to_finals_tone('zhǔn', strict=True) == 'uěn'
    assert to_finals_tone('zhǔn', strict=False) == 'ǔn'


def test_to_finals_tone_uses_u_umlaut_always():
    # FINALS_TONE 风格没有 v_to_u 参数，只能用 ü
    assert to_finals_tone('lüè') == 'üè'
    assert to_finals_tone('nǚ') == 'ǚ'
    assert to_finals_tone('jū', strict=True) == 'ǖ'
    assert to_finals_tone('jué', strict=True) == 'üé'
    assert to_finals_tone('jué', strict=False) == 'ué'
    assert to_finals_tone('yuán', strict=True) == 'üán'
    assert to_finals_tone('qún', strict=True) == 'ǘn'


@pytest.mark.parametrize('pinyin,tone2,tone3', [
    ('zhōng', 'o1ng', 'ong1'),
    ('hǎo', 'a3o', 'ao3'),
    ('xiǎng', 'ia3ng', 'iang3'),
    ('nǐ', 'i3', 'i3'),
    ('ér', 'e2r', 'er2'),
    ('zhuāng', 'ua1ng', 'uang1'),
    ('yīng', 'i1ng', 'ing1'),
])
def test_to_finals_tone2_and_tone3_digit_position(pinyin, tone2, tone3):
    assert to_finals_tone2(pinyin) == tone2
    assert to_finals_tone3(pinyin) == tone3


@pytest.mark.parametrize('pinyin', ['zhōng', 'zho1ng', 'zhong1'])
def test_to_finals_tone2_tone3_accept_all_toned_styles(pinyin):
    assert to_finals_tone2(pinyin) == 'o1ng'
    assert to_finals_tone3(pinyin) == 'ong1'


def test_to_finals_tone2_strict_full_final_digit_follows_toned_letter():
    assert to_finals_tone2('liù', strict=True) == 'io4u'
    assert to_finals_tone2('liù', strict=False) == 'iu4'
    assert to_finals_tone3('liù', strict=True) == 'iou4'
    assert to_finals_tone3('liù', strict=False) == 'iu4'
    assert to_finals_tone2('guī', strict=True) == 'ue1i'
    assert to_finals_tone2('guī', strict=False) == 'u1i'
    assert to_finals_tone3('guī', strict=True) == 'uei1'
    assert to_finals_tone3('guī', strict=False) == 'ui1'
    assert to_finals_tone2('zhǔn', strict=True) == 'ue3n'
    assert to_finals_tone3('zhǔn', strict=True) == 'uen3'


@pytest.mark.parametrize('pinyin,t2_v,t2_u,t3_v,t3_u', [
    ('lüè', 've4', 'üe4', 've4', 'üe4'),
    ('nǚ', 'v3', 'ü3', 'v3', 'ü3'),
    ('jū', 'v1', 'ü1', 'v1', 'ü1'),
    ('jué', 've2', 'üe2', 've2', 'üe2'),
    ('juǎn', 'va3n', 'üa3n', 'van3', 'üan3'),
    ('qún', 'v2n', 'ü2n', 'vn2', 'ün2'),
    ('yuán', 'va2n', 'üa2n', 'van2', 'üan2'),
])
def test_to_finals_tone2_tone3_v_to_u_switch_strict(pinyin, t2_v, t2_u,
                                                    t3_v, t3_u):
    assert to_finals_tone2(pinyin, strict=True) == t2_v
    assert to_finals_tone2(pinyin, strict=True, v_to_u=True) == t2_u
    assert to_finals_tone3(pinyin, strict=True) == t3_v
    assert to_finals_tone3(pinyin, strict=True, v_to_u=True) == t3_u


def test_to_finals_tone2_tone3_neutral_tone_with_five():
    assert to_finals_tone2('shang') == 'ang'
    assert to_finals_tone3('shang') == 'ang'
    assert to_finals_tone2('shang', neutral_tone_with_five=True) == 'a5ng'
    assert to_finals_tone3('shang', neutral_tone_with_five=True) == 'ang5'
    assert to_finals_tone2('de', neutral_tone_with_five=True) == 'e5'
    assert to_finals_tone3('de', neutral_tone_with_five=True) == 'e5'
    assert to_finals_tone2('zi', neutral_tone_with_five=True) == 'i5'


def test_to_finals_tone2_neutral_flag_does_not_affect_toned_syllable():
    assert to_finals_tone2('zhōng', neutral_tone_with_five=True) == 'o1ng'
    assert to_finals_tone3('zhōng', neutral_tone_with_five=True) == 'ong1'


# ---------------------------------------------------------------------------
# tone_to_normal / tone_to_tone2 / tone_to_tone3
# ---------------------------------------------------------------------------


@pytest.mark.parametrize('tone,expected', [
    ('zhōng', 'zhong'),
    ('hǎo', 'hao'),
    ('ér', 'er'),
    ('shang', 'shang'),
    ('jué', 'jue'),
])
def test_tone_to_normal_basic(tone, expected):
    assert tone_to_normal(tone) == expected


def test_tone_to_normal_v_to_u():
    assert tone_to_normal('lüè') == 'lve'
    assert tone_to_normal('lüè', v_to_u=True) == 'lüe'
    assert tone_to_normal('nǚ') == 'nv'
    assert tone_to_normal('nǚ', v_to_u=True) == 'nü'


@pytest.mark.parametrize('tone,tone2,tone3', [
    ('zhōng', 'zho1ng', 'zhong1'),
    ('hǎo', 'ha3o', 'hao3'),
    ('ér', 'e2r', 'er2'),
    ('xiǎng', 'xia3ng', 'xiang3'),
    ('yuǎn', 'yua3n', 'yuan3'),
    ('liù', 'liu4', 'liu4'),
])
def test_tone_to_tone2_and_tone_to_tone3(tone, tone2, tone3):
    assert tone_to_tone2(tone) == tone2
    assert tone_to_tone3(tone) == tone3


def test_tone_to_tone2_tone3_v_to_u():
    assert tone_to_tone2('lüè') == 'lve4'
    assert tone_to_tone2('lüè', v_to_u=True) == 'lüe4'
    assert tone_to_tone3('lüè') == 'lve4'
    assert tone_to_tone3('lüè', v_to_u=True) == 'lüe4'
    assert tone_to_tone2('nǚ') == 'nv3'
    assert tone_to_tone3('nǚ', v_to_u=True) == 'nü3'


def test_tone_to_tone2_tone3_neutral_tone():
    assert tone_to_tone2('shang') == 'shang'
    assert tone_to_tone3('shang') == 'shang'
    assert tone_to_tone2('shang', neutral_tone_with_five=True) == 'sha5ng'
    assert tone_to_tone3('shang', neutral_tone_with_five=True) == 'shang5'
    assert tone_to_tone2('shang', neutral_tone_with_5=True) == 'sha5ng'
    assert tone_to_tone3('shang', neutral_tone_with_5=True) == 'shang5'


def test_tone_to_tone2_legacy_kwarg_overrides_new_kwarg():
    assert tone_to_tone2('shang', neutral_tone_with_five=False,
                         neutral_tone_with_5=True) == 'sha5ng'
    assert tone_to_tone2('shang', neutral_tone_with_five=True,
                         neutral_tone_with_5=False) == 'shang'
    assert tone_to_tone3('shang', neutral_tone_with_five=False,
                         neutral_tone_with_5=True) == 'shang5'
    assert tone_to_tone3('shang', neutral_tone_with_five=True,
                         neutral_tone_with_5=False) == 'shang'


# ---------------------------------------------------------------------------
# tone2_to_*
# ---------------------------------------------------------------------------


@pytest.mark.parametrize('tone2,expected', [
    ('zho1ng', 'zhong'),
    ('ha3o', 'hao'),
    ('e2r', 'er'),
    ('xia3ng', 'xiang'),
    ('shang', 'shang'),
    ('sha5ng', 'shang'),
])
def test_tone2_to_normal_basic(tone2, expected):
    assert tone2_to_normal(tone2) == expected


def test_tone2_to_normal_v_to_u():
    assert tone2_to_normal('lüe4') == 'lve'
    assert tone2_to_normal('lüe4', v_to_u=True) == 'lüe'
    assert tone2_to_normal('lve4') == 'lve'
    assert tone2_to_normal('lve4', v_to_u=True) == 'lüe'
    assert tone2_to_normal('nv3', v_to_u=True) == 'nü'


@pytest.mark.parametrize('tone2,expected', [
    ('zho1ng', 'zhōng'),
    ('ha3o', 'hǎo'),
    ('e2r', 'ér'),
    ('xia3ng', 'xiǎng'),
    ('liu4', 'liù'),
    ('gui1', 'guī'),
    ('lve4', 'lüè'),
    ('lüe4', 'lüè'),
    ('nv3', 'nǚ'),
])
def test_tone2_to_tone_basic(tone2, expected):
    assert tone2_to_tone(tone2) == expected


def test_tone2_to_tone_neutral_tone_loses_digit():
    assert tone2_to_tone('sha5ng') == 'shang'
    assert tone2_to_tone('shang') == 'shang'


@pytest.mark.parametrize('tone2,expected', [
    ('zho1ng', 'zhong1'),
    ('ha3o', 'hao3'),
    ('e2r', 'er2'),
    ('xia3ng', 'xiang3'),
    ('yua3n', 'yuan3'),
    ('liu4', 'liu4'),
])
def test_tone2_to_tone3_moves_digit_to_end(tone2, expected):
    assert tone2_to_tone3(tone2) == expected


def test_tone2_to_tone3_v_to_u():
    assert tone2_to_tone3('lüe4') == 'lve4'
    assert tone2_to_tone3('lüe4', v_to_u=True) == 'lüe4'
    assert tone2_to_tone3('lve4') == 'lve4'
    assert tone2_to_tone3('lve4', v_to_u=True) == 'lüe4'
    assert tone2_to_tone3('nv3', v_to_u=True) == 'nü3'


def test_tone2_to_tone3_preserves_neutral_tone_five():
    # 没有 neutral_tone_with_five 参数，输入里已有的 5 应原样保留
    assert tone2_to_tone3('sha5ng') == 'shang5'
    assert tone2_to_tone3('shang') == 'shang'


# ---------------------------------------------------------------------------
# tone3_to_*
# ---------------------------------------------------------------------------


@pytest.mark.parametrize('tone3,expected', [
    ('zhong1', 'zhong'),
    ('hao3', 'hao'),
    ('er2', 'er'),
    ('xiang3', 'xiang'),
    ('shang', 'shang'),
    ('shang5', 'shang'),
])
def test_tone3_to_normal_basic(tone3, expected):
    assert tone3_to_normal(tone3) == expected


def test_tone3_to_normal_v_to_u():
    assert tone3_to_normal('lüe4') == 'lve'
    assert tone3_to_normal('lüe4', v_to_u=True) == 'lüe'
    assert tone3_to_normal('lve4') == 'lve'
    assert tone3_to_normal('lve4', v_to_u=True) == 'lüe'
    assert tone3_to_normal('nv3', v_to_u=True) == 'nü'


@pytest.mark.parametrize('tone3,expected', [
    ('zhong1', 'zhōng'),
    ('hao3', 'hǎo'),
    ('er2', 'ér'),
    ('xiang3', 'xiǎng'),
    ('liu4', 'liù'),
    ('gui1', 'guī'),
    ('lve4', 'lüè'),
    ('lüe4', 'lüè'),
    ('nv3', 'nǚ'),
    ('yuan3', 'yuǎn'),
])
def test_tone3_to_tone_basic(tone3, expected):
    assert tone3_to_tone(tone3) == expected


def test_tone3_to_tone_neutral_tone_loses_digit():
    assert tone3_to_tone('shang5') == 'shang'
    assert tone3_to_tone('shang') == 'shang'


@pytest.mark.parametrize('tone3,expected', [
    ('zhong1', 'zho1ng'),
    ('hao3', 'ha3o'),
    ('er2', 'e2r'),
    ('xiang3', 'xia3ng'),
    ('yuan3', 'yua3n'),
    ('liu4', 'liu4'),
    ('gui1', 'gui1'),
])
def test_tone3_to_tone2_moves_digit_after_toned_letter(tone3, expected):
    assert tone3_to_tone2(tone3) == expected


def test_tone3_to_tone2_v_to_u():
    assert tone3_to_tone2('lüe4') == 'lve4'
    assert tone3_to_tone2('lüe4', v_to_u=True) == 'lüe4'
    assert tone3_to_tone2('lve4') == 'lve4'
    assert tone3_to_tone2('lve4', v_to_u=True) == 'lüe4'
    assert tone3_to_tone2('nv3', v_to_u=True) == 'nü3'


def test_tone3_to_tone2_preserves_neutral_tone_five():
    assert tone3_to_tone2('shang5') == 'sha5ng'
    assert tone3_to_tone2('shang') == 'shang'


# ---------------------------------------------------------------------------
# 跨函数一致性 / 往返转换
# ---------------------------------------------------------------------------


TONE_SYLLABLES = [
    'zhōng', 'hǎo', 'nǐ', 'ér', 'ān', 'yīng', 'wǒ', 'jué', 'qún',
    'liù', 'guī', 'xiǎng', 'zhuāng', 'yuǎn', 'lüè', 'nǚ', 'lǜ',
    'zhī', 'shang', 'de',
]


@pytest.mark.parametrize('tone', TONE_SYLLABLES)
def test_roundtrip_tone_to_tone2_and_back(tone):
    assert to_tone(to_tone2(tone)) == tone


@pytest.mark.parametrize('tone', TONE_SYLLABLES)
def test_roundtrip_tone_to_tone3_and_back(tone):
    assert to_tone(to_tone3(tone)) == tone


@pytest.mark.parametrize('tone', TONE_SYLLABLES)
def test_roundtrip_tone2_tone3_conversions_agree(tone):
    assert tone2_to_tone3(to_tone2(tone)) == to_tone3(tone)
    assert tone3_to_tone2(to_tone3(tone)) == to_tone2(tone)


@pytest.mark.parametrize('tone', TONE_SYLLABLES)
def test_normal_is_style_independent(tone):
    expected = to_normal(tone)
    assert to_normal(to_tone2(tone)) == expected
    assert to_normal(to_tone3(tone)) == expected
    assert tone_to_normal(tone) == expected
    assert tone2_to_normal(to_tone2(tone)) == expected
    assert tone3_to_normal(to_tone3(tone)) == expected


@pytest.mark.parametrize('tone', TONE_SYLLABLES)
def test_generic_and_dedicated_converters_agree(tone):
    assert to_tone2(tone) == tone_to_tone2(tone)
    assert to_tone3(tone) == tone_to_tone3(tone)
    assert to_tone(to_tone2(tone)) == tone2_to_tone(to_tone2(tone))
    assert to_tone(to_tone3(tone)) == tone3_to_tone(to_tone3(tone))


@pytest.mark.parametrize('tone', TONE_SYLLABLES)
def test_initials_plus_finals_reconstructs_normal_in_loose_mode(tone):
    # 非严格模式下，声母 + 韵母应能拼回 NORMAL 风格的书写形式
    initials = to_initials(tone, strict=False)
    finals = to_finals(tone, strict=False)
    assert initials + finals == to_normal(tone)


@pytest.mark.parametrize('tone', TONE_SYLLABLES)
def test_finals_tone_family_is_consistent(tone):
    assert to_finals(to_finals_tone(tone)) == to_finals(tone)
    assert to_normal(to_finals_tone2(tone)) == to_finals(tone)
    assert to_normal(to_finals_tone3(tone)) == to_finals(tone)
