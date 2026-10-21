---
title: "std::ascii"
type: std-模块
module: ascii
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - ascii
一句话: 只作用于 ASCII 子集的字节处理工具，含转义迭代器与 ASCII 字符类型。
---

# std::ascii

> [!abstract] 一句话
> `std::ascii` 用来处理「只关心 ASCII」的场景：把字节转成转义文本，以及在一百多个 ASCII 字符的范围内做判断与转换。

## 模块简介

Rust 的字符串默认按 UTF-8 处理，`to_uppercase`、`chars()` 这些都是完整 Unicode 语义。但很多场合只该看 ASCII：解析 HTTP 头、十六进制串、自定义协议的字段名、日志里的可见字符。对一个非 ASCII 字符按 Unicode 规则做大写转换，可能一下子变成多个字符，长度都变了——这时候需要的是「只碰 ASCII、其余原样保留」的操作。

模块本体很小，公开的东西就四样。`escape_default` 接收一个字节，返回 `EscapeDefault` 迭代器，逐字节产出转义后的形式（`\n`、`\t`、`\"`、`\'`，不可见字节变成 `\xNN`），这正是调试打印时看到的那种文本。`Char` 是一个只覆盖 U+0000 到 U+007F 的枚举。`AsciiExt` 是早期的 ASCII 扩展方法 trait，已经废弃。

需要强调的是：**稳定版里几乎没有直接可用的一等公民**。`Char` 目前仍属于未稳定的接口，需要在 nightly 上加特性开关；`AsciiExt` 里的方法早都搬到了 `u8`、`char`、`str` 身上。所以日常写代码时，真正用的是 `b.is_ascii()`、`s.eq_ignore_ascii_case(...)`、`c.to_ascii_uppercase()` 这类固有方法，而本模块主要提供 `escape_default` 与 `EscapeDefault`。

## 快速上手

```rust
use std::ascii::{escape_default, EscapeDefault};

fn main() {
    // escape_default 逐字节产出转义结果，用于生成可读的调试文本
    let newline: String = escape_default(b'\n').map(char::from).collect();
    assert_eq!(newline, "\\n");

    // 迭代器可以链式处理：把引号、制表符一起转义
    let raw = b"a\"b\tc";
    let shown: String = raw
        .iter()
        .copied()
        .flat_map(escape_default)
        .map(char::from)
        .collect();
    assert_eq!(shown, "a\\\"b\\tc");

    // 显式标注类型，说明返回的就是 EscapeDefault
    let single_quote: EscapeDefault = escape_default(b'\'');
    let quoted: String = single_quote.map(char::from).collect();
    assert_eq!(quoted, "\\'");

    // 常见做法：只对 ASCII 子集做判断，避免误伤多字节字符
    let text = "Rust 2021";
    assert!(text.bytes().all(|b| b.is_ascii()));
    assert!("RUST".eq_ignore_ascii_case("rust"));

    println!("{newline} / {shown} / {quoted}");
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| `ascii::escape_default` | 把单个字节转成转义后的可读形式。 |
| `ascii::EscapeDefault` | `escape_default` 返回的迭代器，逐字节产出转义结果。 |
| `ascii::Char` | 只表示 U+0000 至 U+007F 的枚举，尚未稳定。 |
| `ascii::AsciiExt` | 早期的 ASCII 扩展方法 trait，已废弃，方法并入固有实现。 |
| `u8::is_ascii` | 判断单个字节是否在 ASCII 范围内。 |
| `u8::to_ascii_uppercase` | 只对 ASCII 字母做大小写转换，其余原样返回。 |
| `str::eq_ignore_ascii_case` | 忽略 ASCII 大小写比较两个字符串。 |
| `[u8]::is_ascii` | 判断整段字节是否全部属于 ASCII。 |

## 注意事项

> [!warning] `AsciiExt` 已经废弃
> 不要再 `use std::ascii::AsciiExt`。它当年的方法现在都是 `u8`、`char`、`str` 的固有方法，直接调用即可；路径导入只会带来废弃警告。

> [!danger] 「只转 ASCII」与「转 Unicode」是两件事
> `to_ascii_uppercase` 遇到非 ASCII 字符会原样返回，看起来像「没生效」；真正的 Unicode 大小写转换要用 `to_uppercase`，它返回的是另一个 `String`，长度可能变化。处理用户输入时先想清楚要哪一种。

> [!tip] 先判定再走快路径
> 处理外部数据时，可以先用 `is_ascii()` 判断整段内容是否纯 ASCII：是就走字节级快速路径，否则回退到 UTF-8 语义。这样既安全又不会破坏多字节字符。

## 相关

- [[模块索引]]
- [[str|std::str 模块]]：UTF-8 字符串的完整操作。
- [[u8|std::u8 模块]]：字节类型上的 ASCII 判断方法。
- [[13-字符串|字符串]]：`String` 与 `&str` 的日常用法。
- [[char|std::char 模块]]：单个字符的大小写与分类方法。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 4 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`EscapeDefault`](https://doc.rust-lang.org/std/ascii/struct.EscapeDefault.html)

### 枚举

- [`Char`](https://doc.rust-lang.org/std/ascii/enum.Char.html)

### 特质

- [`AsciiExt`](https://doc.rust-lang.org/std/ascii/trait.AsciiExt.html)

### 函数

- [`escape_default`](https://doc.rust-lang.org/std/ascii/fn.escape_default.html)

<!-- END AUTO ITEMS -->
