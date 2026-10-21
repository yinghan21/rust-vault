---
title: "std::convert"
type: std-模块
module: convert
stable: "1.0.0"
unstable: false
tags:
  - std/模块
  - std/特质
aliases:
  - convert
  - 类型转换
一句话: 类型转换特质：不会失败的 `From`/`Into`、可能失败的 `TryFrom`/`TryInto`，以及廉价的引用转换 `AsRef`/`AsMut`。
---

# std::convert

> [!abstract] 一句话
> `std::convert` 用特质描述类型之间的转换：`From`/`Into` 不会失败，`TryFrom`/`TryInto` 可能失败，`AsRef`/`AsMut` 只做引用层的廉价转换。

## 模块简介

Rust 没有隐式类型转换，跨类型赋值必须显式写出来。`std::convert` 把这些显式转换抽象成四个互为对偶的特质：

- `From<T> for U` / `Into<U> for T`：不会失败的值到值转换。标准库有一个 blanket 实现，**实现了 `From` 就自动获得 `Into`**，所以库作者只需要实现 `From`。
- `TryFrom<T> for U` / `TryInto<U> for T`：可能失败的转换，返回 `Result<U, Self::Error>`，例如大整数转小整数、整数转 `char`。
- `AsRef<T>` / `AsMut<T>`：引用到引用的廉价转换，不消耗值，常用来放宽函数参数类型。
- `Infallible`：表示「这个转换永远不会失败」的错误类型，配合 `TryFrom` 使用。

这些特质最常见的用途不是转换本身，而是**泛型约束**。写 `fn log(msg: impl Into<String>)`，调用方可以传 `&str`、`String`、`&String`；写 `fn read(path: impl AsRef<Path>)`，`&str`、`String`、`PathBuf` 都能传进来。

历史注意点：Rust 1.41 之前孤儿规则较严，为外部类型实现 `Into` 有时是唯一选择；现在应当一律优先实现 `From` / `TryFrom`，把 `Into` / `TryInto` 交给标准库自动生成。

## 快速上手

```rust
use std::convert::{AsRef, Infallible, TryFrom};

struct Celsius(f64);

impl From<Celsius> for f64 {
    fn from(c: Celsius) -> f64 {
        c.0
    }
}

// 参数用 AsRef<str>，&str 与 String 都能传
fn print_len(s: impl AsRef<str>) {
    println!("长度 = {}", s.as_ref().len());
}

// 用 Infallible 表示「不会失败」的转换错误
fn always_ok() -> Result<u8, Infallible> {
    Ok(42)
}

fn main() {
    // From 自动带来 Into
    let c = Celsius(36.6);
    let t: f64 = c.into();
    assert_eq!(t, 36.6);

    // 也可以直接调用 From::from
    let t2 = f64::from(Celsius(0.0));
    assert_eq!(t2, 0.0);

    // TryFrom 用于可能溢出的转换
    let small: Result<i8, _> = i8::try_from(300i32);
    assert!(small.is_err());
    assert_eq!(u8::try_from(255i32), Ok(255));

    assert_eq!(always_ok(), Ok(42));

    print_len("hello");
    print_len(String::from("你好"));
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[convert.From|From]] | 不会失败的值到值转换，通常实现这个。 |
| [[convert.Into|Into]] | `From` 的反向视角，由标准库自动提供。 |
| [[convert.TryFrom|TryFrom]] | 可能失败的转换，返回 `Result`。 |
| `convert::TryInto` | 由 `TryFrom` 自动提供的反向特质。 |
| [[convert.AsRef|AsRef]] | 廉价的引用到引用转换，常用于参数约束。 |
| `convert::AsMut` | 可变的引用到引用转换。 |
| `convert::Infallible` | 永不发生的错误类型，用作 `TryFrom::Error`。 |
| `impl From<A> for B` | 为新类型实现转换，自动获得 `Into`。 |
| `String::from` / `.into()` | 最常见的转换写法，目标类型由上下文推断。 |
| `i8::try_from` | 带溢出检查的整数转换。 |

## 注意事项

> [!warning] 实现 `From` 而不是 `Into`
> 手写 `Into` 不会反过来得到 `From`，而泛型代码和多数 API 都要求 `From`。只实现 `From`，两个方向就都有了。

> [!danger] `as` 不做检查
> `as` 在整数之间会截断高位，负数转无符号会回绕。可能失败的场景改用 `TryFrom` 并处理错误，别用 `as` 掩盖问题。

> [!tip] 用 `AsRef<str>` 放宽参数
> 函数参数写成 `impl AsRef<str>` 或 `impl Into<String>`，调用方可以传 `&str`、`String`、`&String`，不必到处写 `.to_string()`。

## 相关

- [[convert.From|From]] 与 [[convert.Into|Into]]：不会失败的转换对。
- [[convert.TryFrom|TryFrom]]：可能失败的转换。
- [[convert.AsRef|AsRef]]：引用转换与参数约束。
- [[15-trait 基础|trait 基础]]：孤儿规则与 blanket 实现。
- [[14-泛型|泛型]]：用转换特质写泛型函数。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 11 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 枚举

- [`Infallible`](https://doc.rust-lang.org/std/convert/enum.Infallible.html)

### 特质

- [`AsMut`](https://doc.rust-lang.org/std/convert/trait.AsMut.html)
- [[convert.AsRef|`AsRef`]]
- [[convert.From|`From`]]
- [[convert.Into|`Into`]]
- [[convert.TryFrom|`TryFrom`]]
- [`TryInto`](https://doc.rust-lang.org/std/convert/trait.TryInto.html)
- [`BoundedCastFromInt`](https://doc.rust-lang.org/std/convert/trait.BoundedCastFromInt.html)
- [`CheckedCastFromInt`](https://doc.rust-lang.org/std/convert/trait.CheckedCastFromInt.html)
- [`FloatToInt`](https://doc.rust-lang.org/std/convert/trait.FloatToInt.html)

### 函数

- [`identity`](https://doc.rust-lang.org/std/convert/fn.identity.html)

<!-- END AUTO ITEMS -->
