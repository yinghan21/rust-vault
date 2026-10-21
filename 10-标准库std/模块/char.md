---
title: "std::char"
type: std-模块
module: char
stable: "1.0.0"
unstable: false
tags:
  - std/模块
  - std/类型
aliases:
  - char 模块
  - 字符处理
一句话: 单个 Unicode 标量值的工具模块：码点与字符互转、大小写映射、转义与 UTF-16 解码。
---

# std::char

> [!abstract] 一句话
> `std::char` 提供 `char` 原始类型的配套工具：与 `u32` 的码点转换、`from_digit`、`decode_utf16`，以及大小写与转义相关的迭代器类型。

## 模块简介

`char` 表示单个 Unicode 标量值，是 `U+0000..=U+D7FF` 与 `U+E000..=U+10FFFF` 区间内的码点，固定占 4 字节。它不是「一个字」：一个用户可见的字符（字素簇）可能由多个 `char` 组成，例如 emoji 组合序列或带变音符的字母。

这个模块存在的技术原因是：`char` 的绝大多数方法（`is_alphabetic`、`to_digit`、`to_ascii_uppercase`、`len_utf8` 等）都直接定义在原始类型上，只有无法写成关联函数的部分才放在模块里——主要是 `u32` 与 `char` 之间的转换函数、UTF-16 解码，以及 `to_uppercase`、`escape_default` 等方法返回的迭代器类型。

`MAX`、`REPLACEMENT_CHARACTER`、`UNICODE_VERSION` 以及 `from_u32` 等少数名字在模块级仍然保留，但官方文档已建议改写成 `char::MAX`、`char::from_u32` 这类关联项形式，新代码直接写后者即可。

需要注意大小写转换的结果是迭代器而非单个 `char`：一个字符最多可以映射成多个字符（`ß` 的大写是 `SS`），所以必须 `collect` 成字符串。

## 快速上手

```rust
fn main() {
    // u32 码点转 char：代理区与越界码点返回 None
    assert_eq!(char::from_u32(0x1F600), Some('😀'));
    assert_eq!(char::from_u32(0xD800), None);

    // 数字字符与数值互转
    assert_eq!(char::from_digit(15, 16), Some('f'));
    assert_eq!('7'.to_digit(10), Some(7));

    // 大小写转换：结果可能是多个字符
    let upper: String = 'ß'.to_uppercase().collect();
    assert_eq!(upper, "SS");

    // 转义序列：调试输出与源码字面量都能用
    let escaped: String = '\n'.escape_default().collect();
    assert_eq!(escaped, "\\n");

    let unicode: String = '中'.escape_unicode().collect();
    assert_eq!(unicode, "\\u{4e2d}");

    // UTF-16 解码：孤立代理项会变成 Err
    let decoded: String = char::decode_utf16([0xD83D, 0xDE00])
        .map(|r| r.unwrap_or(char::REPLACEMENT_CHARACTER))
        .collect();
    assert_eq!(decoded, "😀");
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| `char::from_u32` | 把 `u32` 码点转换为 `char`，非法码点返回 `None`。 |
| `char::from_u32_unchecked` | 跳过有效性检查，非法码点属于 UB。 |
| `char::from_digit` | 把 0–35 的数值按给定进制转为字符。 |
| `char::decode_utf16` | 把 `u16` 序列按 UTF-16 解码为字符迭代器。 |
| `char::REPLACEMENT_CHARACTER` | 解码失败时使用的替换字符 `U+FFFD`。 |
| `char::MAX` | `char` 能表示的最大码点 `'\u{10FFFF}'`。 |
| `char::UNICODE_VERSION` | 大小写等方法所依据的 Unicode 版本。 |
| `char::EscapeUnicode` | `escape_unicode` 返回的迭代器，输出 `\u{...}`。 |
| `char::EscapeDefault` | `escape_default` 返回的迭代器，输出常见转义。 |
| `char::ToUppercase` / `char::ToLowercase` | 大小写映射迭代器，可能产出多个字符。 |
| `char::CharTryFromError` | `u32` 转 `char` 失败时的错误类型。 |
| `char::ParseCharError` | 解析字符失败时的错误类型。 |
| `char::DecodeUtf16Error` | UTF-16 解码失败时的错误类型。 |

## 注意事项

> [!tip] `char` 不等于「一个字」
> 一个字符可能由多个 `char` 组成（emoji 组合、带变音符的字母）。按用户感知的字符切分需要字素簇算法，标准库只提供 Unicode 标量值这一层。

> [!danger] 不能按字符下标索引字符串
> `&s[i]` 是字节索引，不是字符索引，切在多字节字符中间会 panic；按字符遍历请用 `s.chars()`。注意 `chars().nth(n)` 是线性时间，频繁随机访问要先 `collect::<Vec<char>>()`。

> [!warning] 模块级名字已让位给关联项
> `std::char::MAX`、`std::char::from_u32` 这类模块级写法仍然可用，但文档建议写成 `char::MAX`、`char::from_u32`，避免与导入冲突。

## 相关

- [[primitive.char|Type char]]：原始类型页，字符的绝大部分方法都定义在那里。
- [[str|std::str 模块]]：字符串切片与 UTF-8 字节处理。
- [[string|std::string 模块]]：可增长的 UTF-8 字符串 `String`。
- [[13-字符串|字符串]]：字符、字节、UTF-8 与字素簇的关系。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 20 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`CharTryFromError`](https://doc.rust-lang.org/std/char/struct.CharTryFromError.html)
- [`DecodeUtf16`](https://doc.rust-lang.org/std/char/struct.DecodeUtf16.html)
- [`DecodeUtf16Error`](https://doc.rust-lang.org/std/char/struct.DecodeUtf16Error.html)
- [`EscapeDebug`](https://doc.rust-lang.org/std/char/struct.EscapeDebug.html)
- [`EscapeDefault`](https://doc.rust-lang.org/std/char/struct.EscapeDefault.html)
- [`EscapeUnicode`](https://doc.rust-lang.org/std/char/struct.EscapeUnicode.html)
- [`ParseCharError`](https://doc.rust-lang.org/std/char/struct.ParseCharError.html)
- [`ToLowercase`](https://doc.rust-lang.org/std/char/struct.ToLowercase.html)
- [`ToUppercase`](https://doc.rust-lang.org/std/char/struct.ToUppercase.html)
- [`TryFromCharError`](https://doc.rust-lang.org/std/char/struct.TryFromCharError.html)
- [`ToCasefold`](https://doc.rust-lang.org/std/char/struct.ToCasefold.html)
- [`ToTitlecase`](https://doc.rust-lang.org/std/char/struct.ToTitlecase.html)

### 枚举

- [`CharCase`](https://doc.rust-lang.org/std/char/enum.CharCase.html)

### 函数

- [`decode_utf16`](https://doc.rust-lang.org/std/char/fn.decode_utf16.html)
- [`from_digit`](https://doc.rust-lang.org/std/char/fn.from_digit.html)
- [`from_u32`](https://doc.rust-lang.org/std/char/fn.from_u32.html)
- [`from_u32_unchecked`](https://doc.rust-lang.org/std/char/fn.from_u32_unchecked.html)

### 常量

- [`MAX`](https://doc.rust-lang.org/std/char/constant.MAX.html)
- [`REPLACEMENT_CHARACTER`](https://doc.rust-lang.org/std/char/constant.REPLACEMENT_CHARACTER.html)
- [`UNICODE_VERSION`](https://doc.rust-lang.org/std/char/constant.UNICODE_VERSION.html)

<!-- END AUTO ITEMS -->
