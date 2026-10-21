---
title: "std::error"
type: std-模块
module: error
stable: "1.0.0"
unstable: false
tags:
  - std/模块
  - std/错误
aliases:
  - error
一句话: 错误处理的核心接口：Error 特质把可预期的错误统一成可打印、可溯源、可装箱的类型。
---

# std::error

> [!abstract] 一句话
> `std::error` 定义 [[error.Error|Error]] 特质与配套接口，让 `Result` 里的错误值能被统一打印、沿 `source` 链溯源、装箱擦除后再取回。

## 模块简介

Rust 有两套处理失败的机制。一套是 panic：`panic!`、`std::panic::catch_unwind`、`#[panic_handler]` 这一组，用来表示**程序 bug**（越界、`unwrap` 了 `None`、断言失败），正常情况下不该发生。另一套就是本模块所在的错误系统：`Result`、`Error` 特质和自定义错误类型，用来表示**可预期的运行时失败**（文件不存在、解析失败、连接被拒）。

`Error` 特质本身非常轻：它要求实现者同时实现 `Debug`（给开发者看的诊断信息）和 [[fmt.Display|Display]]（给用户看的说明），并可选提供 `source()` 返回底层原因。这样上层代码只依赖 `dyn Error` 就能打印任意错误、遍历整条错误链，而不需要知道具体类型。

标准库还提供了错误擦除的标准载体 `Box<dyn Error>`（以及 `Box<dyn Error + Send + Sync>`）。`?` 运算符会自动把实现了 `Error` 的类型转换进去，所以 `fn main() -> Result<(), Box<dyn Error>>` 能直接承载应用里所有类型的错误；需要区分具体类型时再用 `downcast_ref` 取回。

模块里另外几个条目（`Report`、`Request`、`request_ref`、`request_value`）仍是不稳定接口，只能在 nightly 上用。日常写库和写应用，掌握 `Error` 加 `source()` 就够了。

## 快速上手

```rust
use std::error::Error;
use std::fmt;

// 自定义错误：包装底层错误，并记录额外的上下文
#[derive(Debug)]
struct PortError {
    input: String,
    source: std::num::ParseIntError,
}

// Display 写给用户看
impl fmt::Display for PortError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "端口 `{}` 不是合法数字", self.input)
    }
}

// source 指回底层错误，形成错误链
impl Error for PortError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        Some(&self.source)
    }
}

fn parse_port(s: &str) -> Result<u16, PortError> {
    s.parse::<u16>().map_err(|e| PortError {
        input: s.to_string(),
        source: e,
    })
}

fn main() -> Result<(), Box<dyn Error>> {
    let err = parse_port("70000").unwrap_err();

    // 逐层打印整条错误链
    let mut cur: Option<&(dyn Error + 'static)> = Some(&err);
    while let Some(e) = cur {
        println!("- {}", e);
        cur = e.source();
    }

    // 装箱后仍能还原成具体类型
    let boxed: Box<dyn Error> = Box::new(err);
    assert!(boxed.downcast_ref::<PortError>().is_some());
    assert!(boxed.to_string().contains("70000"));

    // ? 会自动把具体错误转换成 Box<dyn Error>
    let port = parse_port("8080")?;
    assert_eq!(port, 8080);
    Ok(())
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[error.Error\|Error]] | 错误值的基础特质，要求同时实现 `Debug` 与 `Display`。 |
| `Error::source()` | 返回底层错误，构成错误链；默认返回 `None`。 |
| `dyn Error::downcast_ref()` | 把 `&dyn Error` 还原为具体类型的引用。 |
| `dyn Error::downcast_mut()` | 同上，返回可变引用。 |
| `dyn Error::is()` | 判断动态错误是否为某个具体类型。 |
| `Box<dyn Error>::downcast()` | 从装箱错误中取出具体类型。 |
| `Box<dyn Error>` | 最常用的错误擦除载体，`?` 可自动转换。 |
| `Box<dyn Error + Send + Sync>` | 需要跨线程传递错误时用这个变体。 |
| `Error::description()` | 已废弃的旧接口，新代码不要实现。 |
| `Report` | 打印错误及完整来源链（不稳定，仅 nightly）。 |
| `request_ref` / `request_value` | 按类型向下取上下文数据（不稳定，仅 nightly）。 |

## 注意事项

> [!tip] 库和应用的选择不同
> - **库**：定义具体的错误枚举或结构体，`impl Error`，让调用方能匹配分支。
> - **应用**：直接用 `Box<dyn Error>` 或 `Result<(), Box<dyn Error + Send + Sync>>`，省去大量样板。

> [!warning] `source()` 只该返回底层原因
> 很多实现习惯把 `self` 包一层再返回，容易造成无限递归。`source()` 应返回**被包装的那个错误**，而不是自己；错误链的第一层内容已经在 `Display` 里了。

> [!danger] 常见错误
> - 只实现 `Display` 不实现 `Debug`（或反过来）——`Error` 要求两者都有，`unwrap()` 打印的是 `Debug`。
> - 用 `Box<dyn Error>` 当库的公开返回类型，调用方就没法按变体分支处理了。
> - 忘记 `'static`：`Error` 要求错误类型本身是 `'static`，不要在错误里存借用（存 `String` 而不是 `&str`）。

## 相关

- [[result.Result|Result]]：错误处理的载体类型。
- [[fmt.Display|Display]]：决定错误怎么打印给用户。
- [[11-错误处理|错误处理]]：`?`、`From` 转换与错误设计的完整笔记。
- [[boxed.Box|Box]]：`Box<dyn Error>` 背后的智能指针。
- [[string.ToString|ToString]]：`to_string()` 来自 `Display`。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 5 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`Report`](https://doc.rust-lang.org/std/error/struct.Report.html)
- [`Request`](https://doc.rust-lang.org/std/error/struct.Request.html)

### 特质

- [[error.Error|`Error`]]

### 函数

- [`request_ref`](https://doc.rust-lang.org/std/error/fn.request_ref.html)
- [`request_value`](https://doc.rust-lang.org/std/error/fn.request_value.html)

<!-- END AUTO ITEMS -->
