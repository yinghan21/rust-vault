---
title: "std::fmt"
type: std-模块
module: fmt
stable: "1.0.0"
unstable: false
tags:
  - std/模块
  - std/宏
aliases:
  - fmt
一句话: 格式化与打印的运行时支撑：Display/Debug 特质、格式参数解析、Formatter 与 Write。
---

# std::fmt

> [!abstract] 一句话
> `std::fmt` 是 [[macro.format|format]]、[[macro.println|println]]、[[macro.write|write]] 这些宏背后的运行时：它定义 `Display`/`Debug` 等格式化特质，并在运行时把参数拼成字符串。

## 模块简介

`format!` 家族是编译器内建的语法扩展，但它本身不干活——编译器把格式串预先解析成一个 `fmt::Arguments`（包含字面片段和参数引用），再交给本模块的函数和特质去实际拼接。所以「怎么格式化」这件事最终体现为**类型实现了哪个格式化特质**。

最常用的两个特质是 [[fmt.Display|Display]]（`{}`，面向用户的可读输出）和 [[fmt.Debug|Debug]]（`{:?}`、`{:#?}`，面向开发者的调试输出）。除此之外还有一组按进制的特质：`Binary`（`{:b}`）、`Octal`（`{:o}`）、`LowerHex`/`UpperHex`（`{:x}`/`{:X}`）、`LowerExp`/`UpperExp`（`{:e}`/`{:E}`）、`Pointer`（`{:p}`）。每个特质对应格式串里的一个标记，没实现就会编译报错。

格式说明符还能带参数：`{name}` 取命名参数，`{:>8}` 右对齐补空格，`{:*^10}` 居中填充 `*`，`{:.3}` 保留三位小数，`{:#x}` 带 `0x` 前缀。这些信息在调用时通过 `Formatter` 传给实现者——`Formatter` 提供 `width()`、`precision()`、`fill()`、`align()`，而 `pad()` 一次性把宽度和精度应用到 `&str` 上。

最后是 `fmt::Write` 特质：`String` 实现了它，所以可以 `write!(&mut s, ...)` 往缓冲区追加内容而不分配新的 `String`。注意它和 `io::Write` 同名但完全无关。

## 快速上手

```rust
use std::fmt::{self, Write as _};

struct Point {
    x: f64,
    y: f64,
}

// Debug：给开发者看，手写时用 debug_struct 能自动带上 {:#?} 的多行格式
impl fmt::Debug for Point {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("Point")
            .field("x", &self.x)
            .field("y", &self.y)
            .finish()
    }
}

// Display：给用户看，{} 走这里
impl fmt::Display for Point {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        // 用 pad 才能让 {:>12}、{:.3} 这类宽度/精度参数生效
        f.pad(&format!("({}, {})", self.x, self.y))
    }
}

fn main() {
    let p = Point { x: 1.5, y: -2.0 };

    assert_eq!(format!("{}", p), "(1.5, -2)");
    assert_eq!(format!("{:?}", p), "Point { x: 1.5, y: -2.0 }");

    // 宽度、填充、对齐、精度由 Formatter 传递
    assert_eq!(format!("{:>12}", p), "   (1.5, -2)");
    assert_eq!(format!("{:*^11}", p), "*(1.5, -2)*");
    assert_eq!(format!("{:.4}", std::f64::consts::PI), "3.1416");

    // 进制与科学计数法
    assert_eq!(format!("{:b}", 10), "1010");
    assert_eq!(format!("{:o}", 10), "12");
    assert_eq!(format!("{:x}", 255), "ff");
    assert_eq!(format!("{:#X}", 255), "0xFF");
    assert_eq!(format!("{:e}", 1234.5), "1.2345e3");

    // 位置参数与命名参数
    assert_eq!(format!("{1}-{0}", "a", "b"), "b-a");
    assert_eq!(format!("{name}={value}", name = "x", value = 1), "x=1");

    // 往任意 fmt::Write 缓冲追加内容，不额外分配 String
    let mut out = String::new();
    write!(&mut out, "{} 与 {:?}", p, p).unwrap();
    assert_eq!(out, "(1.5, -2) 与 Point { x: 1.5, y: -2.0 }");
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[fmt.Display\|Display]] | `{}` 对应的特质，面向用户的可读输出。 |
| [[fmt.Debug\|Debug]] | `{:?}` / `{:#?}`，面向开发者的调试输出。 |
| `fmt::Binary` | `{:b}` 二进制。 |
| `fmt::Octal` | `{:o}` 八进制。 |
| `fmt::LowerHex` / `UpperHex` | `{:x}` / `{:X}` 十六进制。 |
| `fmt::LowerExp` / `UpperExp` | `{:e}` / `{:E}` 科学计数法。 |
| `fmt::Pointer` | `{:p}`，打印指针地址。 |
| `fmt::Write` | 往 `String` 等 Unicode 缓冲写入的特质。 |
| `fmt::Formatter` | 格式化上下文：宽度、精度、填充、对齐。 |
| `fmt::Arguments` | 预编译的格式串与参数，由 `format_args!` 产生。 |
| `fmt::Result` | 格式化函数返回的 `Result<(), fmt::Error>`。 |
| `fmt::Error` | 格式化失败的错误类型。 |
| [[macro.format\|format]] | 返回 `String` 的格式化宏。 |
| [[macro.write\|write]] | 把格式化内容写进 `fmt::Write` 或 `io::Write` 的宏。 |

## 注意事项

> [!warning] 自定义 `Display` 不会自动支持宽度和精度
> 如果你在 `fmt` 里直接 `write!(f, ...)`，`format!("{:>10}", x)` 的宽度会被**静默忽略**。要让宽度、精度、对齐生效，必须自己处理：最简单是 `f.pad(&s)`，或者读 `f.width()` / `f.precision()` 手动补。

> [!tip] `Display` 和 `Debug` 别混用
> `Debug` 是给开发者看的，格式可以随便变、不保证稳定；`Display` 是给用户看的输出契约。写库时给类型加 `#[derive(Debug)]`，只在确实需要「漂亮打印」时才手动实现 `Display`，这样 `{:?}` 永远可用。

> [!danger] 两个 `Write` 与分配开销
> - `fmt::Write`（面向字符串）和 `io::Write`（面向字节流）同名不同物，同时 `use` 会冲突，用 `use std::io::Write as _;` 之类的写法。
> - `format!` 每次都会分配一个 `String`；在循环或热路径里用 `write!(&mut buf, ...)` 复用缓冲区。
> - `println!` 会锁标准输出并可能 panic（写入失败时），对健壮性敏感的代码用 `writeln!(io::stdout(), ...)?`。

## 相关

- [[macro.format|format]]：最常用的格式化宏，返回 `String`。
- [[macro.println|println]]：带换行打印到标准输出。
- [[fmt.Display|Display]] / [[fmt.Debug|Debug]]：两大核心格式化特质。
- [[string.ToString|ToString]]：任何 `Display` 都自动获得 `to_string()`。
- [[11-错误处理|错误处理]]：`fmt::Result` 与 `?` 在实现 `Display` 时的用法。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 29 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`Arguments`](https://doc.rust-lang.org/std/fmt/struct.Arguments.html)
- [`DebugList`](https://doc.rust-lang.org/std/fmt/struct.DebugList.html)
- [`DebugMap`](https://doc.rust-lang.org/std/fmt/struct.DebugMap.html)
- [`DebugSet`](https://doc.rust-lang.org/std/fmt/struct.DebugSet.html)
- [`DebugStruct`](https://doc.rust-lang.org/std/fmt/struct.DebugStruct.html)
- [`DebugTuple`](https://doc.rust-lang.org/std/fmt/struct.DebugTuple.html)
- [`Error`](https://doc.rust-lang.org/std/fmt/struct.Error.html)
- [`Formatter`](https://doc.rust-lang.org/std/fmt/struct.Formatter.html)
- [`FromFn`](https://doc.rust-lang.org/std/fmt/struct.FromFn.html)
- [`NumBuffer`](https://doc.rust-lang.org/std/fmt/struct.NumBuffer.html)
- [`FormattingOptions`](https://doc.rust-lang.org/std/fmt/struct.FormattingOptions.html)

### 枚举

- [`Alignment`](https://doc.rust-lang.org/std/fmt/enum.Alignment.html)
- [`DebugAsHex`](https://doc.rust-lang.org/std/fmt/enum.DebugAsHex.html)
- [`Sign`](https://doc.rust-lang.org/std/fmt/enum.Sign.html)

### 特质

- [`Binary`](https://doc.rust-lang.org/std/fmt/trait.Binary.html)
- [[fmt.Debug|`Debug`]]
- [[fmt.Display|`Display`]]
- [`LowerExp`](https://doc.rust-lang.org/std/fmt/trait.LowerExp.html)
- [`LowerHex`](https://doc.rust-lang.org/std/fmt/trait.LowerHex.html)
- [`Octal`](https://doc.rust-lang.org/std/fmt/trait.Octal.html)
- [`Pointer`](https://doc.rust-lang.org/std/fmt/trait.Pointer.html)
- [`UpperExp`](https://doc.rust-lang.org/std/fmt/trait.UpperExp.html)
- [`UpperHex`](https://doc.rust-lang.org/std/fmt/trait.UpperHex.html)
- [`Write`](https://doc.rust-lang.org/std/fmt/trait.Write.html)

### 类型别名

- [`Result`](https://doc.rust-lang.org/std/fmt/type.Result.html)

### 函数

- [`format`](https://doc.rust-lang.org/std/fmt/fn.format.html)
- [`from_fn`](https://doc.rust-lang.org/std/fmt/fn.from_fn.html)
- [`write`](https://doc.rust-lang.org/std/fmt/fn.write.html)

### 其他

- [[fmt.Debug|`Debug`]]

<!-- END AUTO ITEMS -->
