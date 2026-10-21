---
title: "std::convert::TryFrom"
type: std-条目
kind: 特质
module: convert
slug: convert.TryFrom
stable: "1.34.0"
tags:
  - std/特质
aliases:
  - TryFrom
一句话: 表达可能失败的转换，返回 Result<Self, Self::Error>，替代会静默丢数据的 as 强转。
---

# TryFrom

> [!abstract] 一句话
> `TryFrom` 是 [[convert.From|From]] 的「可失败版本」：转换要么给出 `Ok(新值)`，要么给出 `Err(错误)`，绝不像 `as` 那样悄悄截断。它稳定于 1.34.0，是 `TryInto` 的对偶。

## 简介

定义是 `pub trait TryFrom<T>: Sized { type Error; fn try_from(value: T) -> Result<Self, Self::Error>; }`。与 `From` 只差一个 `Result` 和一个关联类型 `Error`——放弃「永远不会失败」这个前提，换来失败时能说清楚原因。

为什么需要它：`From` 只用于**完美转换**，即不失败、不丢信息，例如 `i32` 到 `i64`。反方向的 `i64` 到 `i32` 就不完美了，1_000_000_000_000 放不进 32 位。标准库因此不为它实现 `From`，而是给了 `TryFrom`。若用 `as` 强转，结果会静默截断成 `-727379968`，编译器一声不吭。

`Error` 是这个 trait 的关键设计：失败原因由实现者决定，可以是零大小的错误枚举，也可以是 `String`。标准库的整数转换统一用 `std::num::TryFromIntError`，它不分配内存、可以轻松比较。

另有一条自动关系：`impl<T, U> TryFrom<U> for T where U: Into<T>`，即任何实现了 `From` 的类型对**自动**获得 `TryFrom`，其 `Error` 是 `std::convert::Infallible`——一个永远不可能出现的错误类型。这让泛型代码只需约束 `TryFrom` 就同时覆盖了「一定成功」与「可能失败」两种情况。

关于约束方向，标准库文档明确建议：给泛型函数写边界时优先用 `TryInto` 而不是 `TryFrom`，因为 `impl<T, U> TryInto<U> for T where U: TryFrom<T>` 是自动成立的，而反过来不成立，写 `TryFrom` 会把只实现 `TryInto` 的类型排除在外。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `try_from()` | 尝试把 `T` 转成 `Self`，失败时返回 `Err`。 |
| 关联类型 `Error` | 声明失败时的错误类型，由实现者选定。 |

签名是 `fn try_from(value: T) -> Result<Self, Self::Error>`。注意参数是**按值**传入的 `T`，不是 `&T`：转换会消耗输入。

## 提供的方法

无。真正被调用的一般是反向的 `try_into`，它属于 `TryInto`，并且因为那条 blanket impl，实现 `TryFrom` 就自动拥有了它。

```rust
fn main() {
    let x: u8 = 300u32.try_into().unwrap_or(0);
    assert_eq!(x, 0);
}
```

上面这行能编译，靠的就是「`u8: TryFrom<u32>` ⇒ `u32: TryInto<u8>`」。

## 与相邻 trait 的关系

| 维度 | `From` | `TryFrom` |
| --- | --- | --- |
| 适用前提 | 转换永不失败，且不丢信息 | 可能失败，或需要校验 |
| 返回类型 | `Self` | `Result<Self, Self::Error>` |
| 失败信息 | 不存在 | 关联类型 `Error` 由实现者决定 |
| 自动关系 | 实现 `From` 自动获得 `TryFrom`（`Error = Infallible`） | 实现 `TryFrom` 自动获得 `TryInto` |
| 典型例子 | `i32 → i64`、`&str → String` | `i64 → i32`、`u32 → u8`、字符串解析 |

`TryFrom` 与 `TryInto` 是同一件事的两个方向，写法互补：实现方写 `TryFrom`，调用方多用 `try_into()`（类型由目标推断）。二者从 Rust 2021 edition 起都在 prelude 里，2018 edition 需要手写 `use std::convert::TryFrom;`。

`TryFrom` 与 `FromStr` 也常被拿来比：`FromStr` 专管「从 `&str` 解析」，返回 `Result`；`TryFrom` 通用于任意两种类型，`&str` 相关的那部分可以和 `FromStr` 互相转发。

## 示例

### 数值窄化：as 与 try_from 的差别

```rust
fn main() {
    let big: i64 = 1_000_000_000_000;

    // as 静默截断，得到的是一个毫不相关的负数
    assert_eq!(big as i32, -727379968);

    // try_from 明确拒绝放不下的值
    assert!(i32::try_from(big).is_err());
    assert_eq!(i32::try_from(42i64), Ok(42));

    // 无符号也一样：u8 装不下 300
    assert!(u8::try_from(300u32).is_err());
    assert_eq!(u8::try_from(255u32), Ok(255));
}
```

### 自定义可失败转换

```rust
#[derive(Debug, PartialEq)]
struct Port(u16);

impl TryFrom<i32> for Port {
    type Error = String;

    fn try_from(value: i32) -> Result<Self, Self::Error> {
        u16::try_from(value)
            .map(Port)
            .map_err(|_| format!("端口超出范围：{value}"))
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    assert_eq!(Port::try_from(8080)?, Port(8080));

    // 错误是 String，可以用 ? 转成 Box<dyn Error>
    assert!(Port::try_from(70000).is_err());
    assert_eq!(
        Port::try_from(-1).unwrap_err(),
        "端口超出范围：-1".to_string()
    );
    Ok(())
}
```

### 借 From 自动得到 TryFrom

```rust
use std::convert::Infallible;

fn main() {
    // 因为存在 From<i32> for i64，i64 的 TryFrom<i32> 是自动的
    let small: i32 = 7;
    let big = i64::try_from(small).unwrap();
    assert_eq!(big, 7);

    // 这条路径的错误类型是 Infallible：它永远不可能被构造出来
    let never_fails: Result<i64, Infallible> = i64::try_from(1i32);
    assert!(never_fails.is_ok());
}
```

## 常见陷阱

1. **用 `as` 做窄化转换**：`as` 对整数是截断或回绕，对 `-1i32 as u32` 会得到 `4294967295`，编译器不会提醒；只要可能越界就该用 `try_from`。
2. **为可失败的转换实现 `From`**：`From` 无法表达失败，实现者只能 panic 或塞一个哨兵值，两者都把问题推给调用方。
3. **泛型边界写成 `T: TryFrom<U>`**：会把只实现 `TryInto` 的类型挡在外面，标准库建议写 `T: TryInto<U>`。
4. **`Error` 类型选得太大**：直接用 `String` 或 `Box<dyn Error>` 会带来堆分配，也让调用方难以用 `match` 分支处理；能用小枚举就别用字符串。
5. **`try_into` 缺少目标类型**：`let x = 300u32.try_into().unwrap();` 编译不过（无法推断目标），要么写 `let x: u8 = ...`，要么改用 `u8::try_from(300u32)`。
6. **以为 `TryFrom` 在 2018 edition 的 prelude 里**：需要显式 `use std::convert::TryFrom;`，否则 `try_from` 找不到。

## 相关

- [[convert|std::convert 模块]]：`TryFrom` 所属模块。
- [[convert.From|From]]：不失败的转换，`TryFrom` 的完美版本。
- [[convert.Into|Into]]：`From` 的反向写法。
- `TryInto`：`TryFrom` 的反向写法，泛型边界优先用它（本库暂未单列条目）。
- [[result.Result|Result]]：`try_from` 的返回类型。
- [[11-错误处理|错误处理]]：`?` 与错误类型转换的用法。
