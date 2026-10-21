---
title: "std::str"
type: std-模块
module: str
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - str
  - 字符串切片模块
一句话: 原始类型 str 的配套模块：UTF-8 文本切片的借用语义、切片边界规则与字符/字节迭代器。
---

# std::str

> [!abstract] 一句话
> `std::str` 是原始类型 [[primitive.str|str]]（写作 `&str`）的配套模块：它本身不拥有数据，只是「保证合法 UTF-8 的一段字节」，这里放它的字符迭代器、字节校验函数与解析特质。

## 模块简介

`str` 是 Rust 的字符串原始类型，但和 `i32` 不同，它是**动态大小类型**：长度要到运行时才知道，所以不能按值使用，只能以 `&str`（或 `&mut str`、`Box<str>`、`Rc<str>` 等形式）出现。`&str` 与切片的胖指针结构相同——地址 + 字节长度——指向的是一段**已经验证过 UTF-8 合法性**的字节。这就是为什么本章要先讲 [[slice|std::slice]]：`&str` 本质上就是「带 UTF-8 不变量的 `&[u8]`」，`s.as_bytes()` 拿到的正是那个字节切片。

「只借用、不拥有」是 `&str` 最重要的性质。字符串字面量 `"hello"` 的类型就是 `&'static str`，直接嵌在二进制里、零开销；从 [[string.String|String]] 借出 `&s` 也不复制任何字节。所以函数参数写 `&str` 是最通用的选择：字面量、`String` 的借用、切片结果都能传进去，而且不夺走所有权。需要拥有、需要修改、需要拼接时才用 `String`。

与 C 字符串、Java 字符串最大的不同是**索引单位**：`len()` 返回字节数，`chars().count()` 才是字符数。中文一个字通常占 3 个字节，emoji 可能占 4 个，所以 `s[0]` 这种按字节的整数索引根本不允许——`&s[..n]` 必须落在**字符边界**上，切在半个字符中间会 panic。要按位置访问，用 `chars()`、`char_indices()`（给出每个字符的字节偏移），或 `get(range)` 这种返回 `Option` 的安全切片。

模块提供的另一大块是**迭代器**：`Chars`、`CharIndices`、`Bytes`、`Lines`、`Split`、`SplitWhitespace`、`Matches`、`Utf8Chunks` 等，它们通常由同名方法创建，几乎不用手写类型。还有 `str::from_utf8` 这类**字节转字符串**的校验函数（失败给 `Utf8Error`，`from_utf8_unchecked` 则跳过校验、属于 `unsafe`），以及 [[str.FromStr|FromStr]] 特质——`"42".parse::<i32>()` 背后就是它在工作。

## 快速上手

```rust
fn main() {
    let s = "你好, Rust";

    // len() 数的是字节，chars().count() 才是字符数
    assert_eq!(s.len(), 12);
    assert_eq!(s.chars().count(), 8);

    // 按字节切片必须落在 char 边界上，否则 panic
    assert_eq!(&s[..3], "你");
    assert_eq!(&s[8..], "Rust");
    assert_eq!(s.get(..1), None); // 0..1 切开了「你」的三个字节
    assert_eq!(s.get(..3), Some("你"));

    // 三种视图：字节、字符、字符加字节偏移
    assert_eq!(s.as_bytes().len(), 12);
    let first: Vec<(usize, char)> = s.char_indices().take(2).collect();
    assert_eq!(first, vec![(0, '你'), (3, '好')]);

    // 从字节切片校验出 &str，非法 UTF-8 会失败
    assert_eq!(std::str::from_utf8(b"hi"), Ok("hi"));
    assert!(std::str::from_utf8(&[0x66, 0xff]).is_err());

    // parse() 背后是 FromStr 特质
    let n: i32 = "42".parse().unwrap();
    assert_eq!(n, 42);

    // 行迭代：\n 与 \r\n 都能识别，末尾换行不产生空行
    let text = "a\nb\r\nc";
    assert_eq!(text.lines().count(), 3);

    // 分割、匹配、修剪
    assert_eq!("a,b,,c".split(',').count(), 4);
    assert_eq!("abab".matches("ab").count(), 2);
    assert_eq!("  hi  ".trim(), "hi");

    // 改名类操作返回新 String，原 &str 保持不变
    assert_eq!(s.to_uppercase(), "你好, RUST");
    assert!(s.contains("Rust"));
    assert!(s.starts_with("你好"));

    println!("字符数 = {}", s.chars().count());
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[primitive.str\|str]] | 原始类型 `str`，全部字符串方法的所在地。 |
| `str::from_utf8` | 校验字节切片并转成 `&str`。 |
| `str::from_utf8_mut` | 同上，返回 `&mut str`。 |
| `str::Chars` | `chars()` 的返回类型，按 Unicode 标量迭代。 |
| `str::CharIndices` | `char_indices()` 的返回类型，附带字节偏移。 |
| `str::Bytes` | `bytes()` 的返回类型，逐个产出 `u8`。 |
| `str::Lines` | `lines()` 的返回类型，按行切分。 |
| `str::SplitWhitespace` | `split_whitespace()` 的返回类型，按空白切分。 |
| `str::Split` | `split(pat)` 的返回类型，按分隔符切分。 |
| `str::SplitN` | `splitn(n, pat)` 的返回类型，限制切分次数。 |
| `str::SplitTerminator` | `split_terminator(pat)` 的返回类型，忽略尾部空串。 |
| `str::Matches` | `matches(pat)` 的返回类型，产出所有匹配片段。 |
| `str::MatchIndices` | `match_indices(pat)` 的返回类型，附带位置。 |
| `str::Utf8Error` | 字节转字符串失败时的错误类型。 |
| [[str.FromStr\|FromStr]] | 从字符串解析出值的特质，`parse()` 依赖它。 |

## 注意事项

> [!warning] `len()` 是字节数
> `"你好".len()` 是 6 而不是 2。按字节数分配缓冲区、按字节数截断日志时很容易把多字节字符切坏。要字符数用 `chars().count()`，要显示宽度还得考虑东亚宽字符（标准库不提供，需要外部 crate）。

> [!danger] 字符串切片会 panic
> `&s[0..1]` 在 `s` 含中文时直接 panic：`byte index 1 is not a char boundary`。不确定边界时用 `s.get(range)`（返回 `Option<&str>`）、`char_indices()` 或先 `s.char_indices()` 找到偏移。`from_utf8_unchecked` / `from_raw_parts` 都是 `unsafe`，违反不变量就是未定义行为。

> [!tip] `&str` 还是 `String`
> 只读参数一律写 `&str`，别写 `&String`（多一层间接、还限制了调用者）；要返回新字符串、要拼接、要长期拥有才用 [[string|std::string]] 的 `String`。两者互转很便宜：`String::from(&str)` 会分配，`&string` / `string.as_str()` 不分配。

## 相关

- [[primitive.str|str]]：`&str` 的全部方法（`find`、`split_at`、`trim`、`parse` 等）。
- [[string|std::string]]：`String`，可增长的 UTF-8 字符串，`&str` 的所有者版本。
- [[slice|std::slice]]：切片语义，`&str` 与 `&[u8]` 的关系。
- [[str.FromStr|FromStr]]：自定义类型如何支持 `parse()`。
- [[13-字符串|字符串]]：`String` / `&str` / 编码的完整学习笔记。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 34 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`Bytes`](https://doc.rust-lang.org/std/str/struct.Bytes.html)
- [`CharIndices`](https://doc.rust-lang.org/std/str/struct.CharIndices.html)
- [`Chars`](https://doc.rust-lang.org/std/str/struct.Chars.html)
- [`EncodeUtf16`](https://doc.rust-lang.org/std/str/struct.EncodeUtf16.html)
- [`EscapeDebug`](https://doc.rust-lang.org/std/str/struct.EscapeDebug.html)
- [`EscapeDefault`](https://doc.rust-lang.org/std/str/struct.EscapeDefault.html)
- [`EscapeUnicode`](https://doc.rust-lang.org/std/str/struct.EscapeUnicode.html)
- [`Lines`](https://doc.rust-lang.org/std/str/struct.Lines.html)
- [`LinesAny`](https://doc.rust-lang.org/std/str/struct.LinesAny.html)
- [`MatchIndices`](https://doc.rust-lang.org/std/str/struct.MatchIndices.html)
- [`Matches`](https://doc.rust-lang.org/std/str/struct.Matches.html)
- [`ParseBoolError`](https://doc.rust-lang.org/std/str/struct.ParseBoolError.html)
- [`RMatchIndices`](https://doc.rust-lang.org/std/str/struct.RMatchIndices.html)
- [`RMatches`](https://doc.rust-lang.org/std/str/struct.RMatches.html)
- [`RSplit`](https://doc.rust-lang.org/std/str/struct.RSplit.html)
- [`RSplitN`](https://doc.rust-lang.org/std/str/struct.RSplitN.html)
- [`RSplitTerminator`](https://doc.rust-lang.org/std/str/struct.RSplitTerminator.html)
- [`Split`](https://doc.rust-lang.org/std/str/struct.Split.html)
- [`SplitAsciiWhitespace`](https://doc.rust-lang.org/std/str/struct.SplitAsciiWhitespace.html)
- [`SplitInclusive`](https://doc.rust-lang.org/std/str/struct.SplitInclusive.html)
- [`SplitN`](https://doc.rust-lang.org/std/str/struct.SplitN.html)
- [`SplitTerminator`](https://doc.rust-lang.org/std/str/struct.SplitTerminator.html)
- [`SplitWhitespace`](https://doc.rust-lang.org/std/str/struct.SplitWhitespace.html)
- [`Utf8Chunk`](https://doc.rust-lang.org/std/str/struct.Utf8Chunk.html)
- [`Utf8Chunks`](https://doc.rust-lang.org/std/str/struct.Utf8Chunks.html)
- [`Utf8Error`](https://doc.rust-lang.org/std/str/struct.Utf8Error.html)

### 特质

- [[str.FromStr|`FromStr`]]

### 函数

- [`from_boxed_utf8_unchecked`](https://doc.rust-lang.org/std/str/fn.from_boxed_utf8_unchecked.html)
- [`from_utf8`](https://doc.rust-lang.org/std/str/fn.from_utf8.html)
- [`from_utf8_mut`](https://doc.rust-lang.org/std/str/fn.from_utf8_mut.html)
- [`from_utf8_unchecked`](https://doc.rust-lang.org/std/str/fn.from_utf8_unchecked.html)
- [`from_utf8_unchecked_mut`](https://doc.rust-lang.org/std/str/fn.from_utf8_unchecked_mut.html)
- [`from_raw_parts`](https://doc.rust-lang.org/std/str/fn.from_raw_parts.html)
- [`from_raw_parts_mut`](https://doc.rust-lang.org/std/str/fn.from_raw_parts_mut.html)

<!-- END AUTO ITEMS -->
