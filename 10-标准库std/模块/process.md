---
title: "std::process"
type: std-模块
module: process
stable: "1.0.0"
unstable: false
tags:
  - std/模块
  - std/IO
aliases:
  - process
一句话: 启动并管理子进程（Command、Child、Stdio、ExitStatus），以及用 exit 或 abort 终止当前进程。
---

# std::process

> [!abstract] 一句话
> `std::process` 管两件事：用 `Command` 拉起子进程、控制它的输入输出并检查退出状态；以及用 `exit` / `abort` 结束当前进程。

## 模块简介

模块分成两半。一半是**子进程**：`Command` 是进程构建器，`spawn` 之后拿到 `Child`，`Stdio` 描述三条标准流怎么接，`Output` 与 `ExitStatus` 描述跑完之后的结果。另一半是**当前进程的终止**：`exit(code)` 与 `abort()`，外加 `id()` 拿 PID。

`Command` 的用法是典型的 builder：`Command::new("程序")` 之后接 `arg` / `args` 加参数、`env` / `env_remove` / `env_clear` 改环境、`current_dir` 换工作目录、`stdin` / `stdout` / `stderr` 决定标准流走向，最后三选一收尾——`status()` 等它结束只留退出状态，`output()` 等它结束并把 stdout/stderr 全部收进内存，`spawn()` 立刻返回 `Child`、由你自己决定何时 `wait()`、怎么读管道。子进程**不经过 shell**：`|`、`>`、`&&`、通配符、`$VAR` 展开统统不会生效，需要这些就显式起 `sh -c` 或 `cmd /C`。

终止当前进程要小心。`process::exit` 立刻结束进程，**不执行任何析构函数**，不 flush [[io.BufWriter|BufWriter]] 之类的缓冲，`Drop` 里写的清理（删临时文件、回滚事务）也不会跑。`process::abort` 更暴力：Unix 上发 `SIGABRT`，Windows 上走 CRT 的 `abort`，用于「内存状态已经不可信」的场合。正常收尾更推荐直接从 `main` 返回 `Result<(), E>` 或 `ExitCode`——[[process.Termination|Termination]] trait 就是为这两种返回类型准备的。

## 快速上手

```rust
use std::process::{self, Command};

fn main() -> std::io::Result<()> {
    // 让程序自己充当子进程：带 --child 时只打印一行并以 7 退出
    if std::env::args().skip(1).any(|arg| arg == "--child") {
        println!("子进程 pid = {}", process::id());
        process::exit(7);
    }

    // 启动子进程并等它结束，同时收集 stdout / stderr
    let exe = std::env::current_exe()?;
    let output = Command::new(exe).arg("--child").output()?;

    assert_eq!(output.status.code(), Some(7));
    assert!(!output.status.success());

    let text = String::from_utf8_lossy(&output.stdout);
    assert!(text.contains("子进程 pid = "));
    println!("子进程退出码 {:?}，输出：{}", output.status.code(), text.trim());

    Ok(())
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[process.Command\|Command]] | 进程构建器，配置程序、参数、环境、目录与标准流。 |
| `Command::arg` / `args` | 追加一个 / 多个命令行参数，不做任何转义。 |
| `Command::env` / `env_remove` / `current_dir` | 增删环境变量、设置子进程工作目录。 |
| `Command::spawn` | 立即启动，返回 `Child`，不等待。 |
| `Command::output` | 启动并等待，收集完整输出；只想要状态时用 `status`。 |
| `Child` | 运行中或已退出的子进程句柄，可 `kill` 可 `wait`。 |
| `Child::wait` / `wait_with_output` | 阻塞等待结束，后者顺带收走管道输出。 |
| `ChildStdin` / `ChildStdout` / `ChildStderr` | 子进程的三条流，分别实现 [[io.Write\|Write]] / [[io.Read\|Read]]。 |
| `Stdio` | 描述某条标准流怎么接：继承、`piped`、`null`。 |
| `Output` | 已结束进程的 `status`、`stdout`、`stderr`。 |
| `ExitStatus` | 退出状态：`success()` 判 0，`code()` 取具体码。 |
| `ExitCode` | 可以从 `main` 返回的退出码。 |
| [[process.exit\|exit]] | 立刻以指定码终止当前进程，不跑析构。 |
| `process::abort` | 异常方式终止进程，Unix 上是 `SIGABRT`。 |
| `process::id` | 返回当前进程的 PID。 |
| [[process.Termination\|Termination]] | `main` 返回类型可实现的 trait，`Result` 与 `ExitCode` 都已实现。 |

## 注意事项

> [!danger] `exit` 会跳过析构与 flush
> 所有局部变量的 `Drop` 都不会执行：[[io.BufWriter|BufWriter]] 里没写出的数据直接丢，`Drop` 里删临时文件、提交事务的代码也不会跑。要么在调用前显式 `flush()` / `drop`，要么干脆从 `main` 返回 `Result` / `ExitCode` 让运行时正常收尾。

> [!warning] 没有 shell，管道也不免费
> `Command::new("ls")` 是直接 exec，不是 `sh -c "ls"`：重定向、通配符、`&&`、变量替换都不生效，需要就自己起 `sh -c` / `cmd /C`。另外 `output()` 会把子进程输出全部读进内存，遇到持续输出或永不退出的程序会一直阻塞（管道缓冲写满后双方互等）；这种场景用 `spawn()` 加 [[io.BufReader|BufReader]] 自己按行读。

> [!tip] 退出状态不等于「成功 / 失败」
> `success()` 只看退出码是否为 0。Unix 上进程被信号杀死时 `code()` 返回 `None`，要拿具体信号得用 [[os|std::os]] 里的 `ExitStatusExt::signal`；需要把非零状态当成错误返回时，用 `ExitStatus::exit_ok()` 或 `ExitStatusError`。

## 相关

- [[env|std::env]]：命令行参数、环境变量、当前目录——`Command` 的常见搭档。
- [[io|std::io]]：管道读写的就是普通的 `Read` / `Write`。
- [[thread|std::thread]]：多线程与子进程结合时，注意别在锁里等待子进程。
- [[11-错误处理|错误处理]]：`io::Result` 与从 `main` 返回错误。
- [[os|std::os]]：平台专属的进程与退出状态扩展。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 18 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`Child`](https://doc.rust-lang.org/std/process/struct.Child.html)
- [`ChildStderr`](https://doc.rust-lang.org/std/process/struct.ChildStderr.html)
- [`ChildStdin`](https://doc.rust-lang.org/std/process/struct.ChildStdin.html)
- [`ChildStdout`](https://doc.rust-lang.org/std/process/struct.ChildStdout.html)
- [[process.Command|`Command`]]
- [`CommandArgs`](https://doc.rust-lang.org/std/process/struct.CommandArgs.html)
- [`CommandEnvs`](https://doc.rust-lang.org/std/process/struct.CommandEnvs.html)
- [`ExitCode`](https://doc.rust-lang.org/std/process/struct.ExitCode.html)
- [`ExitStatus`](https://doc.rust-lang.org/std/process/struct.ExitStatus.html)
- [`Output`](https://doc.rust-lang.org/std/process/struct.Output.html)
- [`Stdio`](https://doc.rust-lang.org/std/process/struct.Stdio.html)
- [`CommandResolvedEnvs`](https://doc.rust-lang.org/std/process/struct.CommandResolvedEnvs.html)
- [`ExitStatusError`](https://doc.rust-lang.org/std/process/struct.ExitStatusError.html)

### 特质

- [[process.Termination|`Termination`]]

### 函数

- [`abort`](https://doc.rust-lang.org/std/process/fn.abort.html)
- [[process.exit|`exit`]]
- [`id`](https://doc.rust-lang.org/std/process/fn.id.html)
- [`abort_immediate`](https://doc.rust-lang.org/std/process/fn.abort_immediate.html)

<!-- END AUTO ITEMS -->
