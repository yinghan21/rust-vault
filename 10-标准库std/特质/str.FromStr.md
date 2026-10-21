---
title: "std::str::FromStr"
type: std-条目
kind: 特质
module: str
slug: str.FromStr
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - FromStr
一句话: 定义「从字符串解析出值」的契约，实现后即可用 str::parse。
---

# `FromStr`

> [!abstract] 一句话
> `FromStr` 把「一段文本 → 一个值」写成 trait：实现 `from_str` 并指定错误类型 `Err`，就能用 `"…".parse::<T>()` 拿到 `Result<T, T::Err>`。

## 简介

`parse` 是 `FromStr` 的语法糖：`s.parse::<T>()` 等价于 `T::from_str(s)`。标准库给整数、浮点、`bool`、`char`、`IpAddr`、`PathBuf` 等一大批类型实现了它，于是命令行参数、配置文件、环境变量都能一行解析。

`FromStr` 没有生命周期参数，因此**只能解析自身不含借用数据的类型**：可以解析 `i32`、`String`、自建结构体，不能解析 `&i32`、`&str` 或任何带引用的结构体。需要零拷贝解析就自己写别的 trait（比如 `from_bytes`），不要硬套 `FromStr`。

错误类型由 `Err` 指定，没有默认值，这就迫使你说明「解析失败长什么样」。标准库常直接复用 `ParseIntError`、`ParseFloatError`，自建类型则通常定义一个零大小错误结构体。

解析格式与 `Display` 输出**不保证互逆**：`Display` 可能丢精度或有损格式化，`FromStr` 也可能只接受更严格的写法，往返测试需要通过 `assert_eq!` 自己验证。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `from_str(s)` | 从字符串解析出值，失败时返回 `Err`。 |
| `type Err` | 关联类型，声明解析错误的类型。 |

完整签名：`fn from_str(s: &str) -> Result<Self, Self::Err>`。

## 与相邻 trait 的关系

| trait | 关系 |
| --- | --- |
| `Display` | 反向的文本化方向，但不与 `FromStr` 构成往返保证。 |
| `TryFrom<&str>` | 与 `FromStr` 语义相近，但能对多种输入类型泛化，且不会有「解析」这一层隐含语义。 |
| `From<&str>` | 不会失败的转换；解析可能失败，所以不能替代 `FromStr`。 |
| `parse` | `str::parse` 是 `FromStr` 的便利入口，靠类型标注选实现。 |

## 示例

### 实现 `FromStr` 并用 `parse`

```rust
use std::str::FromStr;

#[derive(Debug, PartialEq)]
struct Point {
    x: i32,
    y: i32,
}

#[derive(Debug, PartialEq, Eq)]
struct ParsePointError;

impl FromStr for Point {
    type Err = ParsePointError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        // 期望格式形如 "(1,2)"
        let (x, y) = s
            .strip_prefix('(')
            .and_then(|s| s.strip_suffix(')'))
            .and_then(|s| s.split_once(','))
            .ok_or(ParsePointError)?;

        let x = x.parse::<i32>().map_err(|_| ParsePointError)?;
        let y = y.parse::<i32>().map_err(|_| ParsePointError)?;
        Ok(Point { x, y })
    }
}

fn main() {
    let expected = Ok(Point { x: 1, y: 2 });

    // 显式调用
    assert_eq!(Point::from_str("(1,2)"), expected);
    // 隐式调用，靠类型推导
    assert_eq!("(1,2)".parse(), expected);
    assert_eq!("(1,2)".parse::<Point>(), expected);
    // 格式不对时返回错误
    assert!(Point::from_str("(1 2)").is_err());
}
```

### 复用标准库的错误类型并传播

```rust
use std::num::ParseIntError;
use std::str::FromStr;

#[derive(Debug, PartialEq)]
struct Port(u16);

impl FromStr for Port {
    type Err = ParseIntError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        // parse 不会自动去掉空白，先 trim 再解析
        Ok(Port(s.trim().parse()?))
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    assert_eq!("8080".parse::<Port>()?, Port(8080));
    assert_eq!(" 8080 ".parse::<Port>()?, Port(8080));
    assert!("8080x".parse::<Port>().is_err());
    Ok(())
}
```

## 常见陷阱

1. **想解析带借用的类型**：`FromStr` 没有生命周期参数，`&str`、`Cow<str>` 这类都实现不了，只能返回拥有所有权的数据。
2. **忘了 `trim`**：`" 42".parse::<i32>()` 直接失败，标准库不会替你跳过空白。
3. **关联类型 `Err` 没法定下来**：`?` 要求错误能转换成外层错误类型，混用多种错误时给自定义错误加 `impl From<ParseIntError>`，或者统一装进 `Box<dyn Error>`。
4. **类型推断歧义**：`"1".parse().unwrap()` 单独出现会报「type annotations needed」，用 `parse::<i32>()` 或让 `let` 标注类型。
5. **在 `from_str` 里 `unwrap`**：内部解析失败直接 panic，用户输入就能让程序崩，返回 `Err` 才是契约。
6. **假设与 `Display` 互逆**：浮点、时间、带默认值的类型往返常常丢信息，需要往返保证就自己写测试确认。

## 相关

- [[str|std::str 模块]]：`parse`、`FromStr` 与字符串切片方法。
- [[string.ToString|ToString]]：把值转成 `String` 的反方向特质。
- [[convert.TryFrom|TryFrom]]：更通用的可能失败的转换。
- [[convert.From|From]]：不会失败的转换，对比着看更清楚。
- [[11-错误处理|错误处理]]：`?`、错误类型与 `Box<dyn Error>` 的配合。
- [[13-字符串|字符串]]：`String`、`&str` 与文本处理的整体脉络。
