---
title: "std::backtrace"
type: std-模块
module: backtrace
stable: "1.65.0"
unstable: false
tags:
  - std/模块
aliases:
  - backtrace
一句话: 捕获当前操作系统线程的栈回溯，用 `Backtrace` 把「出错时的调用链」挂到错误类型上。
---

# std::backtrace

> [!abstract] 一句话
> `std::backtrace` 让程序在运行时拍下一张调用栈快照，方便把错误发生的位置链式记录下来。

## 模块简介

`std::backtrace` 只有一个核心类型 `Backtrace`，它表示一次栈回溯的捕获结果。捕获有两个入口：`Backtrace::capture()` 是「按环境变量决定要不要真的采集」，未开启时返回的是空回溯；`Backtrace::force_capture()` 则无条件采集，常用于错误类型里保存出错位置。捕获之后可以用 `status()` 查询到底是捕获成功、被禁用，还是当前平台不支持。

典型用法是把它作为一个字段塞进自定义错误类型：构造错误时 `force_capture()` 一次，打印或 `Debug` 输出时就能看到「错误从哪条调用链冒出来」。`Backtrace` 本身实现了 `Display`，直接 `{}` 就能输出可读文本，也可以配合 `{:?}` 打印。

关于精度要有合理预期：回溯是**尽力而为**的。内联、优化级别、缺少调试信息都会让栈帧缺失或错位，符号名、文件名、行号都可能不准。它适合排障，不适合当作可靠的程序逻辑输入。

## 快速上手

```rust
use std::backtrace::{Backtrace, BacktraceStatus};

fn main() {
    // capture：只在 RUST_BACKTRACE 环境变量开启时才真正收集栈帧
    let lazy = Backtrace::capture();
    // force_capture：无条件收集，适合挂在错误类型上记录出错位置
    let forced = Backtrace::force_capture();

    match forced.status() {
        BacktraceStatus::Captured => println!("force_capture 已捕获回溯"),
        _ => println!("当前平台没有可用的回溯"),
    }

    if lazy.status() == BacktraceStatus::Disabled {
        println!("未开启 RUST_BACKTRACE，capture() 得到的是空回溯");
    }

    // Display 输出可以直接写进日志
    let text = forced.to_string();
    println!("开头几行：{:?}", text.lines().take(2).collect::<Vec<_>>());
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| `Backtrace` | 一次捕获到的线程栈回溯。 |
| `Backtrace::capture` | 受 `RUST_BACKTRACE` 控制地捕获，未开启时为空。 |
| `Backtrace::force_capture` | 无条件捕获，适合错误诊断。 |
| `Backtrace::status` | 查询捕获状态，返回 `BacktraceStatus`。 |
| `BacktraceFrame` | 回溯中的单独一帧。 |
| `BacktraceFrame::symbols` | 迭代该帧内的符号信息，会消费掉这一帧。 |
| `BacktraceStatus` | 枚举：`Captured` / `Disabled` / `Unsupported`。 |
| `Display for Backtrace` | 用 `{}` 直接输出可读的回溯文本。 |
| `RUST_BACKTRACE` | 环境变量，控制 `capture` 是否真正采集栈帧。 |

## 注意事项

> [!warning] 默认拿不到任何东西
> 不设置 `RUST_BACKTRACE` 时，`Backtrace::capture()` 返回空回溯，`status()` 为 `Disabled`。本地调试时要么设置环境变量，要么明确使用 `force_capture()`。

> [!danger] 开销不小，别放在热路径
> 采集和符号化都要读调试信息，比普通日志贵得多。正确做法是「一个错误一次捕获」，在构造错误时拍一张快照，而不是在循环里反复 `force_capture()`。

> [!tip] 精度没有保证
> 内联、优化、剥离符号都会让栈帧缺失或错位。发布构建需要排障时，记得保留调试符号（或使用单独的符号文件），否则打印出来的可能只有地址。

## 相关

- [[模块索引]]
- [[error|std::error 模块]]：把回溯挂到错误类型的常见场所。
- [[panic|std::panic 模块]]：panic 时打印的也是回溯信息。
- [[11-错误处理|错误处理]]：自定义错误类型与错误链的设计。
- [[env|std::env 模块]]：读取与设置 `RUST_BACKTRACE` 等环境变量。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 3 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`Backtrace`](https://doc.rust-lang.org/std/backtrace/struct.Backtrace.html)
- [`BacktraceFrame`](https://doc.rust-lang.org/std/backtrace/struct.BacktraceFrame.html)

### 枚举

- [`BacktraceStatus`](https://doc.rust-lang.org/std/backtrace/enum.BacktraceStatus.html)

<!-- END AUTO ITEMS -->
