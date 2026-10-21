---
title: "std::process::exit"
type: std-条目
kind: 函数
module: process
slug: process.exit
stable: "1.0.0"
tags:
  - std/错误
aliases:
  - exit
一句话: 立即以指定退出码终止当前进程，立刻返回 OS，但不会运行任何析构函数。
---

# `exit`

> [!abstract] 一句话
> `std::process::exit(code)` 让进程**当场结束**并把 `code` 交给操作系统。它永不返回，代价是当前栈上、其他线程栈上的析构函数一律不执行。

## 简介

正常的退出方式是让 `main` 返回：栈层层展开，每个 `Drop` 都会跑，`BufWriter` 里的缓冲会被 flush。`exit` 走的是另一条路——直接向操作系统请求终止，**跳过所有析构**。

这个差别在两种场景下很要紧。写文件、写管道的程序如果还有未 flush 的缓冲，`exit` 一来数据就丢了；持锁或持有临时资源的程序，`exit` 之后这些资源只能等操作系统回收。反过来，如果只是想给脚本返回一个非零状态码，而所有工作已经写完、`Drop` 里没有必须执行的收尾，`exit` 是最省事的做法。

更推荐的写法是让 `main` 返回 `ExitCode`（或 `Result`）：既能把退出码传给系统，又能保证析构照常执行。`exit` 还会运行注册在 `atexit` 里的退出处理函数，因此那些 handler 必须保证在任何时刻、任意线程状态下都能安全执行。

## 签名与参数

```text
pub fn exit(code: i32) -> !
```

| 参数 | 说明 |
| --- | --- |
| `code` | 交给操作系统的退出码，`0` 表示成功。 |
| 返回 `!` | 永不返回，因此可以当作 `match` 分支的收尾。 |

- 返回类型是 `!`（never type）：它之后的语句永远不会执行，所以常用于「出错就退出」的分支。
- 退出码最终由 shell 解释：Unix 上通常只保留低 8 位，`256` 会变成 `0`，所以业务码建议落在 `0..=255`。
- 不会 flush 你手里的缓冲：先 `flush` 或让 writer 先 `drop`，再调 `exit`。

## 示例

### 出错即退出

```rust
use std::process;

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();

    if args.is_empty() {
        eprintln!("用法: demo <文件>");
        // 只给系统一个退出码，之后的代码不会再执行
        process::exit(2);
    }

    println!("收到 {} 个参数", args.len());
}
```

### 推荐写法：用 `ExitCode` 代替 `exit`

```rust
use std::process::ExitCode;

fn main() -> ExitCode {
    match std::env::var("RUST_VAULT_MODE") {
        Ok(mode) if !mode.is_empty() => {
            println!("mode = {mode}");
            ExitCode::SUCCESS
        }
        _ => {
            eprintln!("缺少环境变量 RUST_VAULT_MODE");
            ExitCode::FAILURE
        }
    }
}
```

`main` 返回 `ExitCode` 时，函数体里的局部变量会正常析构，缓冲也会正常写出，同时退出码照旧传给系统。

## 常见陷阱

1. **`exit` 不跑析构**：缓冲区里没 flush 的数据会丢、`File` 不会关闭，对策是先手动 `flush` 再退出，或干脆让 `main` 返回。
2. **在 `Drop` 或锁里调 `exit`**：其他线程被瞬间掐断，可能留下半写文件，对策是把终止决策集中到最外层。
3. **以为 `Drop` 会兜底**：`exit` 之后 `Drop` 完全不执行，依赖 `Drop` 清理临时文件的逻辑会失效。
4. **退出码越界**：Unix 只取低 8 位，`exit(256)` 实际是 `0`（看似成功），对策是业务码控制在 `0..=255`。
5. **用 `exit` 代替错误处理**：它绕过了清理逻辑，对策是能用 `Result` + `?` 向上传播就别提前终止。

## 相关

- [[process|std::process 模块]]：`Command`、`ExitStatus`、`ExitCode` 都在这里。
- [[process.Command|Command]]：启动子进程，与「终止自己」正好相反。
- [[process.Termination|Termination]]：`main` 返回值如何变成退出码。
- [[macro.panic|panic]]：panic 会展开栈并跑析构，`exit` 不会，两者语义不同。
- [[11-错误处理|错误处理]]：优先用 `Result` 传播错误而不是提前退出。
