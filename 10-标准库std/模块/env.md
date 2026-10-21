---
title: "std::env"
type: std-模块
module: env
stable: "1.0.0"
unstable: false
tags:
  - std/模块
  - std/IO
aliases:
  - env
  - 环境变量
一句话: 进程环境的检查与修改：命令行参数、环境变量、当前目录、可执行文件路径与临时目录。
---

# std::env

> [!abstract] 一句话
> `std::env` 让你读取进程的命令行参数、环境变量、当前工作目录与可执行文件路径，并拼接或拆分 `PATH` 风格的路径列表。

## 模块简介

每个程序启动时都带着一组外部状态：命令行参数、环境变量、工作目录。`std::env` 就是访问这些状态的入口，全部是同步的、针对**当前进程**的操作。

模块里的函数几乎都成对出现：不带后缀的返回 `String`（要求内容合法 UTF-8），以 `_os` 结尾的返回 `OsString`（保留原始字节，读取后再自行处理编码）。`args` 与 `args_os`、`var` 与 `var_os`、`vars` 与 `vars_os` 都是这样的组合。在 Linux 上两者通常没有区别，在 Windows 上命令行参数和环境变量都可能是非 UTF-8 的。

`env::args()` 返回的迭代器第一个元素是程序名（对应 C 的 `argv[0]`），因此取业务参数时要先 `next()` 跳过。读取环境变量失败会返回 `VarError`，区分「变量不存在」（`NotPresent`）和「值不是合法 UTF-8」（`NotUnicode`）。

修改环境变量（`set_var`、`remove_var`）只影响当前进程及其子进程，且会与其他线程的读取产生竞争，因此在 2024 edition 中它们是 `unsafe` 的。当前目录与可执行文件路径返回 `io::Result<PathBuf>`，可直接与 [[path|std::path]] 的工具配合使用。

## 快速上手

```rust
use std::env;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // 第一个参数是程序名，其余才是业务参数
    let mut args = env::args();
    let program = args.next().unwrap_or_else(|| String::from("demo"));
    let rest: Vec<String> = args.collect();
    println!("程序名 = {program}");
    println!("参数 = {rest:?}");

    // 读取环境变量，缺失时可以回退到另一个名字
    let home = env::var("HOME").or_else(|_| env::var("USERPROFILE"));
    println!("用户目录 = {home:?}");

    // 带默认值的写法
    let level = env::var("RUST_LOG").unwrap_or_else(|_| String::from("info"));
    assert!(!level.is_empty());

    // 当前工作目录与可执行文件路径
    let dir = env::current_dir()?;
    println!("当前目录 = {}", dir.display());
    let exe = env::current_exe()?;
    println!("可执行文件 = {}", exe.display());

    // 临时目录：适合放测试用的临时文件
    println!("临时目录 = {}", env::temp_dir().display());

    Ok(())
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[env.args|args]] | 遍历命令行参数（`String`），第一个是程序名。 |
| `env::args_os` | 同上，但返回 `OsString`，允许非 UTF-8。 |
| [[env.var|var]] | 读取环境变量，失败返回 `VarError`。 |
| `env::var_os` | 读取环境变量，返回 `Option<OsString>`。 |
| `env::vars` | 遍历全部环境变量，产出 `(String, String)`。 |
| `env::vars_os` | 遍历全部环境变量，产出 `(OsString, OsString)`。 |
| `env::set_var` | 设置环境变量；2024 edition 中是 `unsafe`。 |
| `env::remove_var` | 删除环境变量；2024 edition 中是 `unsafe`。 |
| `env::current_dir` | 返回当前工作目录 `PathBuf`。 |
| `env::set_current_dir` | 切换当前工作目录。 |
| `env::current_exe` | 返回当前可执行文件的完整路径。 |
| `env::temp_dir` | 返回系统临时目录。 |
| `env::join_paths` / `env::split_paths` | 拼接 / 拆分 `PATH` 风格的路径列表。 |
| `env::VarError` | `NotPresent` 或 `NotUnicode`。 |
| `env::Args` / `env::Vars` | 参数与环境变量迭代器类型。 |

## 注意事项

> [!warning] 平台差异
> Windows 的环境变量名不区分大小写，Linux 区分；`PATH` 分隔符在 Windows 上是 `;`、在 Unix 上是 `:`。拼接和拆分请用 `join_paths` / `split_paths`，不要手写分隔符。

> [!danger] 2024 edition 中修改变量需要 `unsafe`
> `set_var` / `remove_var` 会改写进程全局状态，其他线程可能正在读取同一变量。多线程程序应避免在运行时修改环境，改为把配置显式传参。

> [!tip] 非 UTF-8 用 `_os` 版本
> Windows 的路径与参数可能不是合法 UTF-8。需要原样保留时用 `args_os` / `var_os` 和 `OsString`，不要直接 `to_string_lossy` 后再拼路径。

## 相关

- [[env.args|args]] 与 [[env.var|var]]：最常用的两个入口。
- [[path|std::path 模块]]：当前目录、可执行文件路径都是 `PathBuf`。
- [[process|std::process 模块]]：子进程继承当前进程的环境变量。
- [[fs|std::fs 模块]]：配合 `current_dir` / `temp_dir` 组织文件读写。
- [[ffi.OsString|OsString]]：非 UTF-8 参数与环境变量的载体。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 22 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`Args`](https://doc.rust-lang.org/std/env/struct.Args.html)
- [`ArgsOs`](https://doc.rust-lang.org/std/env/struct.ArgsOs.html)
- [`JoinPathsError`](https://doc.rust-lang.org/std/env/struct.JoinPathsError.html)
- [`SplitPaths`](https://doc.rust-lang.org/std/env/struct.SplitPaths.html)
- [`Vars`](https://doc.rust-lang.org/std/env/struct.Vars.html)
- [`VarsOs`](https://doc.rust-lang.org/std/env/struct.VarsOs.html)

### 枚举

- [`VarError`](https://doc.rust-lang.org/std/env/enum.VarError.html)

### 函数

- [[env.args|`args`]]
- [`args_os`](https://doc.rust-lang.org/std/env/fn.args_os.html)
- [`current_dir`](https://doc.rust-lang.org/std/env/fn.current_dir.html)
- [`current_exe`](https://doc.rust-lang.org/std/env/fn.current_exe.html)
- [`home_dir`](https://doc.rust-lang.org/std/env/fn.home_dir.html)
- [`join_paths`](https://doc.rust-lang.org/std/env/fn.join_paths.html)
- [`remove_var`](https://doc.rust-lang.org/std/env/fn.remove_var.html)
- [`set_current_dir`](https://doc.rust-lang.org/std/env/fn.set_current_dir.html)
- [`set_var`](https://doc.rust-lang.org/std/env/fn.set_var.html)
- [`split_paths`](https://doc.rust-lang.org/std/env/fn.split_paths.html)
- [`temp_dir`](https://doc.rust-lang.org/std/env/fn.temp_dir.html)
- [[env.var|`var`]]
- [`var_os`](https://doc.rust-lang.org/std/env/fn.var_os.html)
- [`vars`](https://doc.rust-lang.org/std/env/fn.vars.html)
- [`vars_os`](https://doc.rust-lang.org/std/env/fn.vars_os.html)

<!-- END AUTO ITEMS -->
