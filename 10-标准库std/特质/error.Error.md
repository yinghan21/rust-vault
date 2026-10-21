---
title: "std::error::Error"
type: std-条目
kind: 特质
module: error
slug: error.Error
stable: "1.0.0"
tags:
  - std/特质
  - std/错误
aliases:
  - Error
一句话: 错误值的基础契约，要求能 Display + Debug，并提供 source、downcast 等能力。
---

# `Error`

> [!abstract] 一句话
> `Error` 规定了「什么才算一个错误值」：必须能 `Display`（给人看）和 `Debug`（给开发者看），可选地通过 `source()` 给出下层原因，并能通过 `downcast` 系列方法还原成具体类型。

## 简介

`Result<T, E>` 里的 `E` 完全自由，但库与库之间要互操作就得有共同语言，`Error` 就是这个共同语言。它的直接 supertrait 是 [[fmt.Display|Display]] 和 [[fmt.Debug|Debug]]，所以 `impl Error for MyError {}` 之前必须先把这两个实现写出来。

实现 `Error` 本身通常**不用写任何方法**：唯一有默认实现的 `source` 默认返回 `None`。真正需要覆写它的场合是「错误跨越了抽象层次」——底层模块报 IO 错，上层模块包成自己的错误，同时希望调用方还能拿到原始原因，这时 `source()` 就是那条回溯链。

`dyn Error` 上还有一组方法（`is`、`downcast_ref`、`downcast_mut`、`downcast`），用于把「装箱的抽象错误」还原成具体类型。错误信息建议写成简短的小写句、不加句号，且**不要把下层错误同时写进 `Display` 和 `source`**，否则日志里会出现两遍。

## 必须实现

| 项目 | 说明 |
| --- | --- |
| `Display` | 给人读的错误信息，`to_string()` 来自这里。 |
| `Debug` | 开发者视角的详情，`{:?}` 与 `unwrap` panic 用。 |

`Error` 自身没有必须实现的方法，`impl Error for MyError {}` 空实现即可；但 supertrait 未满足时无法编译。

## 提供的方法

| 方法 | 说明 |
| --- | --- |
| `source()` | 返回下层错误，默认实现为 `None`。 |
| `cause()` | 旧版获取下层错误的入口，已被 `source` 取代。 |

签名是 `fn source(&self) -> Option<&(dyn Error + 'static)>`。注意返回类型带 `'static`：下层错误不能借用短生命周期数据，这也是 `Error` 类型一般用拥有所有权的字段的原因。

## 关联方法（在 `dyn Error` 上）

| 方法 | 说明 |
| --- | --- |
| `is<T>()` | 判断实际类型是否为 `T`。 |
| `downcast_ref<T>()` | 以引用形式取出具体类型，不匹配返回 `None`。 |
| `downcast_mut<T>()` | 以可变引用形式取出具体类型，失败返回 `None`。 |
| `downcast<T>()` | 把 `Box<dyn Error>` 转换回 `Box<T>`。 |

`is` / `downcast_ref` / `downcast_mut` 在 `dyn Error`、`dyn Error + Send`、`dyn Error + Send + Sync` 三种装箱形态上各有一份实现，行为一致；`downcast` 同样对应 `Box<dyn Error>`、`Box<dyn Error + Send>`、`Box<dyn Error + Send + Sync>` 三种入参。

## 示例

### 最小错误类型

```rust
use std::error::Error;
use std::fmt;
use std::path::PathBuf;

#[derive(Debug)]
struct ReadConfigError {
    path: PathBuf,
}

impl fmt::Display for ReadConfigError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "无法读取配置：{}", self.path.display())
    }
}

// 没有下层错误，空实现即可
impl Error for ReadConfigError {}

fn main() {
    let err = ReadConfigError {
        path: PathBuf::from("config.toml"),
    };
    assert_eq!(err.to_string(), "无法读取配置：config.toml");
    assert!(err.source().is_none());
    println!("错误：{err}");
}
```

### 用 `source` 串起原因链，并向下转型

```rust
use std::error::Error;
use std::fmt;

#[derive(Debug)]
struct ParseError;

impl fmt::Display for ParseError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "解析失败")
    }
}

impl Error for ParseError {}

#[derive(Debug)]
struct AppError {
    source: ParseError,
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "应用错误")
    }
}

impl Error for AppError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        Some(&self.source)
    }
}

fn main() {
    let boxed: Box<dyn Error> = Box::new(AppError {
        source: ParseError,
    });

    // 先判断类型，再取出所有权并转回具体类型
    assert!(boxed.is::<AppError>());
    match boxed.downcast::<AppError>() {
        Ok(app) => println!(
            "转回 AppError，下层原因: {}",
            app.source().map(|e| e.to_string()).unwrap_or_default()
        ),
        Err(err) => println!("不是 AppError: {err}"),
    }

    // 手动沿着 source() 走一遍原因链
    let err = AppError {
        source: ParseError,
    };
    let mut chain = Vec::new();
    let mut current: Option<&(dyn Error + 'static)> = Some(&err);
    while let Some(e) = current {
        chain.push(e.to_string());
        current = e.source();
    }
    assert_eq!(chain, vec!["应用错误".to_string(), "解析失败".to_string()]);
}
```

## 常见陷阱

1. **只实现 `Display` 就写 `impl Error`**：漏掉 `Debug` 会编译失败，对策是给错误类型加 `#[derive(Debug)]`。
2. **原因写了两遍**：`Display` 里再拼一次下层信息、又实现 `source`，日志会重复，对策是二选一。
3. **对 `&dyn Error` 调 `downcast`**：它只存在于 `Box<dyn Error>` 上，对策是引用用 `downcast_ref`，所有权用 `downcast`。
4. **错误类型带借用参数**：`source()` 要求 `'static`，含短生命周期引用的错误无法装箱成 `Box<dyn Error>`，对策是改存 `String` / `PathBuf`。
5. **用了 `description`**：它已弃用，对策是统一用 `Display` / `to_string()` 取文案。

## 相关

- [[error|std::error 模块]]：`Error` 与相关辅助项的入口。
- [[result.Result|Result]]：错误值真正被使用的地方。
- [[fmt.Display|Display]]、[[fmt.Debug|Debug]]：`Error` 的两个 supertrait。
- [[11-错误处理|错误处理]]：`?`、自定义错误与错误链的完整讲法。
- [[16-trait 对象与动态分发|trait 对象]]：`Box<dyn Error>` 为什么能装各种错误。
