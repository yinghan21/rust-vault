---
title: "std::fmt::Display"
type: std-条目
kind: 特质
module: fmt
slug: fmt.Display
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - Display
一句话: 定义面向用户的文本表示，实现一次即可用于 {}、to_string()、format! 等所有位置。
---

# `Display`

> [!abstract] 一句话
> `Display` 决定一个类型「打印给人看」时长什么样：实现它之后，`{}`、`println!`、`to_string()`、`format!` 全都自动可用，而且不用再手写 `ToString`。

## 简介

标准库把「转成字符串」拆成两半：`Display` 管用户可见的展示，`Debug` 管开发者调试用的转储。两者格式占位符不同（`{}` 与 `{:?}`），定位也不同——所以 `Display` 没有 `#[derive(Display)]`，一个类型对用户该怎么显示，编译器猜不出来。

`Display` 只有 `fmt` 一个方法，拿到的 `Formatter` 里带着用户写的宽度、精度、填充字符和对齐方式。要想让 `{:>10}` 生效，必须把拼好的字符串交给 `f.pad`，而不是直接 `write!` 出去。

实现 `Display` 会顺带得到 `ToString`：标准库有一条空白实现 `impl<T: fmt::Display + ?Sized> ToString for T`，因此**永远不要手写 `impl ToString`**，否则会和这条实现冲突。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `fmt(&self, f)` | 用给定格式化器写出 `self` 的文本表示。 |

完整签名：`fn fmt(&self, f: &mut Formatter<'_>) -> Result<(), Error>`。

`Display` 没有提供其他方法，只此一个。

## 与相邻 trait 的关系

| trait | 关系 |
| --- | --- |
| `Debug` | 兄弟特质：`Display` 面向用户、不能派生；`Debug` 面向调试、几乎总是派生。 |
| `ToString` | 随 `Display` 免费获得，二者不并存手写。 |
| `FromStr` | 反向操作，但不保证与 `Display` 输出互逆。 |
| `Formatter` | 提供 `width`、`precision`、`fill`、`align` 与 `pad` 等格式控制。 |

## 示例

### 实现 `Display`

```rust
use std::fmt;

struct Point {
    x: i32,
    y: i32,
}

impl fmt::Display for Point {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({}, {})", self.x, self.y)
    }
}

fn main() {
    let origin = Point { x: 0, y: 0 };

    // {} 走 Display
    assert_eq!(format!("The origin is: {origin}"), "The origin is: (0, 0)");

    // Display 自动带来 ToString，无需额外实现
    assert_eq!(origin.to_string(), "(0, 0)");
}
```

### 让宽度与对齐参数生效

```rust
use std::fmt;

struct Money(i64); // 以「分」为单位

impl fmt::Display for Money {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let s = format!("{}.{:02}", self.0 / 100, (self.0 % 100).abs());
        // 交给 f.pad，{:>8}、{:*^9} 这类参数才会被尊重
        f.pad(&s)
    }
}

fn main() {
    assert_eq!(format!("{}", Money(1234)), "12.34");
    assert_eq!(format!("{:>8}", Money(1234)), "   12.34");
    assert_eq!(format!("{:*^9}", Money(1234)), "**12.34**");
}
```

## 常见陷阱

1. **只派生了 `Debug` 就用 `{}`**：报错「doesn't implement `Display`」。要么手写 `Display`，要么把占位符改成 `{:?}`。
2. **试图 `#[derive(Display)]`**：不存在这个派生，`Display` 只能手写。
3. **忽略 `fmt::Error`**：用 `write!` 后必须 `?` 或用 `let _ =` 显式说明；吞掉错误会让格式化静默失败。
4. **对齐参数失效**：直接 `write!(f, "...")` 会跳过 `{:>8}` 的宽度填充，得调 `f.pad`。
5. **同时手写 `ToString`**：与标准库的空白实现冲突，编译直接报 conflicting implementations。
6. **对外输出混用 `Debug`**：`{:#?}` 会换行、带引号，适合日志但不适合拼进界面文案。

## 相关

- [[fmt|std::fmt 模块]]：格式化语法、`Formatter` 与全部格式特质。
- [[fmt.Debug|Debug]]：面向调试的兄弟特质，通常派生。
- [[string.ToString|ToString]]：由 `Display` 自动实现的转换特质。
- [[macro.format|format]]：用 `Display` 拼装 `String` 的宏。
- [[13-字符串|字符串]]：`String` 与 `&str` 的格式化细节。
- [[15-trait 基础|trait 基础]]：从零写一个 trait 实现。
