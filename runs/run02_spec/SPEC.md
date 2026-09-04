# tone_convert 模块规格说明

> 本文件只包含**函数签名与文档说明**，不含任何实现代码。
> 你的任务是根据「这些函数应该做什么」来推导期望行为。

## `to_normal(pinyin, v_to_u=False)`

```
将 :py:attr:`~pypinyin.Style.TONE`、
:py:attr:`~pypinyin.Style.TONE2` 或
:py:attr:`~pypinyin.Style.TONE3` 风格的拼音转换为
:py:attr:`~pypinyin.Style.NORMAL` 风格的拼音

:param pinyin: :py:attr:`~pypinyin.Style.TONE`、
               :py:attr:`~pypinyin.Style.TONE2` 或
               :py:attr:`~pypinyin.Style.TONE3` 风格的拼音
:param v_to_u: 是否使用 ``ü`` 代替原来的 ``v``，
               当为 False 时结果中将使用 ``v`` 表示 ``ü``
:return: :py:attr:`~pypinyin.Style.NORMAL` 风格的拼音

Usage::

  >>> from pypinyin.contrib.tone_convert import to_normal
  >>> to_normal('zhōng')
  'zhong'
  >>> to_normal('zho1ng')
  'zhong'
  >>> to_normal('zhong1')
  'zhong'
  >>> to_normal('lüè')
  'lve'
  >>> to_normal('lüè', v_to_u=True)
  'lüe'
```

## `to_tone(pinyin)`

```
将 :py:attr:`~pypinyin.Style.TONE2` 或
:py:attr:`~pypinyin.Style.TONE3` 风格的拼音转换为
:py:attr:`~pypinyin.Style.TONE` 风格的拼音

:param pinyin: :py:attr:`~pypinyin.Style.TONE2` 或
               :py:attr:`~pypinyin.Style.TONE3` 风格的拼音
:return: :py:attr:`~pypinyin.Style.TONE` 风格的拼音

Usage::

  >>> from pypinyin.contrib.tone_convert import to_tone
  >>> to_tone('zho1ng')
  'zhōng'
  >>> to_tone('zhong1')
  'zhōng'
```

## `to_tone2(pinyin, v_to_u=False, neutral_tone_with_five=False, **kwargs)`

```
将 :py:attr:`~pypinyin.Style.TONE` 或
:py:attr:`~pypinyin.Style.TONE3` 风格的拼音转换为
:py:attr:`~pypinyin.Style.TONE2` 风格的拼音

:param pinyin: :py:attr:`~pypinyin.Style.TONE` 或
               :py:attr:`~pypinyin.Style.TONE3` 风格的拼音
:param v_to_u: 是否使用 ``ü`` 代替原来的 ``v``，
               当为 False 时结果中将使用 ``v`` 表示 ``ü``
:param neutral_tone_with_five: 是否使用 ``5`` 标识轻声
:param kwargs: 用于兼容老版本的 ``neutral_tone_with_5`` 参数，当传入
               ``neutral_tone_with_5`` 参数时，
               将覆盖 ``neutral_tone_with_five`` 的值。
:return: :py:attr:`~pypinyin.Style.TONE2` 风格的拼音

Usage::

  >>> from pypinyin.contrib.tone_convert import to_tone2
  >>> to_tone2('zhōng')
  'zho1ng'
  >>> to_tone2('zhong1')
  'zho1ng'
  >>> to_tone2('shang')
  'shang'
  >>> to_tone2('shang', neutral_tone_with_five=True)
  'sha5ng'
  >>> to_tone2('lüè')
  'lve4'
  >>> to_tone2('lüè', v_to_u=True)
  'lüe4'
```

## `to_tone3(pinyin, v_to_u=False, neutral_tone_with_five=False, **kwargs)`

```
将 :py:attr:`~pypinyin.Style.TONE` 或
:py:attr:`~pypinyin.Style.TONE2` 风格的拼音转换为
:py:attr:`~pypinyin.Style.TONE3` 风格的拼音

:param pinyin: :py:attr:`~pypinyin.Style.TONE` 或
               :py:attr:`~pypinyin.Style.TONE2` 风格的拼音
:param v_to_u: 是否使用 ``ü`` 代替原来的 ``v``，
               当为 False 时结果中将使用 ``v`` 表示 ``ü``
:param neutral_tone_with_five: 是否使用 ``5`` 标识轻声
:param kwargs: 用于兼容老版本的 ``neutral_tone_with_5`` 参数，当传入
               ``neutral_tone_with_5`` 参数时，
               将覆盖 ``neutral_tone_with_five`` 的值。
:return: :py:attr:`~pypinyin.Style.TONE2` 风格的拼音

Usage::

  >>> from pypinyin.contrib.tone_convert import to_tone3
  >>> to_tone3('zhōng')
  'zhong1'
  >>> to_tone3('zho1ng')
  'zhong1'
  >>> to_tone3('shang')
  'shang'
  >>> to_tone3('shang', neutral_tone_with_five=True)
  'shang5'
  >>> to_tone3('lüè')
  'lve4'
  >>> to_tone3('lüè', v_to_u=True)
  'lüe4'
```

## `to_initials(pinyin, strict=True)`

```
将 :py:attr:`~pypinyin.Style.TONE`、
:py:attr:`~pypinyin.Style.TONE2` 、
:py:attr:`~pypinyin.Style.TONE3` 或
:py:attr:`~pypinyin.Style.NORMAL` 风格的拼音转换为
:py:attr:`~pypinyin.Style.INITIALS` 风格的拼音

:param pinyin: :py:attr:`~pypinyin.Style.TONE`、
               :py:attr:`~pypinyin.Style.TONE2` 、
               :py:attr:`~pypinyin.Style.TONE3` 或
               :py:attr:`~pypinyin.Style.NORMAL` 风格的拼音
:param strict: 返回结果是否严格遵照《汉语拼音方案》来处理声母和韵母，
               详见 :ref:`strict`
:return: :py:attr:`~pypinyin.Style.INITIALS` 风格的拼音

Usage::

  >>> from pypinyin.contrib.tone_convert import to_initials
  >>> to_initials('zhōng')
  'zh'
```

## `to_finals(pinyin, strict=True, v_to_u=False)`

```
将 :py:attr:`~pypinyin.Style.TONE`、
:py:attr:`~pypinyin.Style.TONE2` 、
:py:attr:`~pypinyin.Style.TONE3` 或
:py:attr:`~pypinyin.Style.NORMAL` 风格的拼音转换为
:py:attr:`~pypinyin.Style.FINALS` 风格的拼音

:param pinyin: :py:attr:`~pypinyin.Style.TONE`、
               :py:attr:`~pypinyin.Style.TONE2` 、
               :py:attr:`~pypinyin.Style.TONE3` 或
               :py:attr:`~pypinyin.Style.NORMAL` 风格的拼音
:param strict: 返回结果是否严格遵照《汉语拼音方案》来处理声母和韵母，
               详见 :ref:`strict`
:param v_to_u: 是否使用 ``ü`` 代替原来的 ``v``，
               当为 False 时结果中将使用 ``v`` 表示 ``ü``
:return: :py:attr:`~pypinyin.Style.FINALS` 风格的拼音

Usage::

  >>> from pypinyin.contrib.tone_convert import to_finals
  >>> to_finals('zhōng')
  'ong'
```

## `to_finals_tone(pinyin, strict=True)`

```
将 :py:attr:`~pypinyin.Style.TONE`、
:py:attr:`~pypinyin.Style.TONE2` 或
:py:attr:`~pypinyin.Style.TONE3` 风格的拼音转换为
:py:attr:`~pypinyin.Style.FINALS_TONE` 风格的拼音

:param pinyin: :py:attr:`~pypinyin.Style.TONE`、
               :py:attr:`~pypinyin.Style.TONE2` 或
               :py:attr:`~pypinyin.Style.TONE3` 风格的拼音
:param strict: 返回结果是否严格遵照《汉语拼音方案》来处理声母和韵母，
               详见 :ref:`strict`
:return: :py:attr:`~pypinyin.Style.FINALS_TONE` 风格的拼音

Usage::

  >>> from pypinyin.contrib.tone_convert import to_finals_tone
  >>> to_finals_tone('zhōng')
  'ōng'
```

## `to_finals_tone2(pinyin, strict=True, v_to_u=False, neutral_tone_with_five=False)`

```
将 :py:attr:`~pypinyin.Style.TONE`、
:py:attr:`~pypinyin.Style.TONE2` 或
:py:attr:`~pypinyin.Style.TONE3` 风格的拼音转换为
:py:attr:`~pypinyin.Style.FINALS_TONE2` 风格的拼音

:param pinyin: :py:attr:`~pypinyin.Style.TONE`、
               :py:attr:`~pypinyin.Style.TONE2` 或
               :py:attr:`~pypinyin.Style.TONE3` 风格的拼音
:param strict: 返回结果是否严格遵照《汉语拼音方案》来处理声母和韵母，
               详见 :ref:`strict`
:param v_to_u: 是否使用 ``ü`` 代替原来的 ``v``，
               当为 False 时结果中将使用 ``v`` 表示 ``ü``
:param neutral_tone_with_five: 是否使用 ``5`` 标识轻声
:return: :py:attr:`~pypinyin.Style.FINALS_TONE2` 风格的拼音

Usage::

  >>> from pypinyin.contrib.tone_convert import to_finals_tone2
  >>> to_finals_tone2('zhōng')
  'o1ng'
```

## `to_finals_tone3(pinyin, strict=True, v_to_u=False, neutral_tone_with_five=False)`

```
将 :py:attr:`~pypinyin.Style.TONE`、
:py:attr:`~pypinyin.Style.TONE2` 或
:py:attr:`~pypinyin.Style.TONE3` 风格的拼音转换为
:py:attr:`~pypinyin.Style.FINALS_TONE3` 风格的拼音

:param pinyin: :py:attr:`~pypinyin.Style.TONE`、
               :py:attr:`~pypinyin.Style.TONE2` 或
               :py:attr:`~pypinyin.Style.TONE3` 风格的拼音
:param strict: 返回结果是否严格遵照《汉语拼音方案》来处理声母和韵母，
               详见 :ref:`strict`
:param v_to_u: 是否使用 ``ü`` 代替原来的 ``v``，
               当为 False 时结果中将使用 ``v`` 表示 ``ü``
:param neutral_tone_with_five: 是否使用 ``5`` 标识轻声
:return: :py:attr:`~pypinyin.Style.FINALS_TONE3` 风格的拼音

Usage::

  >>> from pypinyin.contrib.tone_convert import to_finals_tone3
  >>> to_finals_tone3('zhōng')
  'ong1'
```

## `tone_to_normal(tone, v_to_u=False)`

```
将 :py:attr:`~pypinyin.Style.TONE` 风格的拼音转换为
:py:attr:`~pypinyin.Style.NORMAL` 风格的拼音

:param tone: :py:attr:`~pypinyin.Style.TONE` 风格的拼音
:param v_to_u: 是否使用 ``ü`` 代替原来的 ``v``，
               当为 False 时结果中将使用 ``v`` 表示 ``ü``
:return: :py:attr:`~pypinyin.Style.NORMAL` 风格的拼音

Usage::

  >>> from pypinyin.contrib.tone_convert import tone_to_normal
  >>> tone_to_normal('zhōng')
  'zhong'
  >>> tone_to_normal('lüè')
  'lve'
  >>> tone_to_normal('lüè', v_to_u=True)
  'lüe'
```

## `tone_to_tone2(tone, v_to_u=False, neutral_tone_with_five=False, **kwargs)`

```
将 :py:attr:`~pypinyin.Style.TONE` 风格的拼音转换为
:py:attr:`~pypinyin.Style.TONE2` 风格的拼音

:param tone: :py:attr:`~pypinyin.Style.TONE` 风格的拼音
:param v_to_u: 是否使用 ``ü`` 代替原来的 ``v``，
               当为 False 时结果中将使用 ``v`` 表示 ``ü``
:param neutral_tone_with_five: 是否使用 ``5`` 标识轻声
:param kwargs: 用于兼容老版本的 ``neutral_tone_with_5`` 参数，当传入
               ``neutral_tone_with_5`` 参数时，
               将覆盖 ``neutral_tone_with_five`` 的值。
:return: :py:attr:`~pypinyin.Style.TONE2` 风格的拼音

Usage::

  >>> from pypinyin.contrib.tone_convert import tone_to_tone2
  >>> tone_to_tone2('zhōng')
  'zho1ng'
  >>> tone_to_tone2('shang')
  'shang'
  >>> tone_to_tone2('shang', neutral_tone_with_5=True)
  'sha5ng'
  >>> tone_to_tone2('lüè')
  'lve4'
  >>> tone_to_tone2('lüè', v_to_u=True)
  'lüe4'
```

## `tone_to_tone3(tone, v_to_u=False, neutral_tone_with_five=False, **kwargs)`

```
将 :py:attr:`~pypinyin.Style.TONE` 风格的拼音转换为
:py:attr:`~pypinyin.Style.TONE3` 风格的拼音

:param tone: :py:attr:`~pypinyin.Style.TONE` 风格的拼音
:param v_to_u: 是否使用 ``ü`` 代替原来的 ``v``，
               当为 False 时结果中将使用 ``v`` 表示 ``ü``
:param neutral_tone_with_five: 是否使用 ``5`` 标识轻声
:param kwargs: 用于兼容老版本的 ``neutral_tone_with_5`` 参数，当传入
               ``neutral_tone_with_5`` 参数时，
               将覆盖 ``neutral_tone_with_five`` 的值。
:return: :py:attr:`~pypinyin.Style.TONE3` 风格的拼音

Usage::

  >>> from pypinyin.contrib.tone_convert import tone_to_tone3
  >>> tone_to_tone3('zhōng')
  'zhong1'
  >>> tone_to_tone3('shang')
  'shang'
  >>> tone_to_tone3('shang', neutral_tone_with_five=True)
  'shang5'
  >>> tone_to_tone3('lüè')
  'lve4'
  >>> tone_to_tone3('lüè', v_to_u=True)
  'lüe4'
```

## `tone2_to_normal(tone2, v_to_u=False)`

```
将 :py:attr:`~pypinyin.Style.TONE2` 风格的拼音转换为
:py:attr:`~pypinyin.Style.NORMAL` 风格的拼音

:param tone2: :py:attr:`~pypinyin.Style.TONE2` 风格的拼音
:param v_to_u: 是否使用 ``ü`` 代替原来的 ``v``，
               当为 False 时结果中将使用 ``v`` 表示 ``ü``
:return: Style.NORMAL 风格的拼音

Usage::

  >>> from pypinyin.contrib.tone_convert import tone2_to_normal
  >>> tone2_to_normal('zho1ng')
  'zhong'
  >>> tone2_to_normal('lüe4')
  'lve'
  >>> tone2_to_normal('lüe4', v_to_u=True)
  'lüe'
```

## `tone2_to_tone(tone2)`

```
将 :py:attr:`~pypinyin.Style.TONE2` 风格的拼音转换为
:py:attr:`~pypinyin.Style.TONE` 风格的拼音

:param tone2: :py:attr:`~pypinyin.Style.TONE2` 风格的拼音
:return: Style.TONE 风格的拼音

Usage::

  >>> from pypinyin.contrib.tone_convert import tone2_to_tone
  >>> tone2_to_tone('zho1ng')
  'zhōng'
```

## `tone2_to_tone3(tone2, v_to_u=False)`

```
将 :py:attr:`~pypinyin.Style.TONE2` 风格的拼音转换为
:py:attr:`~pypinyin.Style.TONE3` 风格的拼音

:param tone2: :py:attr:`~pypinyin.Style.TONE2` 风格的拼音
:param v_to_u: 是否使用 ``ü`` 代替原来的 ``v``，
               当为 False 时结果中将使用 ``v`` 表示 ``ü``
:return: :py:attr:`~pypinyin.Style.TONE3` 风格的拼音

Usage::

  >>> from pypinyin.contrib.tone_convert import tone2_to_tone3
  >>> tone2_to_tone3('zho1ng')
  'zhong1'
  >>> tone2_to_tone3('lüe4')
  'lve4'
  >>> tone2_to_tone3('lüe4', v_to_u=True)
  'lüe4'
```

## `tone3_to_normal(tone3, v_to_u=False)`

```
将 :py:attr:`~pypinyin.Style.TONE3` 风格的拼音转换为
:py:attr:`~pypinyin.Style.NORMAL` 风格的拼音

:param tone3: :py:attr:`~pypinyin.Style.TONE3` 风格的拼音
:param v_to_u: 是否使用 ``ü`` 代替原来的 ``v``，
               当为 False 时结果中将使用 ``v`` 表示 ``ü``
:return: :py:attr:`~pypinyin.Style.NORMAL` 风格的拼音

Usage::

  >>> from pypinyin.contrib.tone_convert import tone3_to_normal
  >>> tone3_to_normal('zhong1')
  'zhong'
  >>> tone3_to_normal('lüe4')
  'lve'
  >>> tone3_to_normal('lüe4', v_to_u=True)
  'lüe'
```

## `tone3_to_tone(tone3)`

```
将 :py:attr:`~pypinyin.Style.TONE3` 风格的拼音转换为
:py:attr:`~pypinyin.Style.TONE` 风格的拼音

:param tone3: :py:attr:`~pypinyin.Style.TONE3` 风格的拼音
:return: :py:attr:`~pypinyin.Style.TONE` 风格的拼音

Usage::

  >>> from pypinyin.contrib.tone_convert import tone3_to_tone
  >>> tone3_to_tone('zhong1')
  'zhōng'
```

## `tone3_to_tone2(tone3, v_to_u=False)`

```
将 :py:attr:`~pypinyin.Style.TONE3` 风格的拼音转换为
:py:attr:`~pypinyin.Style.TONE2` 风格的拼音

:param tone3: :py:attr:`~pypinyin.Style.TONE3` 风格的拼音
:param v_to_u: 是否使用 ``ü`` 代替原来的 ``v``，
               当为 False 时结果中将使用 ``v`` 表示 ``ü``
:return: :py:attr:`~pypinyin.Style.TONE2` 风格的拼音

Usage::

  >>> from pypinyin.contrib.tone_convert import tone3_to_tone2
  >>> tone3_to_tone2('zhong1')
  'zho1ng'
  >>> tone3_to_tone2('lüe4')
  'lve4'
  >>> tone3_to_tone2('lüe4', v_to_u=True)
  'lüe4'
```
