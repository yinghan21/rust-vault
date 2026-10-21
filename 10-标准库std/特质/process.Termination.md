---
title: "std::process::Termination"
type: std-条目
kind: 特质
module: process
slug: process.Termination
stable: "1.61.0"
tags:
  - std/特质
aliases:
  - Termination
一句话: 定义 main 函数可返回的类型，把返回值翻译成进程退出码。
---

# `Termination`

> [!abstract] 一句话
> `Termination` 决定 `fn main()` 能返回什么：C 的 `main` 只认整数退出码，所以任何要被 `main` 返回的类型都得通过 `report` 转成 `ExitCode`。

## 简介

`main` 的返回类型不是随便写的，编译器要求它实现 `Termination`。标准库为这些类型提供了实现：`()`、`ExitCode`、`!`、`Infallible`，以及最常见的 `Result<T, E> where E: Debug`。

`Result` 的实现很好用：`fn main() -> Result<(), Box<dyn std::error::Error>>` 让你能用 `?`，成功时退出码 0，失败时把 `Err` 用 `Debug` 打到 stderr 并以 1 退出。但它只有「成功 / 失败」两档，想区分错误码就得自己实现 `Termination`：`report` 消费 `self`，返回 `ExitCode`，由 runtime 交给操作系统。

对比 `process::exit`：`exit` 立刻终止进程，跳过所有栈上的析构函数，也不保证缓冲区被刷出；从 `main` 正常返回则走完整收尾流程，这也是推荐用 `Termination` 而不是 `exit` 的原因。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `report(self)` | 把值转换为进程退出码，消费 `self`。 |

完整签名：`fn report(self) -> ExitCode`。

`ExitCode` 是 `process` 模块里的轻量包装：`ExitCode::SUCCESS`、`ExitCode::FAILURE`，或 `ExitCode::from(u8)` 指定具体码。

## 与相邻 trait 的关系

| trait | 关系 |
| --- | --- |
| `process::ExitCode` | `report` 的返回类型，最终被 runtime 用作退出码。 |
| `Debug` | `Result<T, E>` 的 `Termination` 实现要求 `E: Debug`，失败时据此打印。 |
| `Error` | 惯用法：`Box<dyn Error>` 作为 `main` 的错误类型，可容纳任意错误。 |
| `Drop` | 从 `main` 返回会正常析构，`process::exit` 不会。 |

## 示例

### `main` 返回 `Result`

```rust
use std::io;

fn parse_port(s: &str) -> Result<u16, io::Error> {
    s.parse::<u16>()
        .map_err(|_| io::Error::new(io::ErrorKind::InvalidInput, "端口必须是数字"))
}

// 返回 Result 合法，因为 Result<T, E: Debug> 实现了 Termination
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let port = parse_port("8080")?;
    assert_eq!(port, 8080);

    // 出错时会以非零退出码结束，并打印 Debug 形式
    assert!(parse_port("http").is_err());
    Ok(())
}
```

### 自己实现 `Termination`，区分退出码

```rust
use std::process::{ExitCode, Termination};

enum Outcome {
    Done,
    Usage,
}

impl Termination for Outcome {
    fn report(self) -> ExitCode {
        match self {
            Outcome::Done => ExitCode::SUCCESS,
            Outcome::Usage => ExitCode::from(2), // 用法错误约定为 2
        }
    }
}

// main 的返回类型只要实现 Termination，就能是自定义类型
fn main() -> Outcome {
    let args: Vec<String> = std::env::args().collect();
    if args.len() > 1 {
        println!("参数个数：{}", args.len());
        Outcome::Done
    } else {
        eprintln!("用法：程序 <参数>");
        Outcome::Usage
    }
}
```

## 常见陷阱

1. **`fn main` 返回未实现 `Termination` 的类型**：报「doesn't implement `Termination`」，自定义类型要先写 `impl Termination`。
2. **错误类型没有 `Debug`**：`Result<T, E>` 的 `Termination` 要求 `E: Debug`，否则 `main` 返回它也编译不过。
3. **想用 `Result` 区分多个错误码**：`Result` 只会给出 0 或 1，需要具体码就实现 `Termination` 或显式返回 `ExitCode`。
4. **用 `process::exit` 代替返回**：会跳过 `Drop`、不执行 `BufWriter` 的 flush，输出可能丢失；优先从 `main` 返回。
5. **只在 std runtime 成立**：`Termination` 是 std 运行时的约定，`no_std` 或自定义 entry 不保证这个行为。
6. **`report` 消费 `self`**：里面有 `Drop` 逻辑或需要保留数据时，记得它会拿走所有权。

## 相关

- [[process|std::process 模块]]：`Command`、`ExitCode`、`exit` 与进程相关条目。
- [[process.exit|exit]]：立即终止进程，与正常返回的差异值得对比。
- [[result.Result|Result]]：`main` 最常用的返回类型。
- [[error.Error|Error]]：`Box<dyn Error>` 的底层特质。
- [[process.Command|Command]]：子进程的退出状态从另一侧看退出码。
- [[11-错误处理|错误处理]]：`?` 与错误传播的整体写法。
