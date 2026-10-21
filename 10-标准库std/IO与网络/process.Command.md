---
title: "std::process::Command"
type: std-条目
kind: 结构体
module: process
slug: process.Command
stable: "1.0.0"
tags:
  - std/类型
  - std/IO
aliases:
  - Command
一句话: 子进程构建器，先链式配好程序、参数、环境与 IO，再 spawn/output/status 启动它。
---

# `Command`

> [!abstract] 一句话
> `Command` 是**先配置、后启动**的子进程构建器：`Command::new("程序")` 建出一个默认配置，再用 `arg`、`env`、`current_dir`、`stdout` 等链式方法描述清楚「怎么跑」，最后用 `spawn` / `output` / `status` 真正启动。

## 简介

绝大多数场景不是「调一个函数」，而是「填一张启动表单」：程序路径、命令行参数、工作目录、环境变量、三根标准流怎么接。`Command` 把这堆配置收进一个结构体，每个设置方法都返回 `&mut Command`，所以可以一路 `.arg(..).env(..).output()` 写下来。

它和「直接调 `system()`」的区别在于：参数以数组形式逐个传入，**不经过 shell**，因此不存在引号拼接和注入问题；反过来说，通配符 `*`、管道 `|`、重定向 `>` 也不会被解释，要这些语义就显式启动一个 shell。

三种启动方式是层次递进的：`status()` 只等退出状态，`output()` 等结束并收集输出，`spawn()` 拿到 `Child` 后立刻返回，交给你自己控制等待与管道读写。同一个 `Command` 可以反复启动多个进程，配置会保留。

## 常用方法

### 构造与参数

| 方法 | 说明 |
| --- | --- |
| `new(program)` | 以程序路径创建命令，其余配置为默认值。 |
| `arg(arg)` | 追加一个命令行参数。 |
| `args(args)` | 批量追加多个参数，接受任意可迭代对象。 |

### 环境变量

| 方法 | 说明 |
| --- | --- |
| `env(key, val)` | 插入或覆盖一个环境变量。 |
| `envs(vars)` | 批量插入或覆盖环境变量。 |
| `env_remove(key)` | 移除变量，并阻止从父进程继承它。 |
| `env_clear()` | 清空所有变量，并阻止继承父进程环境。 |

### 工作目录与标准流

| 方法 | 说明 |
| --- | --- |
| `current_dir(dir)` | 设置子进程的工作目录。 |
| `stdin(cfg)` | 配置子进程的标准输入。 |
| `stdout(cfg)` | 配置子进程的标准输出。 |
| `stderr(cfg)` | 配置子进程的标准错误。 |

`stdin` / `stdout` / `stderr` 的参数是 `Stdio`，常用取值 `Stdio::null()`、`Stdio::piped()`、`Stdio::inherit()`，也可以直接传 `Stdio` 的 `Into` 实现。

### 启动子进程

| 方法 | 说明 |
| --- | --- |
| `spawn()` | 启动子进程并立刻返回 `Child` 句柄。 |
| `output()` | 启动并等待结束，收集全部输出。 |
| `status()` | 启动并等待结束，只取退出状态。 |

### 读取配置

| 方法 | 说明 |
| --- | --- |
| `get_program()` | 返回传给 `new` 的程序路径。 |
| `get_args()` | 返回待传参数的迭代器。 |
| `get_envs()` | 返回显式设置的环境变量迭代器。 |
| `get_current_dir()` | 返回设置的工作目录，未设置则 `None`。 |

## 示例

### 只配置不启动：把 `Command` 当表单来读

```rust
use std::ffi::OsStr;
use std::path::Path;
use std::process::Command;

fn main() {
    let mut cmd = Command::new("my-tool");
    cmd.arg("--verbose")
        .args(["build", "release"])
        .env("RUST_LOG", "debug")
        .env_remove("HOME")
        .current_dir(Path::new("."));

    assert_eq!(cmd.get_program(), OsStr::new("my-tool"));
    assert_eq!(cmd.get_args().count(), 3);
    assert_eq!(cmd.get_current_dir(), Some(Path::new(".")));
    // 只统计显式设置过的变量，不含继承来的
    assert!(cmd.get_envs().count() >= 1);
    println!("参数个数: {}", cmd.get_args().count());
}
```

### 真正启动一个子进程

```rust
use std::process::Command;

fn main() -> std::io::Result<()> {
    // 分平台挑一个系统自带的小程序，避免依赖第三方命令
    let mut cmd = if cfg!(windows) {
        let mut c = Command::new("cmd");
        c.args(["/C", "ver"]);
        c
    } else {
        let mut c = Command::new("sh");
        c.args(["-c", "uname"]);
        c
    };

    // output 会等子进程结束后把 stdout / stderr 一起收集回来
    let output = cmd.output()?;
    println!("退出码: {:?}", output.status.code());
    println!("标准输出: {}", String::from_utf8_lossy(&output.stdout).trim());
    Ok(())
}
```

## 常见陷阱

1. **参数不经过 shell**：`Command::new("ls").arg("*.rs")` 里的 `*.rs` 不会被展开，对策是自己列举文件，或显式 `sh -c` / `cmd /C`。
2. **`spawn` 不会等你，也不会替你收尸**：`Child` 被 drop 后进程仍在跑，必须 `wait` 或 `wait_with_output`，否则可能留下僵尸进程。
3. **`spawn` 时输出默认继承终端**：想拿到输出必须 `stdout(Stdio::piped())` 再读 `Child::stdout`，或者干脆用 `output()`。
4. **`env_clear()` 会连 `PATH` 一起清掉**：子进程可能因此找不到程序，对策是清空后用 `env("PATH", ...)` 补回需要的变量。
5. **找不到程序返回 `NotFound`**：程序名拼错或不在 `PATH` 里都会这样，对策是传绝对路径并检查 `ErrorKind`。

## 相关

- [[process|std::process 模块]]：`Child`、`Output`、`ExitStatus`、`Stdio` 都在这里。
- [[process.exit|exit]]：终止当前进程，与「启动子进程」正好相反。
- [[env.var|env::var]]：读当前进程的环境变量，决定传给子进程什么。
- [[os|std::os 模块]]：`OsStr` 用于传非 UTF-8 的程序名与参数。
- [[01-命令行工具|命令行工具]]：用 `Command` 包装外部命令的实战场景。
