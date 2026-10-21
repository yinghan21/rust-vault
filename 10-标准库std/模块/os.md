---
title: "std::os"
type: std-模块
module: os
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - os
一句话: "平台相关能力的入口：std::os::unix / std::os::windows 等子模块，模块本身没有公开条目。"
---

# std::os

> [!abstract] 一句话
> `std::os` 本身不导出任何条目，它是一组平台子模块的命名空间——`std::os::unix`、`std::os::windows`、`std::os::wasi`——里面放着标准库基线之外的平台扩展特质与类型。

## 模块简介

先说清一件事：`std::os` **没有自己的公开条目**，没有函数、没有结构体，只有子模块。真正的 API 都在 `std::os::unix`、`std::os::windows` 这类子模块里，而每个子模块只在对应平台上参与编译。所以本页没有「常用条目」表，下文列出的是常用的平台子模块与扩展特质。

子模块放的是「标准库基线的平台扩展」：Unix 一侧有 `PermissionsExt`（读写 `mode` 权限位）、`OsStrExt`/`OsStringExt`（`OsStr` 与字节序列互转）、`UnixStream`/`UnixListener`/`UnixDatagram`（Unix 域套接字）、`CommandExt`（设置 `uid`/`gid`、用 `exec` 替换进程）、`MetadataExt`（inode、设备号）；Windows 一侧有 `OpenOptionsExt`（`share_mode`、`custom_flags`）、`MetadataExt`（文件属性、创建时间）、`AsRawHandle`/`FromRawHandle`/`OwnedHandle`（与 `HANDLE` 互转）、`symlink_file`/`symlink_dir`（区分文件与目录符号链接）、`CommandExt`（`CREATE_NO_WINDOW` 等创建标志）。

跨平台代码的写法是「主干跨平台，差异集中收口」：核心逻辑只用 `std::fs`、`std::net`、`std::process` 这些跨平台接口，把平台差异放进一个函数或一个模块，用 `#[cfg(unix)]`、`#[cfg(windows)]` 分支实现。需要判断当前平台时，用 [[env|std::env]] 的 `consts::{OS, ARCH, FAMILY}`——它们是编译期常量，可以直接参与 `cfg!` 表达式的比较。

和 [[ffi|std::ffi]] 的分工要记牢：`OsStr`/`OsString` 是「操作系统字符串」，在 Unix 上是任意字节、在 Windows 上是 WTF-8 编码，转换成 `str` 可能失败；把这些值拆成字节或宽字符的能力就来自 `std::os` 的扩展特质。相应地，[[path.Path|Path]]/`PathBuf` 也提供了平台扩展（比如 Windows 的盘符前缀、Unix 的字节视图）。

## 快速上手

```rust
use std::ffi::OsString;
use std::path::Path;

fn main() {
    // 跨平台部分：编译期平台常量 + 普通路径处理
    println!("OS = {}", std::env::consts::OS);
    println!("FAMILY = {}", std::env::consts::FAMILY);
    println!("ARCH = {}", std::env::consts::ARCH);

    let name = OsString::from("报告.txt");
    let path = Path::new(&name);
    assert!(path.ends_with("报告.txt"));

    // 平台专用能力必须用 #[cfg] 属性门控，而不是运行期 if
    #[cfg(unix)]
    {
        use std::os::unix::ffi::OsStrExt;
        let bytes = name.as_os_str().as_bytes();
        println!("Unix 下 OsStr 是字节序列，长度 = {}", bytes.len());
    }

    #[cfg(windows)]
    {
        use std::os::windows::ffi::OsStrExt;
        let wide: Vec<u16> = name.encode_wide().collect();
        println!("Windows 下 OsStr 可按 UTF-16 编码，单元数 = {}", wide.len());
    }

    // cfg! 只产生 bool，两个分支都要能编译
    println!("是否 Windows = {}", cfg!(windows));
}
```

## 常用条目（平台子模块）

> [!note] 本模块没有公开条目
> 下面列出的是 `std::os` 下最常用的子模块与扩展特质，它们分别只在对应平台上可用。

| 条目 | 说明 |
| --- | --- |
| `std::os::unix` | Unix（Linux、macOS、BSD）平台扩展的总入口。 |
| `std::os::unix::fs::PermissionsExt` | 读写 Unix 权限位 `mode`。 |
| `std::os::unix::ffi::OsStrExt` / `OsStringExt` | `OsStr` / `OsString` 与字节序列互转。 |
| `std::os::unix::net::UnixStream` / `UnixListener` | Unix 域套接字。 |
| `std::os::unix::process::CommandExt` | 设置 `uid`/`gid`，或用 `exec` 替换进程。 |
| `std::os::windows` | Windows 平台扩展的总入口。 |
| `std::os::windows::fs::OpenOptionsExt` | 设置 `share_mode`、`custom_flags`。 |
| `std::os::windows::fs::MetadataExt` | 读取文件属性、创建时间等。 |
| `std::os::windows::io::AsRawHandle` / `OwnedHandle` | 与系统 `HANDLE` 互转、持有句柄。 |
| `std::os::windows::process::CommandExt` | 设置进程创建标志，如隐藏窗口。 |
| `std::os::windows::ffi::OsStrExt` | `OsStr` 与 UTF-16 宽字符互转。 |
| `std::env::consts` | 编译期平台常量：`OS`、`ARCH`、`FAMILY`。 |

## 注意事项

> [!warning] 平台专用 API 必须用 `#[cfg]` 门控
> 直接写 `use std::os::unix::fs::PermissionsExt;` 会让 Windows 构建失败。把平台代码放进 `#[cfg(unix)]` / `#[cfg(windows)]` 的块或模块里，并保证**每个平台都有一份实现**。

> [!tip] `OsStr` 不是 `str`
> 文件名在 Unix 上可以是任意非 UTF-8 字节。需要给人看时用 `to_string_lossy`（非法字节变成替换字符），需要原样处理时用平台扩展特质取字节或宽字符，不要先 `to_str().unwrap()`。

> [!danger] `cfg!` 不能替代 `#[cfg]`
> `if cfg!(windows) { ... }` 只是让分支恒为 `false/true`，**两个分支都必须能编译**，Windows 专用 API 照样报错。要彻底排除代码，必须用属性 `#[cfg(...)]`。

## 相关

- [[ffi|std::ffi]]：`OsStr`/`OsString` 与 C 字符串。
- [[path|std::path]]：跨平台路径，及其平台扩展。
- [[env|std::env]]：`consts` 平台常量与环境变量。
- [[process|std::process]]：子进程与平台创建标志。
- [[fs|std::fs]]：被 `PermissionsExt` 扩展的文件系统 API。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 0 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

<!-- END AUTO ITEMS -->
