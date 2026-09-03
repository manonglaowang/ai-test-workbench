# -*- coding: utf-8 -*-
"""pytest 测试用例：pypinyin.contrib.tone_convert 声调风格转换模块

所有期望值均由源码 (_tone_convert.py / _constants.py) 与 docstring 推导得出。
"""
from __future__ import unicode_literals

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

@pytest.mark.parametrize('pinyin,expected', [
    ('zhōng', 'zhong'),
    ('shàng', 'shang'),
    ('hǎo', 'hao'),
    ('ér', 'er'),
    ('jiǔ', 'jiu'),
    ('guī', 'gui'),
    ('yuán', 'yuan'),
    ('xué', 'xue'),
])
def test_to_normal_from_tone_style(pinyin, expected):
    assert to_normal(pinyin) == expected


@pytest.mark.parametrize('pinyin,expected', [
    ('zho1ng', 'zhong'),
    ('sha4ng', 'shang'),
    ('ha3o', 'hao'),
    ('e2r', 'er'),
    ('jiu3', 'jiu'),
])
def test_to_normal_from_tone2_style(pinyin, expected):
    assert to_normal(pinyin) == expected


@pytest.mark.parametrize('pinyin,expected', [
    ('zhong1', 'zhong'),
    ('shang4', 'shang'),
    ('hao3', 'hao'),
    ('er2', 'er'),
    ('shang5', 'shang'),
])
def test_to_normal_from_tone3_style(pinyin, expected):
    assert to_normal(pinyin) == expected


@pytest.mark.parametrize('pinyin,expected_v,expected_u', [
    ('lüè', 'lve', 'lüe'),
    ('lǜ', 'lv', 'lü'),
    ('nǚ', 'nv', 'nü'),
    ('lve4', 'lve', 'lüe'),
    ('lüe4', 'lve', 'lüe'),
    ('lv4e', 'lve', 'lüe'),
    ('nv3', 'nv', 'nü'),
])
def test_to_normal_v_to_u_switch(pinyin, expected_v, expected_u):
    assert to_normal(pinyin) == expected_v
    assert to_normal(pinyin, v_to_u=False) == expected_v
    assert to_normal(pinyin, v_to_u=True) == expected_u


@pytest.mark.parametrize('pinyin', ['shang', 'zhong', 'er', 'a'])
def test_to_normal_of_normal_style_is_identity(pinyin):
    assert to_normal(pinyin) == pinyin


def test_to_normal_empty_string():
    assert to_normal('') == ''
    assert to_normal('', v_to_u=True) == ''


# ---------------------------------------------------------------------------
# to_tone
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('pinyin,expected', [
    ('zho1ng', 'zhōng'),
    ('sha4ng', 'shàng'),
    ('ha3o', 'hǎo'),
    ('e2r', 'ér'),
    ('jiu3', 'jiǔ'),
    ('gui1', 'guī'),
    ('nv3', 'nǚ'),
    ('lve4', 'lüè'),
    ('lüe4', 'lüè'),
])
def test_to_tone_from_tone2_style(pinyin, expected):
    assert to_tone(pinyin) == expected


@pytest.mark.parametrize('pinyin,expected', [
    ('zhong1', 'zhōng'),
    ('shang4', 'shàng'),
    ('hao3', 'hǎo'),
    ('er2', 'ér'),
    ('jiu3', 'jiǔ'),
    ('gui1', 'guī'),
    ('lv4e', 'lüè'),
])
def test_to_tone_from_tone3_style(pinyin, expected):
    assert to_tone(pinyin) == expected


@pytest.mark.parametrize('pinyin', ['zhōng', 'lüè', 'shang', 'zhong', '', 'nǚ'])
def test_to_tone_returns_input_unchanged_when_no_digit(pinyin):
    # 源码开头: if not _re_number.search(pinyin): return pinyin
    assert to_tone(pinyin) == pinyin


@pytest.mark.parametrize('pinyin,expected', [
    ('shang5', 'shang'),
    ('sha5ng', 'shang'),
    ('zhong5', 'zhong'),
])
def test_to_tone_drops_neutral_tone_five(pinyin, expected):
    # tone2_to_tone 会先把 '5' 去掉
    assert to_tone(pinyin) == expected


# ---------------------------------------------------------------------------
# to_tone2
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('pinyin,expected', [
    ('zhōng', 'zho1ng'),
    ('shàng', 'sha4ng'),
    ('hǎo', 'ha3o'),
    ('ér', 'e2r'),
    ('jiǔ', 'jiu3'),
    ('guī', 'gui1'),
    ('lún', 'lu2n'),
])
def test_to_tone2_from_tone_style(pinyin, expected):
    assert to_tone2(pinyin) == expected


@pytest.mark.parametrize('pinyin,expected', [
    ('zhong1', 'zho1ng'),
    ('shang4', 'sha4ng'),
    ('hao3', 'ha3o'),
    ('er2', 'e2r'),
    ('jiu3', 'jiu3'),
    ('gui1', 'gui1'),
])
def test_to_tone2_from_tone3_style(pinyin, expected):
    assert to_tone2(pinyin) == expected


@pytest.mark.parametrize('pinyin', ['shang', 'zhong', 'er', ''])
def test_to_tone2_without_tone_keeps_input(pinyin):
    assert to_tone2(pinyin) == pinyin


@pytest.mark.parametrize('pinyin,expected', [
    ('shang', 'sha5ng'),
    ('zhong', 'zho5ng'),
    ('er', 'e5r'),
])
def test_to_tone2_neutral_tone_with_five(pinyin, expected):
    assert to_tone2(pinyin, neutral_tone_with_five=True) == expected


def test_to_tone2_neutral_tone_with_five_does_not_touch_toned_pinyin():
    assert to_tone2('zhōng', neutral_tone_with_five=True) == 'zho1ng'
    assert to_tone2('zhong1', neutral_tone_with_five=True) == 'zho1ng'


def test_to_tone2_empty_string_never_gets_five():
    # _improve_tone3 中有 `tone3 != ''` 的保护
    assert to_tone2('', neutral_tone_with_five=True) == ''


def test_to_tone2_legacy_neutral_tone_with_5_kwarg_overrides():
    assert to_tone2('shang', neutral_tone_with_5=True) == 'sha5ng'
    # 显式传 neutral_tone_with_5 时会覆盖 neutral_tone_with_five
    assert to_tone2(
        'shang', neutral_tone_with_five=True, neutral_tone_with_5=False
    ) == 'shang'
    assert to_tone2(
        'shang', neutral_tone_with_five=False, neutral_tone_with_5=True
    ) == 'sha5ng'


def test_to_tone2_unknown_kwargs_are_ignored():
    assert to_tone2('zhōng', some_unknown_kwarg=True) == 'zho1ng'


@pytest.mark.parametrize('pinyin,expected_v,expected_u', [
    ('lüè', 'lve4', 'lüe4'),
    ('lǜ', 'lv4', 'lü4'),
    ('nǚ', 'nv3', 'nü3'),
    ('lve4', 'lve4', 'lüe4'),
    ('lüe4', 'lve4', 'lüe4'),
])
def test_to_tone2_v_to_u_switch(pinyin, expected_v, expected_u):
    assert to_tone2(pinyin) == expected_v
    assert to_tone2(pinyin, v_to_u=False) == expected_v
    assert to_tone2(pinyin, v_to_u=True) == expected_u


# ---------------------------------------------------------------------------
# to_tone3
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('pinyin,expected', [
    ('zhōng', 'zhong1'),
    ('shàng', 'shang4'),
    ('hǎo', 'hao3'),
    ('ér', 'er2'),
    ('jiǔ', 'jiu3'),
    ('guī', 'gui1'),
    ('lún', 'lun2'),
])
def test_to_tone3_from_tone_style(pinyin, expected):
    assert to_tone3(pinyin) == expected


@pytest.mark.parametrize('pinyin,expected', [
    ('zho1ng', 'zhong1'),
    ('sha4ng', 'shang4'),
    ('ha3o', 'hao3'),
    ('e2r', 'er2'),
    ('sha5ng', 'shang5'),
])
def test_to_tone3_from_tone2_style(pinyin, expected):
    assert to_tone3(pinyin) == expected


@pytest.mark.parametrize('pinyin', ['shang', 'zhong', 'er', ''])
def test_to_tone3_without_tone_keeps_input(pinyin):
    assert to_tone3(pinyin) == pinyin


@pytest.mark.parametrize('pinyin,expected', [
    ('shang', 'shang5'),
    ('zhong', 'zhong5'),
    ('er', 'er5'),
])
def test_to_tone3_neutral_tone_with_five(pinyin, expected):
    assert to_tone3(pinyin, neutral_tone_with_five=True) == expected


def test_to_tone3_neutral_tone_with_five_does_not_touch_toned_pinyin():
    assert to_tone3('zhōng', neutral_tone_with_five=True) == 'zhong1'
    assert to_tone3('zho1ng', neutral_tone_with_five=True) == 'zhong1'


def test_to_tone3_empty_string_never_gets_five():
    assert to_tone3('', neutral_tone_with_five=True) == ''


def test_to_tone3_legacy_neutral_tone_with_5_kwarg_overrides():
    assert to_tone3('shang', neutral_tone_with_5=True) == 'shang5'
    assert to_tone3(
        'shang', neutral_tone_with_five=True, neutral_tone_with_5=False
    ) == 'shang'


@pytest.mark.parametrize('pinyin,expected_v,expected_u', [
    ('lüè', 'lve4', 'lüe4'),
    ('lǜ', 'lv4', 'lü4'),
    ('nǚ', 'nv3', 'nü3'),
    ('lve4', 'lve4', 'lüe4'),
    ('lüe4', 'lve4', 'lüe4'),
    ('lv4e', 'lve4', 'lüe4'),
])
def test_to_tone3_v_to_u_switch(pinyin, expected_v, expected_u):
    assert to_tone3(pinyin) == expected_v
    assert to_tone3(pinyin, v_to_u=False) == expected_v
    assert to_tone3(pinyin, v_to_u=True) == expected_u


# ---------------------------------------------------------------------------
# to_initials
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('pinyin,expected', [
    ('zhōng', 'zh'),
    ('shàng', 'sh'),
    ('chī', 'ch'),
    ('zì', 'z'),
    ('cì', 'c'),
    ('sì', 's'),
    ('rì', 'r'),
    ('lüè', 'l'),
    ('nǚ', 'n'),
    ('bā', 'b'),
    ('ér', ''),
    ('ān', ''),
    ('ǒu', ''),
])
def test_to_initials_strict_default(pinyin, expected):
    assert to_initials(pinyin) == expected
    assert to_initials(pinyin, strict=True) == expected


@pytest.mark.parametrize('pinyin,strict_expected,not_strict_expected', [
    ('yī', '', 'y'),
    ('yuán', '', 'y'),
    ('yǒng', '', 'y'),
    ('wǒ', '', 'w'),
    ('wǔ', '', 'w'),
    ('wēng', '', 'w'),
])
def test_to_initials_y_w_only_counted_when_not_strict(
        pinyin, strict_expected, not_strict_expected):
    assert to_initials(pinyin, strict=True) == strict_expected
    assert to_initials(pinyin, strict=False) == not_strict_expected


@pytest.mark.parametrize('pinyin', ['zhōng', 'zho1ng', 'zhong1', 'zhong'])
def test_to_initials_works_for_every_input_style(pinyin):
    assert to_initials(pinyin) == 'zh'


def test_to_initials_empty_string():
    assert to_initials('') == ''
    assert to_initials('', strict=False) == ''


# ---------------------------------------------------------------------------
# to_finals
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('pinyin,expected', [
    ('zhōng', 'ong'),
    ('shàng', 'ang'),
    ('hǎo', 'ao'),
    ('ér', 'er'),
    ('bā', 'a'),
    ('ê', 'ê'),
])
def test_to_finals_strict_simple(pinyin, expected):
    assert to_finals(pinyin) == expected
    assert to_finals(pinyin, strict=True) == expected


@pytest.mark.parametrize('pinyin,strict_expected,not_strict_expected', [
    # iou / uei / uen 还原
    ('jiǔ', 'iou', 'iu'),
    ('guī', 'uei', 'ui'),
    ('lún', 'uen', 'un'),
    # 零声母 y / w 还原
    ('yī', 'i', 'i'),
    ('yīng', 'ing', 'ing'),
    ('yǒng', 'iong', 'ong'),
    ('yě', 'ie', 'e'),
    ('wǔ', 'u', 'u'),
    ('wǒ', 'uo', 'o'),
    ('wēn', 'uen', 'en'),
    ('wēng', 'ueng', 'eng'),
])
def test_to_finals_strict_vs_not_strict(pinyin, strict_expected,
                                        not_strict_expected):
    assert to_finals(pinyin, strict=True) == strict_expected
    assert to_finals(pinyin, strict=False) == not_strict_expected


@pytest.mark.parametrize('pinyin,strict_v,strict_u,not_strict', [
    # j/q/x + u 还原为 ü
    ('jū', 'v', 'ü', 'u'),
    ('jūn', 'vn', 'ün', 'un'),
    ('quán', 'van', 'üan', 'uan'),
    ('xué', 've', 'üe', 'ue'),
    # 本来就是 ü
    ('lǜ', 'v', 'ü', 'v'),
    ('lüè', 've', 'üe', 've'),
    ('nǚ', 'v', 'ü', 'v'),
    # 零声母 yu 还原为 ü
    ('yuán', 'van', 'üan', 'uan'),
    ('yuè', 've', 'üe', 'ue'),
    ('yūn', 'vn', 'ün', 'un'),
])
def test_to_finals_v_to_u_switch(pinyin, strict_v, strict_u, not_strict):
    assert to_finals(pinyin) == strict_v
    assert to_finals(pinyin, v_to_u=False) == strict_v
    assert to_finals(pinyin, v_to_u=True) == strict_u
    assert to_finals(pinyin, strict=False) == not_strict


@pytest.mark.parametrize('pinyin', ['zhōng', 'zho1ng', 'zhong1', 'zhong'])
def test_to_finals_accepts_every_input_style(pinyin):
    assert to_finals(pinyin) == 'ong'


def test_to_finals_accepts_v_spelling_of_u_umlaut():
    assert to_finals('lve') == 've'
    assert to_finals('lve', v_to_u=True) == 'üe'
    assert to_finals('lve4') == 've'
    assert to_finals('nv3', v_to_u=True) == 'ü'


def test_to_finals_empty_string():
    assert to_finals('') == ''
    assert to_finals('', strict=False) == ''
    assert to_finals('', v_to_u=True) == ''


# ---------------------------------------------------------------------------
# to_finals_tone3
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('pinyin,expected', [
    ('zhōng', 'ong1'),
    ('shàng', 'ang4'),
    ('hǎo', 'ao3'),
    ('ér', 'er2'),
    ('jiǔ', 'iou3'),
    ('guī', 'uei1'),
    ('lún', 'uen2'),
    ('wǒ', 'uo3'),
    ('yuán', 'van2'),
    ('xué', 've2'),
    ('lüè', 've4'),
    ('lǜ', 'v4'),
    ('nǚ', 'v3'),
])
def test_to_finals_tone3_strict_from_tone_style(pinyin, expected):
    assert to_finals_tone3(pinyin) == expected


@pytest.mark.parametrize('pinyin,expected', [
    ('zho1ng', 'ong1'),
    ('zhong1', 'ong1'),
    ('zhong', 'ong'),
    ('sha4ng', 'ang4'),
    ('shang4', 'ang4'),
    ('shang5', 'ang5'),
])
def test_to_finals_tone3_accepts_tone2_and_tone3_input(pinyin, expected):
    assert to_finals_tone3(pinyin) == expected


@pytest.mark.parametrize('pinyin,expected', [
    ('jiǔ', 'iu3'),
    ('guī', 'ui1'),
    ('lún', 'un2'),
    ('wǒ', 'o3'),
    ('yuán', 'uan2'),
    ('xué', 'ue2'),
    ('yīng', 'ing1'),
    ('wǔ', 'u3'),
])
def test_to_finals_tone3_not_strict(pinyin, expected):
    assert to_finals_tone3(pinyin, strict=False) == expected


@pytest.mark.parametrize('pinyin,expected', [
    ('lüè', 'üe4'),
    ('lǜ', 'ü4'),
    ('nǚ', 'ü3'),
    ('yuán', 'üan2'),
    ('jūn', 'ün1'),
    ('xué', 'üe2'),
])
def test_to_finals_tone3_v_to_u(pinyin, expected):
    assert to_finals_tone3(pinyin, v_to_u=True) == expected


@pytest.mark.parametrize('pinyin,expected', [
    ('shang', 'ang5'),
    ('zhong', 'ong5'),
    ('wo', 'uo5'),
])
def test_to_finals_tone3_neutral_tone_with_five(pinyin, expected):
    assert to_finals_tone3(pinyin, neutral_tone_with_five=True) == expected
    # 未开启时不追加 5
    assert to_finals_tone3(pinyin) == expected[:-1]


def test_to_finals_tone3_neutral_tone_with_five_ignored_when_tone_present():
    assert to_finals_tone3('zhōng', neutral_tone_with_five=True) == 'ong1'
    assert to_finals_tone3('zhong1', neutral_tone_with_five=True) == 'ong1'


def test_to_finals_tone3_empty_finals_short_circuits():
    # to_finals 返回空时直接返回，不追加声调数字
    assert to_finals_tone3('') == ''
    assert to_finals_tone3('', neutral_tone_with_five=True) == ''


def test_to_finals_tone3_strict_and_v_to_u_combined():
    assert to_finals_tone3('yuán', strict=False, v_to_u=True) == 'uan2'
    assert to_finals_tone3('jūn', strict=False, v_to_u=True) == 'un1'
    assert to_finals_tone3('lüè', strict=False, v_to_u=True) == 'üe4'


# ---------------------------------------------------------------------------
# to_finals_tone2
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('pinyin,expected', [
    ('zhōng', 'o1ng'),
    ('shàng', 'a4ng'),
    ('hǎo', 'a3o'),
    ('ér', 'e2r'),
    ('jiǔ', 'io3u'),
    ('guī', 'ue1i'),
    ('lún', 'ue2n'),
    ('wǒ', 'uo3'),
    ('yuán', 'va2n'),
    ('xué', 've2'),
    ('lüè', 've4'),
    ('lǜ', 'v4'),
    ('nǚ', 'v3'),
    ('jūn', 'v1n'),
])
def test_to_finals_tone2_strict(pinyin, expected):
    assert to_finals_tone2(pinyin) == expected


@pytest.mark.parametrize('pinyin,expected', [
    ('jiǔ', 'iu3'),
    ('guī', 'ui1'),
    ('lún', 'u2n'),
    ('wǒ', 'o3'),
    ('yuán', 'ua2n'),
    ('xué', 'ue2'),
    ('zhōng', 'o1ng'),
])
def test_to_finals_tone2_not_strict(pinyin, expected):
    assert to_finals_tone2(pinyin, strict=False) == expected


@pytest.mark.parametrize('pinyin,expected', [
    ('lüè', 'üe4'),
    ('lǜ', 'ü4'),
    ('nǚ', 'ü3'),
    ('yuán', 'üa2n'),
    ('jūn', 'ü1n'),
])
def test_to_finals_tone2_v_to_u(pinyin, expected):
    assert to_finals_tone2(pinyin, v_to_u=True) == expected


@pytest.mark.parametrize('pinyin,expected', [
    ('shang', 'a5ng'),
    ('zhong', 'o5ng'),
])
def test_to_finals_tone2_neutral_tone_with_five(pinyin, expected):
    assert to_finals_tone2(pinyin, neutral_tone_with_five=True) == expected


@pytest.mark.parametrize('pinyin,expected', [
    ('shang', 'ang'),
    ('zhong', 'ong'),
])
def test_to_finals_tone2_without_tone_returns_plain_finals(pinyin, expected):
    assert to_finals_tone2(pinyin) == expected


def test_to_finals_tone2_empty_string():
    assert to_finals_tone2('') == ''
    assert to_finals_tone2('', neutral_tone_with_five=True) == ''


# ---------------------------------------------------------------------------
# to_finals_tone
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('pinyin,expected', [
    ('zhōng', 'ōng'),
    ('shàng', 'àng'),
    ('hǎo', 'ǎo'),
    ('ér', 'ér'),
    ('jiǔ', 'iǒu'),
    ('guī', 'uēi'),
    ('wǒ', 'uǒ'),
    ('yuán', 'üán'),
    ('xué', 'üé'),
    ('lüè', 'üè'),
    ('lǜ', 'ǜ'),
    ('nǚ', 'ǚ'),
    ('jūn', 'ǖn'),
])
def test_to_finals_tone_strict(pinyin, expected):
    assert to_finals_tone(pinyin) == expected


@pytest.mark.parametrize('pinyin,expected', [
    ('jiǔ', 'iǔ'),
    ('guī', 'uī'),
    ('wǒ', 'ǒ'),
    ('yuán', 'uán'),
    ('xué', 'ué'),
    ('zhōng', 'ōng'),
])
def test_to_finals_tone_not_strict(pinyin, expected):
    assert to_finals_tone(pinyin, strict=False) == expected


@pytest.mark.parametrize('pinyin,expected', [
    ('zho1ng', 'ōng'),
    ('zhong1', 'ōng'),
    ('lve4', 'üè'),
    ('lüe4', 'üè'),
])
def test_to_finals_tone_accepts_tone2_and_tone3_input(pinyin, expected):
    assert to_finals_tone(pinyin) == expected


@pytest.mark.parametrize('pinyin,expected', [
    ('shang', 'ang'),
    ('shang5', 'ang'),
    ('zhong', 'ong'),
])
def test_to_finals_tone_neutral_tone_has_no_mark(pinyin, expected):
    assert to_finals_tone(pinyin) == expected


def test_to_finals_tone_empty_string():
    assert to_finals_tone('') == ''


# ---------------------------------------------------------------------------
# tone_to_normal / tone_to_tone2 / tone_to_tone3
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('tone,expected', [
    ('zhōng', 'zhong'),
    ('shàng', 'shang'),
    ('shang', 'shang'),
    ('ér', 'er'),
    ('lüè', 'lve'),
    ('nǚ', 'nv'),
])
def test_tone_to_normal(tone, expected):
    assert tone_to_normal(tone) == expected


@pytest.mark.parametrize('tone,expected', [
    ('lüè', 'lüe'),
    ('nǚ', 'nü'),
    ('zhōng', 'zhong'),
])
def test_tone_to_normal_v_to_u(tone, expected):
    assert tone_to_normal(tone, v_to_u=True) == expected


@pytest.mark.parametrize('tone,expected', [
    ('zhōng', 'zho1ng'),
    ('shàng', 'sha4ng'),
    ('shang', 'shang'),
    ('hǎo', 'ha3o'),
    ('jiǔ', 'jiu3'),
    ('guī', 'gui1'),
    ('ér', 'e2r'),
    ('lüè', 'lve4'),
    ('nǚ', 'nv3'),
])
def test_tone_to_tone2(tone, expected):
    assert tone_to_tone2(tone) == expected


def test_tone_to_tone2_v_to_u():
    assert tone_to_tone2('lüè', v_to_u=True) == 'lüe4'
    assert tone_to_tone2('nǚ', v_to_u=True) == 'nü3'
    assert tone_to_tone2('zhōng', v_to_u=True) == 'zho1ng'


def test_tone_to_tone2_neutral_tone_with_five_and_legacy_kwarg():
    assert tone_to_tone2('shang', neutral_tone_with_five=True) == 'sha5ng'
    assert tone_to_tone2('shang', neutral_tone_with_5=True) == 'sha5ng'
    assert tone_to_tone2('shang') == 'shang'
    assert tone_to_tone2(
        'shang', neutral_tone_with_five=True, neutral_tone_with_5=False
    ) == 'shang'
    assert tone_to_tone2('zhōng', neutral_tone_with_five=True) == 'zho1ng'


@pytest.mark.parametrize('tone,expected', [
    ('zhōng', 'zhong1'),
    ('shàng', 'shang4'),
    ('shang', 'shang'),
    ('hǎo', 'hao3'),
    ('jiǔ', 'jiu3'),
    ('guī', 'gui1'),
    ('ér', 'er2'),
    ('lüè', 'lve4'),
    ('nǚ', 'nv3'),
])
def test_tone_to_tone3(tone, expected):
    assert tone_to_tone3(tone) == expected


def test_tone_to_tone3_v_to_u():
    assert tone_to_tone3('lüè', v_to_u=True) == 'lüe4'
    assert tone_to_tone3('nǚ', v_to_u=True) == 'nü3'


def test_tone_to_tone3_neutral_tone_with_five_and_legacy_kwarg():
    assert tone_to_tone3('shang', neutral_tone_with_five=True) == 'shang5'
    assert tone_to_tone3('shang', neutral_tone_with_5=True) == 'shang5'
    assert tone_to_tone3('shang') == 'shang'
    assert tone_to_tone3(
        'shang', neutral_tone_with_five=True, neutral_tone_with_5=False
    ) == 'shang'
    assert tone_to_tone3('', neutral_tone_with_five=True) == ''


# ---------------------------------------------------------------------------
# tone2_to_normal / tone2_to_tone / tone2_to_tone3
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('tone2,expected', [
    ('zho1ng', 'zhong'),
    ('sha4ng', 'shang'),
    ('sha5ng', 'shang'),
    ('shang', 'shang'),
    ('lüe4', 'lve'),
    ('lve4', 'lve'),
    ('lv4e', 'lve'),
    ('nv3', 'nv'),
])
def test_tone2_to_normal(tone2, expected):
    assert tone2_to_normal(tone2) == expected


@pytest.mark.parametrize('tone2,expected', [
    ('lüe4', 'lüe'),
    ('lve4', 'lüe'),
    ('nv3', 'nü'),
    ('zho1ng', 'zhong'),
])
def test_tone2_to_normal_v_to_u(tone2, expected):
    assert tone2_to_normal(tone2, v_to_u=True) == expected


@pytest.mark.parametrize('tone2,expected', [
    ('zho1ng', 'zhōng'),
    ('sha4ng', 'shàng'),
    ('ha3o', 'hǎo'),
    ('e2r', 'ér'),
    ('jiu3', 'jiǔ'),
    ('gui1', 'guī'),
    ('lve4', 'lüè'),
    ('lüe4', 'lüè'),
    ('lv4e', 'lǜe'),
    ('nv3', 'nǚ'),
    ('shang', 'shang'),
])
def test_tone2_to_tone(tone2, expected):
    assert tone2_to_tone(tone2) == expected


def test_tone2_to_tone_strips_neutral_tone_digits():
    # '5' 与 '0' 会被直接去掉
    assert tone2_to_tone('sha5ng') == 'shang'
    assert tone2_to_tone('sha0ng') == 'shang'


def test_tone2_to_tone_replaces_every_occurrence():
    # 正则去掉了 '$' 锚点，因此是全局替换
    assert tone2_to_tone('ni3 ha3o') == 'nǐ hǎo'


@pytest.mark.parametrize('tone2,expected', [
    ('zho1ng', 'zhong1'),
    ('sha4ng', 'shang4'),
    ('sha5ng', 'shang5'),
    ('shang', 'shang'),
    ('lve4', 'lve4'),
    ('lv4e', 'lve4'),
    ('lüe4', 'lve4'),
    ('e2r', 'er2'),
])
def test_tone2_to_tone3(tone2, expected):
    assert tone2_to_tone3(tone2) == expected


@pytest.mark.parametrize('tone2,expected', [
    ('lüe4', 'lüe4'),
    ('lve4', 'lüe4'),
    ('lv4e', 'lüe4'),
    ('zho1ng', 'zhong1'),
])
def test_tone2_to_tone3_v_to_u(tone2, expected):
    assert tone2_to_tone3(tone2, v_to_u=True) == expected


# ---------------------------------------------------------------------------
# tone3_to_normal / tone3_to_tone / tone3_to_tone2
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('tone3,expected', [
    ('zhong1', 'zhong'),
    ('shang4', 'shang'),
    ('shang5', 'shang'),
    ('shang', 'shang'),
    ('lüe4', 'lve'),
    ('lve4', 'lve'),
    ('nv3', 'nv'),
])
def test_tone3_to_normal(tone3, expected):
    assert tone3_to_normal(tone3) == expected


@pytest.mark.parametrize('tone3,expected', [
    ('lüe4', 'lüe'),
    ('lve4', 'lüe'),
    ('nv3', 'nü'),
    ('zhong1', 'zhong'),
])
def test_tone3_to_normal_v_to_u(tone3, expected):
    assert tone3_to_normal(tone3, v_to_u=True) == expected


@pytest.mark.parametrize('tone3,expected', [
    ('zhong1', 'zhōng'),
    ('shang4', 'shàng'),
    ('hao3', 'hǎo'),
    ('er2', 'ér'),
    ('jiu3', 'jiǔ'),
    ('gui1', 'guī'),
    ('lve4', 'lüè'),
    ('lüe4', 'lüè'),
    ('nv3', 'nǚ'),
    ('n2', 'ń'),
    ('shang', 'shang'),
    ('shang5', 'shang'),
])
def test_tone3_to_tone(tone3, expected):
    assert tone3_to_tone(tone3) == expected


@pytest.mark.parametrize('tone3,expected', [
    ('zhong1', 'zho1ng'),
    ('shang4', 'sha4ng'),
    ('shang5', 'sha5ng'),
    ('hao3', 'ha3o'),
    ('er2', 'e2r'),
    ('jiu3', 'jiu3'),
    ('gui1', 'gui1'),
    ('lun2', 'lu2n'),
    ('lve4', 'lve4'),
    ('lüe4', 'lve4'),
    ('nv3', 'nv3'),
    ('ong1', 'o1ng'),
    ('iou3', 'io3u'),
    ('uei1', 'ue1i'),
])
def test_tone3_to_tone2(tone3, expected):
    assert tone3_to_tone2(tone3) == expected


@pytest.mark.parametrize('tone3,expected', [
    ('lve4', 'lüe4'),
    ('lüe4', 'lüe4'),
    ('nv3', 'nü3'),
    ('zhong1', 'zho1ng'),
])
def test_tone3_to_tone2_v_to_u(tone3, expected):
    assert tone3_to_tone2(tone3, v_to_u=True) == expected


@pytest.mark.parametrize('tone3', ['shang', 'zhong', 'lüe', 'lve', ''])
def test_tone3_to_tone2_returns_input_verbatim_without_number(tone3):
    # 源码: number is None 时直接 return tone3（不做 v/ü 归一化）
    assert tone3_to_tone2(tone3) == tone3
    assert tone3_to_tone2(tone3, v_to_u=True) == tone3


# ---------------------------------------------------------------------------
# 跨风格一致性 / 往返转换
# ---------------------------------------------------------------------------

ROUND_TRIP_CASES = [
    ('zhōng', 'zho1ng', 'zhong1', 'zhong'),
    ('shàng', 'sha4ng', 'shang4', 'shang'),
    ('hǎo', 'ha3o', 'hao3', 'hao'),
    ('lüè', 'lve4', 'lve4', 'lve'),
    ('nǚ', 'nv3', 'nv3', 'nv'),
    ('jiǔ', 'jiu3', 'jiu3', 'jiu'),
    ('guī', 'gui1', 'gui1', 'gui'),
    ('ér', 'e2r', 'er2', 'er'),
]


@pytest.mark.parametrize('tone,tone2,tone3,normal', ROUND_TRIP_CASES)
def test_to_xxx_converts_tone_style_into_every_other_style(
        tone, tone2, tone3, normal):
    assert to_tone2(tone) == tone2
    assert to_tone3(tone) == tone3
    assert to_normal(tone) == normal
    # TONE 输入本身不含数字，to_tone 原样返回
    assert to_tone(tone) == tone


@pytest.mark.parametrize('tone,tone2,tone3,normal', ROUND_TRIP_CASES)
def test_to_xxx_converts_tone2_style_into_every_other_style(
        tone, tone2, tone3, normal):
    assert to_tone(tone2) == tone
    assert to_tone2(tone2) == tone2
    assert to_tone3(tone2) == tone3
    assert to_normal(tone2) == normal


@pytest.mark.parametrize('tone,tone2,tone3,normal', ROUND_TRIP_CASES)
def test_to_xxx_converts_tone3_style_into_every_other_style(
        tone, tone2, tone3, normal):
    assert to_tone(tone3) == tone
    assert to_tone2(tone3) == tone2
    assert to_tone3(tone3) == tone3
    assert to_normal(tone3) == normal


@pytest.mark.parametrize('tone,tone2,tone3,normal', ROUND_TRIP_CASES)
def test_pairwise_helpers_match_the_generic_helpers(
        tone, tone2, tone3, normal):
    assert tone_to_tone2(tone) == tone2
    assert tone_to_tone3(tone) == tone3
    assert tone_to_normal(tone) == normal
    assert tone2_to_tone(tone2) == tone
    assert tone2_to_tone3(tone2) == tone3
    assert tone2_to_normal(tone2) == normal
    assert tone3_to_tone(tone3) == tone
    assert tone3_to_tone2(tone3) == tone2
    assert tone3_to_normal(tone3) == normal


@pytest.mark.parametrize('tone', [c[0] for c in ROUND_TRIP_CASES])
def test_initials_plus_finals_equals_normal_pinyin(tone):
    assert to_initials(tone, strict=False) + \
        to_finals(tone, strict=False) == to_normal(tone)


@pytest.mark.parametrize('tone', ['zhōng', 'shàng', 'hǎo', 'jiǔ', 'guī'])
def test_finals_styles_are_consistent_with_each_other(tone):
    assert to_finals(tone) == to_normal(to_finals_tone(tone))
    assert to_finals_tone2(tone) == tone3_to_tone2(to_finals_tone3(tone))
    assert to_finals_tone(tone) == tone2_to_tone(to_finals_tone2(tone))


# ---------------------------------------------------------------------------
# 函数签名（可选参数）约束
# ---------------------------------------------------------------------------

def test_functions_reject_parameters_not_in_their_signature():
    with pytest.raises(TypeError):
        to_tone('zho1ng', v_to_u=True)
    with pytest.raises(TypeError):
        to_normal('zhōng', neutral_tone_with_five=True)
    with pytest.raises(TypeError):
        to_initials('zhōng', v_to_u=True)
    with pytest.raises(TypeError):
        to_finals_tone('zhōng', v_to_u=True)
    with pytest.raises(TypeError):
        to_finals_tone2('zhōng', neutral_tone_with_5=True)
    with pytest.raises(TypeError):
        to_finals_tone3('zhōng', neutral_tone_with_5=True)
    with pytest.raises(TypeError):
        tone2_to_tone('zho1ng', v_to_u=True)
    with pytest.raises(TypeError):
        tone3_to_tone('zhong1', v_to_u=True)
