---
title: "std::primitive::char"
type: std-条目
kind: 原始类型
module: char
slug: primitive.char
stable: "1.0.0"
tags:
  - std/类型
  - rust/基础
aliases:
  - char
一句话: 单个 Unicode 标量值，固定占 4 字节，支持字符分类、大小写映射与 UTF 编码。
---

# `char`

> [!abstract] 一句话
> `char` 表示一个 **Unicode 标量值**（码点），固定占 4 字节；它是一个字符，而不是一个 UTF-8 字节。

## 简介

`char` 是语言内建的字符类型，值域是 Unicode 标量值：码点 `U+0000..=U+10FFFF` 中排除代理区 `U+D800..=U+DFFF`。所以 `'\u{D800}'`、`'\u{DFFF}'`、`'\u{110000}'` 都是编译错误，`char::from_u32` 遇到这些值返回 `None`。

**固定 4 字节，但编码长度不固定**：`size_of::<char>()` 永远是 4，而同一个字符写成 UTF-8 可能是 1–4 字节（`'a'` 1 字节、`'中'` 3 字节、`'😀'` 4 字节），写成 UTF-16 可能是 1–2 个码元。`char` 存的是码点，不是某一种编码下的字节。

**与 `u8` 的区别**：

- `u8` 是一个字节，范围 0–255；`char` 是一个码点，范围到 `0x10FFFF`。
- 字面量不同：`b'a'` 是 `u8`，`'a'` 是 `char`；`&[u8]` 不校验编码，`&str` 保证是合法 UTF-8。
- 转换不同：`'a' as u8` 只对 ASCII 有意义，`'中' as u8` 会把码点截断成低 8 位，得到的不是 UTF-8 字节；要字节请用 `encode_utf8`。

**不是「一个字」**：`char` 是码点，用户眼中的一个字符（字素簇）可能由多个 `char` 组成，例如 `e` 加组合重音，或由 ZWJ 连接的 emoji 序列。按字素切分需要额外算法，标准库只提供码点这一层。

字面量写法：`'a'`、`'\n'`、`'\''`、`'\u{4e2d}'`；**空字符 `''` 不合法**，`char` 不能表示「没有字符」，这种情况用 `Option<char>`。

这 38 个稳定方法都定义在 `char` 原始类型上，配套的模块级条目见 [[char|std::char]]。

## 常用方法

共 38 个稳定方法，按判断、转换、大小写、编码分成 4 组。

### 判断

| 方法 | 说明 |
| --- | --- |
| `is_alphabetic()` | 判断是否具有 Unicode 字母属性。 |
| `is_lowercase()` | 判断是否具有 Unicode 小写属性。 |
| `is_uppercase()` | 判断是否具有 Unicode 大写属性。 |
| `is_numeric()` | 判断是否属于 Unicode 数字类。 |
| `is_alphanumeric()` | 判断是否为字母或数字。 |
| `is_whitespace()` | 判断是否为 Unicode 空白字符。 |
| `is_control()` | 判断是否为 Unicode 控制码。 |
| `is_digit(radix)` | 判断是否为指定进制下的数字。 |
| `is_ascii()` | 判断是否落在 ASCII 范围内。 |
| `is_ascii_alphabetic()` | 判断是否为 ASCII 字母。 |
| `is_ascii_uppercase()` | 判断是否为 ASCII 大写字母。 |
| `is_ascii_lowercase()` | 判断是否为 ASCII 小写字母。 |
| `is_ascii_alphanumeric()` | 判断是否为 ASCII 字母或数字。 |
| `is_ascii_digit()` | 判断是否为 ASCII 十进制数字。 |
| `is_ascii_hexdigit()` | 判断是否为 ASCII 十六进制数字。 |
| `is_ascii_punctuation()` | 判断是否为 ASCII 标点或符号。 |
| `is_ascii_graphic()` | 判断是否为 ASCII 可见图形字符。 |
| `is_ascii_whitespace()` | 判断是否为 ASCII 空白字符。 |
| `is_ascii_control()` | 判断是否为 ASCII 控制字符。 |

### 转换

| 方法 | 说明 |
| --- | --- |
| `from_u32(i)` | 把 `u32` 码点转为字符，非法返回 `None`。 |
| `from_u32_unchecked(i)` | 跳过校验转换码点，非法输入是 UB。 |
| `from_digit(num, radix)` | 把数值按给定进制转为数字字符。 |
| `to_digit(radix)` | 把字符按给定进制转为数值。 |

### 大小写

| 方法 | 说明 |
| --- | --- |
| `to_lowercase()` | 返回 Unicode 小写映射的迭代器。 |
| `to_uppercase()` | 返回 Unicode 大写映射的迭代器。 |
| `to_ascii_uppercase()` | 返回 ASCII 大写副本，非 ASCII 不变。 |
| `to_ascii_lowercase()` | 返回 ASCII 小写副本，非 ASCII 不变。 |
| `make_ascii_uppercase()` | 原地把 ASCII 字母改为大写。 |
| `make_ascii_lowercase()` | 原地把 ASCII 字母改为小写。 |
| `eq_ignore_ascii_case(other)` | 判断两字符忽略 ASCII 大小写是否相等。 |

### 编码

| 方法 | 说明 |
| --- | --- |
| `len_utf8()` | 返回 UTF-8 编码所需字节数。 |
| `len_utf16()` | 返回 UTF-16 编码所需码元数。 |
| `encode_utf8(dst)` | 把字符编码成 UTF-8 写入缓冲区。 |
| `encode_utf16(dst)` | 把字符编码成 UTF-16 写入缓冲区。 |
| `decode_utf16(iter)` | 把 `u16` 序列迭代解码为字符。 |
| `escape_unicode()` | 返回输出 `\u{...}` 转义的迭代器。 |
| `escape_debug()` | 返回输出调试转义的迭代器。 |
| `escape_default()` | 返回输出字面量转义的迭代器。 |

## 示例

### 存储与编码

```rust
fn main() {
    let c = '中';

    // char 固定 4 字节，UTF-8 编码却是 3 字节
    assert_eq!(std::mem::size_of::<char>(), 4);
    assert_eq!(c.len_utf8(), 3);
    assert_eq!(c.len_utf16(), 1);
    assert_eq!('😀'.len_utf8(), 4);
    assert_eq!('😀'.len_utf16(), 2);

    // 编码到缓冲区，缓冲区要留够 len_utf8() 的空间
    let mut buf = [0u8; 4];
    let encoded = c.encode_utf8(&mut buf);
    assert_eq!(encoded, "中");
    assert_eq!(&buf[..3], "中".as_bytes());

    let mut units = [0u16; 2];
    let written = '😀'.encode_utf16(&mut units);
    assert_eq!(written.len(), 2);
    assert_eq!(units, [0xD83D, 0xDE00]);
}
```

### 判断与转换

```rust
fn main() {
    // Unicode 层判断
    assert!('好'.is_alphabetic());
    assert!('٣'.is_numeric());
    assert!('好'.is_alphanumeric());
    assert!('\u{3000}'.is_whitespace());

    // ASCII 层判断更严格
    assert!('a'.is_ascii_alphabetic());
    assert!(!'好'.is_ascii_alphabetic());
    assert!('F'.is_ascii_hexdigit());
    assert!('!'.is_ascii_punctuation());

    // 字符与数值互转
    assert_eq!('7'.to_digit(10), Some(7));
    assert_eq!('f'.to_digit(16), Some(15));
    assert_eq!('g'.to_digit(16), None);
    assert_eq!(char::from_digit(15, 16), Some('f'));

    // 码点转字符：代理区与越界码点会被拒绝
    assert_eq!(char::from_u32(0x1F600), Some('😀'));
    assert_eq!(char::from_u32(0xD800), None);
    assert_eq!(char::from_u32(0x11_0000), None);
}
```

### 大小写

```rust
fn main() {
    // Unicode 映射：结果可能有多个字符，必须收集
    let upper: String = 'ß'.to_uppercase().collect();
    assert_eq!(upper, "SS");
    let lower: String = 'İ'.to_lowercase().collect();
    assert_eq!(lower, "i\u{307}");

    // ASCII 映射：返回单个 char，非 ASCII 原样返回
    assert_eq!('a'.to_ascii_uppercase(), 'A');
    assert_eq!('A'.to_ascii_lowercase(), 'a');
    assert_eq!('中'.to_ascii_uppercase(), '中');

    let mut c = 'x';
    c.make_ascii_uppercase();
    assert_eq!(c, 'X');
    assert!('A'.eq_ignore_ascii_case(&'a'));
}
```

### 转义与 UTF-16 解码

```rust
fn main() {
    // 三种转义：escape_debug 面向调试输出，escape_default 面向字面量
    let debug: String = '\n'.escape_debug().collect();
    assert_eq!(debug, "\\n");
    let default: String = '\n'.escape_default().collect();
    assert_eq!(default, "\\n");
    let unicode: String = '中'.escape_unicode().collect();
    assert_eq!(unicode, "\\u{4e2d}");

    // 孤立代理项会被报告为 Err，而不是直接 panic
    let decoded: String = char::decode_utf16([0xD83D, 0xDE00, 0xDC00])
        .map(|r| r.unwrap_or(char::REPLACEMENT_CHARACTER))
        .collect();
    assert_eq!(decoded, "😀\u{FFFD}");
}
```

## 常见陷阱

1. **用 `as u8` 取字节**：`'中' as u8` 只保留码点低 8 位（得到 `0x2D`），不是 UTF-8 字节；要字节用 `encode_utf8` 写入缓冲区。
2. **以为 `char` 就是 1 字节**：`char` 固定 4 字节，UTF-8 长度由 `len_utf8()` 决定，中文 3 字节、emoji 4 字节。
3. **混用 Unicode 判断与 ASCII 判断**：`'中'.is_alphabetic()` 是 `true`，`'中'.is_ascii_alphabetic()` 是 `false`；协议、文件名等只认 ASCII 的场景要用 `is_ascii_*`。
4. **把 `to_uppercase` 当单字符转换**：它返回迭代器，`'ß'` 转大写是 `"SS"` 两个字符；只要单个 `char` 时用 `to_ascii_uppercase()`。
5. **进制参数超过 36**：`to_digit`、`is_digit`、`from_digit` 的 `radix` 大于 36 会 panic。
6. **对代理区调用 `from_u32_unchecked`**：`char::from_u32` 拒绝 `U+D800..=U+DFFF`，`from_u32_unchecked` 传这些值是未定义行为。
7. **把 `char` 当字素簇**：`"é"` 可能是 `e` 加组合重音两个 `char`，emoji 家庭由多个 `char` 与 ZWJ 组成，按字符计数用 `chars()` 会偏多。

## 相关

- [[char|std::char]]：`char` 的配套模块，含 UTF-16 解码与转义迭代器类型。
- [[primitive.str|Type str]]：UTF-8 字符串切片，`chars()` 迭代产出 `char`。
- [[string.String|String]]：可增长的 UTF-8 字符串，与 `char` 集合互转。
- [[u8|std::u8]]：单字节类型，`char` 编码后的结果就是字节序列。
- [[primitive|std::primitive]]：`char` 所属的原始类型模块。
- [[13-字符串|字符串]]：字符、字节与 UTF-8 编码的整体关系。
