---
title: "std::fmt::Debug"
type: std-条目
kind: 特质
module: fmt
slug: fmt.Debug
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - Debug
一句话: 定义面向开发者的调试输出，通常用 derive 得到，配合 {:?} 与 {:#?} 使用。
---

# `Debug`

> [!abstract] 一句话
> `Debug` 是「给程序员看的」格式化契约：`{:?}` 用它，`{:#?}` 用它缩进展开，`dbg!` 和 `assert_eq!` 失败信息也用它——所以几乎每个类型都应该派生它。

## 简介

`Debug` 与 `Display` 是一对分工明确的兄弟：`Display` 追求可读、面向最终用户；`Debug` 追求信息完整、面向排查问题，允许带上类型名、字段名和引号。正因为「怎么显示才算好」没有唯一答案，而「把字段全列出来」是确定的，所以 `Debug` 可以 `#[derive(Debug)]`，`Display` 不能。

`#[derive(Debug)]` 生成的是 `值 { 字段: 值, ... }` 形式。手写时用 `f.debug_struct`、`f.debug_list`、`f.debug_map` 这类建造器，它们会自动处理 `{:#?}` 的缩进和换行，比自己拼字符串省事。

`Debug` 的输出**不是稳定协议**：标准库不承诺跨版本的精确文本，`HashMap` 这类无序容器的字段顺序每次运行都可能不同，不要拿它做数据交换或在测试里断言整串输出。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `fmt(&self, f)` | 用给定格式化器写出 `self` 的调试表示。 |

完整签名：`fn fmt(&self, f: &mut Formatter<'_>) -> Result<(), Error>`。

`Debug` 没有其他必须或提供的方法，全部工作都在这一个 `fmt` 里。

## 与相邻 trait 的关系

| trait | 关系 |
| --- | --- |
| `Display` | 面向用户的展示；与 `Debug` 各自独立实现，互不自动推导。 |
| `Termination` | `fn main() -> Result<_, E>` 要求 `E: Debug`，出错时用 `Debug` 打印。 |
| `Clone` / `PartialEq` | 测试里常与 `Debug` 一起派生，`assert_eq!` 失败时才打得出内容。 |
| `Formatter` | 提供 `debug_struct` / `debug_list` / `debug_map` 等建造器。 |

## 示例

### 派生 `Debug`

```rust
#[derive(Debug)]
struct Point {
    x: i32,
    y: i32,
}

fn main() {
    let origin = Point { x: 0, y: 0 };

    // {:?} 走 Debug，紧凑单行
    assert_eq!(
        format!("The origin is: {origin:?}"),
        "The origin is: Point { x: 0, y: 0 }",
    );

    // {:#?} 逐字段缩进展开，适合排查嵌套结构
    println!("{origin:#?}");
}
```

### 手写 `Debug`，隐藏不该进日志的字段

```rust
use std::fmt;

struct Account {
    user: String,
    password: String,
}

impl fmt::Debug for Account {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        // 密码用固定占位符顶掉，避免调试输出泄露到日志
        f.debug_struct("Account")
            .field("user", &self.user)
            .field("password", &"<redacted>")
            .finish()
    }
}

fn main() {
    let account = Account {
        user: String::from("ferris"),
        password: String::from("hunter2"),
    };
    let shown = format!("{account:?}");
    assert!(shown.contains("ferris"));
    assert!(!shown.contains("hunter2"));
}
```

## 常见陷阱

1. **忘记派生 `Debug`**：`{:?}`、`assert_eq!`、`dbg!` 全部失效；`#[derive(Debug)]` 要求每个字段都实现 `Debug`。
2. **拿 `{:?}` 当稳定格式**：`HashMap`、`HashSet` 的遍历顺序不确定，测试里断言整串输出会随机失败。
3. **调试信息泄密**：`Debug` 输出最常被直接写进日志，令牌、密码、身份证号要么手写 `fmt` 打码，要么字段类型自己实现带遮蔽的 `Debug`。
4. **`dbg!` 不是无副作用的**：它打印到 stderr 并返回参数所有权，塞在循环或热路径里会明显拖慢程序。
5. **`{:#?}` 混进用户界面**：多行缩进会破坏终端布局和 `--json` 输出，面向用户请走 `Display`。
6. **给 `Debug` 加业务逻辑**：它应该只描述结构，不要在里面做 I/O 或加锁，格式化途中 panic 会让排错更糟。

## 相关

- [[fmt|std::fmt 模块]]：格式化语法与全部格式特质总览。
- [[fmt.Display|Display]]：面向用户的展示特质。
- [[macro.dbg|dbg]]：基于 `Debug` 的调试打印宏。
- [[string.ToString|ToString]]：另一个把值转成文本的入口。
- [[15-trait 基础|trait 基础]]：trait 实现与派生宏的基本写法。
