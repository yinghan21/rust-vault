---
title: "std::convert::From"
type: std-条目
kind: 特质
module: convert
slug: convert.From
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - From
一句话: 消耗输入的值到值转换，实现它就自动免费获得对应的 Into，也是 ? 自动转换错误类型的机制。
---

# From

> [!abstract] 一句话
> `From<T>` 定义「从 `T` 造出一个 `Self`」的转换：实现它，标准库会自动送你对应的 `Into`，而 `?` 运算符转换错误类型时用的也正是 `From::from`。

## 简介

`From` 只定义一件事：`fn from(value: T) -> Self`。它**消耗**输入值，把它变成目标类型。这是 Rust 里最常用的「可失败不必谈」的转换入口：`String::from("hi")`、`PathBuf::from("a/b")`、`IpAddr::from([127, 0, 0, 1])` 都出自这里。

它最重要的设计是那条 `Into` 的 blanket 实现：

```text
impl<T, U> Into<U> for T where U: From<T>
```

也就是说，**只要你实现了 `From<T> for U`，`U` 就自动获得 `Into<U> for T`**。这一点在类型系统层面成立，不需要你写第二份代码。因此社区的共识是：永远优先实现 `From`，不要手写 `Into`。

`From` 也是 `?` 运算符的幕后机制。`expr?` 在遇到 `Err(e)` 时，会尝试把 `e` 转换成函数返回类型里的错误类型，用的就是 `From::from`。所以给自定义错误类型写 `impl From<io::Error>`，就能在 `?` 处直接把 `io::Error` 变成自己的错误。

实现受限的只有孤儿规则（orphan rule）：`impl From<A> for B` 要求 `A` 或 `B` 至少有一个定义在当前 crate。这也解释了为什么早期版本「把外部类型转换成另一个外部类型」必须写 `Into`（因为 `Into<U> for T` 里 `T` 是 `Self`，可以落在外部的源类型上），而 Rust 1.41 起放宽了 `From` 的规则，这种写法基本不再需要。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `from(value)` | 把 `T` 转换成 `Self`，消耗输入值。 |

签名是 `fn from(value: T) -> Self`。注意它**不能失败**：`From` 代表完美的、无损的转换。可能失败就得用 [[convert.TryFrom|TryFrom]]，否则调用方拿不到拒绝的机会 —— 在 `from` 里 panic 属于破坏契约。

标准库还提供了两个免费的实现：`impl<T> From<T> for T`（自反，`x.into()` 恒等）和 `impl<T> From<T> for Option<T>`（`Some` 包装）。它们也意味着你不能再去手写与它们冲突的实现。

## 与相邻 trait 的关系

| 维度 | `From<T> for U` | `Into<U> for T` |
| --- | --- | --- |
| 逻辑写在哪 | 目标类型 `U` 上 | 源类型 `T` 上 |
| 另一侧 | 自动获得 `Into` | 不会反向获得 `From` |
| 推荐度 | 首选 | 只在无法实现 `From` 时考虑 |
| 泛型边界 | `U: From<T>` 较严格 | `T: Into<U>` 更宽松 |

在泛型函数上写约束时反而应该用 `Into`：`fn f(x: impl Into<String>)` 能接受任何「能变成 `String`」的类型；若写成 `T: From<X>`，就排除了只实现了 `Into` 的类型。这个反转是官方文档明确给出的建议。

三者构成一条完整的阶梯：`From` 必然成功，`TryFrom` 可能失败，`Into`/`TryInto` 是它们的反向镜像。

## 示例

### 实现 `From`，免费得到 `Into`

```rust
#[derive(Debug, PartialEq)]
struct Celsius(f64);

impl From<f64> for Celsius {
    fn from(v: f64) -> Self {
        Celsius(v)
    }
}

fn main() {
    // 直接用 From
    let a = Celsius::from(21.5);

    // Into 来自标准库的 blanket 实现，一行代码都不用写
    let b: Celsius = 21.5.into();

    assert_eq!(a, b);
    assert_eq!(b, Celsius(21.5));
}
```

### 让 `?` 自动转换错误类型

```rust
use std::num::ParseIntError;

#[derive(Debug)]
enum AppError {
    Parse(ParseIntError),
}

// ? 会调用 From::from，把 ParseIntError 变成 AppError
impl From<ParseIntError> for AppError {
    fn from(e: ParseIntError) -> Self {
        AppError::Parse(e)
    }
}

fn parse_port(s: &str) -> Result<u16, AppError> {
    let port: u16 = s.parse()?;
    Ok(port)
}

fn main() {
    assert_eq!(parse_port("8080").unwrap(), 8080);
    assert!(parse_port("abc").is_err());
}
```

### 泛型边界用 `Into` 更宽松

```rust
fn greet(name: impl Into<String>) -> String {
    format!("你好，{}", name.into())
}

fn main() {
    // &str -> String 由标准库的 From<&str> 提供
    assert_eq!(greet("世界"), "你好，世界");
    // 已经拥有 String 时直接转移，不做任何拷贝
    assert_eq!(greet(String::from("Rust")), "你好，Rust");
}
```

### 一石二鸟的错误枚举

```rust
use std::num::ParseIntError;

#[derive(Debug)]
enum ConfigError {
    Number(ParseIntError),
    Missing(&'static str),
}

impl From<ParseIntError> for ConfigError {
    fn from(e: ParseIntError) -> Self {
        ConfigError::Number(e)
    }
}

fn parse(text: Option<&str>) -> Result<u32, ConfigError> {
    // 两种错误、一个 ? 出口：都靠 From 统一
    let text = text.ok_or(ConfigError::Missing("缺少字段"))?;
    Ok(text.parse::<u32>()?)
}

fn main() {
    assert_eq!(parse(Some("7")).unwrap(), 7);
    assert!(parse(None).is_err());
}
```

## 常见陷阱

1. **为两个外部类型实现 `From`**：`impl From<Vec<i32>> for MyType` 可以，但源和目标都不在本 crate 时报 E0117，孤儿规则不允许。
2. **既实现 `From` 又想手写 `Into`**：与 blanket 实现冲突，E0119（`conflicting implementations of trait Into`）。写了 `From` 就不要再碰 `Into`。
3. **在 `from` 里处理失败**：`From` 语义上无失败可能，转换可能失败就用 `TryFrom`；在 `from` 里 panic 会让调用方措手不及。
4. **泛型约束写成 `T: From<X>`**：会排除只实现了 `Into` 的类型，边界应写 `T: Into<X>`。
5. **以为 `&str -> String` 和 `String -> &str` 对称**：前者有 `From<&str>`，后者不存在（不能凭空造出借用），要用 `&s`、`s.as_str()`。
6. **`from` 里悄悄丢弃信息**：若转换会溢出、截断，那它就不是 `From` 而是 `TryFrom`；`as` 强转不属于 `From` 的语义。

## 相关

- [[convert|std::convert 模块]]：各类转换特质的总入口。
- [[convert.Into|Into]]：`From` 的反向镜像，由 blanket 实现自动提供。
- [[convert.TryFrom|TryFrom]]：可能失败的转换。
- [[convert.AsRef|AsRef]]：借用层面的廉价转换。
- [[11-错误处理|错误处理]]：`?` 与 `From` 的配合套路。
- [[string.String|String]]：`From<&str>`、`From<char>` 等最常用的实现。
