---
title: "std::string"
type: std-模块
module: string
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - string
  - String 模块
一句话: 可增长的 UTF-8 字符串 String：堆上拥有数据、可修改、可拼接，以及相关的错误类型与 ToString。
---

# std::string

> [!abstract] 一句话
> `std::string` 定义 [[string.String|String]]：一个堆上分配、可以增长和修改、始终保证合法 UTF-8 的字符串类型，外加转换失败的错误类型和 [[string.ToString|ToString]]。

## 模块简介

`String` 在内存里就是「`Vec<u8>` + 一条不变量」：底层是一段连续字节缓冲区，长度和容量可以增长，但内容**任何时候都必须是合法 UTF-8**。这条不变量由 `String` 自己维护——你没法像 C 那样随便往中间塞一个非法字节；想绕过只有 `unsafe` 的 `as_mut_vec`，或者用 `String::from_utf8` 显式校验。因此 `String` 与 [[primitive.str|str]] 的 `&str` 视图之间切换几乎是零成本的：`&s` 或 `s.as_str()` 直接借出那段字节，不会复制。

和 [[str|std::str]] 的分工是本模块的第一课：`&str` 是**借用**的只读文本（字面量也是它），`String` 是**拥有**的、可增长的可变文本。`String` 实现了 `Deref<Target = str>`，所以 `&str` 上的方法（`len`、`contains`、`split`、`trim`、`find`…）都能直接在 `String` 上调用；反过来要 `String` 时，`String::from`、`to_string()`、`to_owned()`、`format!` 任选——前两个会分配。

改字符串主要靠几个方法：`push_str` 追加一段 `&str`，`push` 追加一个 `char`，`insert` / `insert_str` 在指定字节位置插入，`replace_range` 替换区间，`truncate` 截断，`drain` 删除区间并把内容交出来，`retain` 按条件保留字符。拼接除了 `+`（会拿走左边 `String` 的所有权）和 `format!`（不消耗任何参数），还可以 `push_str` 循环追加。注意「字节位置」：`insert` / `drain` / `truncate` 的参数都必须是字符边界，否则 panic。

模块里剩下的都是配角：`Drain`（`drain` 返回的迭代器）、`FromUtf8Error` / `FromUtf16Error`（`from_utf8` / `from_utf16` 失败时的错误）、`ParseError`（`String::from_str` 永不失败的别名），以及 [[string.ToString|ToString]]——任何实现了 `Display` 的类型都自动获得 `to_string()`。

## 快速上手

```rust
fn main() {
    // 三种常见创建方式
    let empty = String::new();
    assert!(empty.is_empty());
    let hello = String::from("你好");
    let rust = "Rust".to_string(); // ToString 由 Display 自动实现
    assert_eq!(hello.len(), 6); // 中文每字 3 字节
    assert_eq!(rust.len(), 4);

    // push_str 追加 &str，push 追加单个 char
    let mut s = String::from("hello");
    s.push_str(", world");
    s.push('!');
    assert_eq!(s, "hello, world!");

    // + 拿走左边 String 的所有权，右边只要是 &str
    let left = String::from("foo");
    let right = String::from("bar");
    let joined = left + "-" + &right;
    assert_eq!(joined, "foo-bar");

    // format! 不消耗任何参数，适合多值拼接
    let title = format!("{joined} v{}", 2);
    assert_eq!(title, "foo-bar v2");

    // 字节 -> String 需要校验 UTF-8
    assert_eq!(String::from_utf8(b"hi".to_vec()).unwrap(), "hi");
    assert!(String::from_utf8(vec![0xff]).is_err());

    // drain 删除区间并交出内容，retain 按字符过滤
    let mut t = String::from("hello, world");
    let removed: String = t.drain(5..7).collect();
    assert_eq!(removed, ", ");
    assert_eq!(t, "helloworld");
    t.retain(|ch| ch != 'o');
    assert_eq!(t, "hellwrld");

    // 常见变换：修剪、大小写、替换
    assert_eq!("  Hi  ".trim().to_lowercase(), "hi");
    assert_eq!(String::from("a-b-c").replace('-', "+"), "a+b+c");

    // into_bytes 直接把底层缓冲区交出去，不再分配
    let owned = String::from("data");
    let raw: Vec<u8> = owned.into_bytes();
    assert_eq!(raw, b"data".to_vec());

    // 只读函数参数写 &str，String 借出来即可
    fn first_word(text: &str) -> &str {
        text.split_whitespace().next().unwrap_or("")
    }
    let sentence = String::from("hello rust");
    assert_eq!(first_word(&sentence), "hello");

    println!("{title}");
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[string.String\|String]] | UTF-8 编码、可增长的拥有型字符串。 |
| [[string.ToString\|ToString]] | 把实现了 `Display` 的值转成 `String` 的特质。 |
| `string::Drain` | `drain(range)` 返回的删除迭代器。 |
| `string::FromUtf8Error` | `String::from_utf8` 失败时的错误。 |
| `string::FromUtf16Error` | `String::from_utf16` 失败时的错误。 |
| `String::new` | 创建空字符串，不分配。 |
| `String::with_capacity` | 预留指定字节容量，避免反复扩容。 |
| `String::from_utf8` | 校验 `Vec<u8>` 并转成 `String`。 |
| `String::from_utf16` | 由 UTF-16 码元切片构造 `String`。 |
| `String::push` / `push_str` | 追加一个 `char` / 追加一段 `&str`。 |
| `String::as_str` | 借出 `&str`，不复制。 |
| `String::into_bytes` | 交出底层 `Vec<u8>`，不再校验。 |
| `String::drain` | 删除一个字节区间并返回迭代器。 |
| `String::retain` | 按字符条件原地保留。 |

## 注意事项

> [!warning] 位置参数是字节下标
> `insert`、`drain`、`replace_range`、`truncate` 的参数都是**字节**偏移，且必须落在字符边界上，否则 panic。比如给 `"你好"` 做 `truncate(1)` 会崩。按字符处理时先 `char_indices()` 求出边界，或改用 `chars()` + `collect()`。

> [!danger] `+` 会移动左边的值
> `a + &b` 中 `a` 被消费，之后不能再用；右边的 `&b` 不受影响，因为 `Add` 的实现只取右边 `&str` 的借用。循环里用 `+` 拼接还会反复分配，改用 `format!`、`push_str` 或先 `with_capacity` 预留容量效率更高。

> [!tip] `String` 与 `&str` 的取舍
> 参数用 `&str`（`&String` 会强制解引用，但限制了调用方，属反模式），要存起来、要返回新文本才用 `String`。`String` 与 `&str` 互转几乎免费：`&s` 不分配，`String::from("…")` / `to_string()` 才分配。需要按字节做底层操作时用 `as_bytes()` / `as_mut_vec()`（后者 `unsafe`）。

## 相关

- [[string.String|String]]：类型本身的全部方法与 `Deref` 行为。
- [[str|std::str]]：`&str` 的借用语义与字符、字节迭代器。
- [[string.ToString|ToString]]：`to_string()` 背后的特质，与 [[fmt.Display|Display]] 配套。
- [[vec|std::vec]]：`Vec<T>`，`String` 的底层结构与 `into_bytes` 的去向。
- [[13-字符串|字符串]]：`String` / `&str` / UTF-8 的完整学习笔记。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 7 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`Drain`](https://doc.rust-lang.org/std/string/struct.Drain.html)
- [`FromUtf8Error`](https://doc.rust-lang.org/std/string/struct.FromUtf8Error.html)
- [`FromUtf16Error`](https://doc.rust-lang.org/std/string/struct.FromUtf16Error.html)
- [[string.String|`String`]]
- [`IntoChars`](https://doc.rust-lang.org/std/string/struct.IntoChars.html)

### 特质

- [[string.ToString|`ToString`]]

### 类型别名

- [`ParseError`](https://doc.rust-lang.org/std/string/type.ParseError.html)

<!-- END AUTO ITEMS -->
