---
title: "std::fs"
type: std-模块
module: fs
stable: "1.0.0"
unstable: false
tags:
  - std/模块
  - std/IO
aliases:
  - fs
  - 文件系统
一句话: 文件系统操作：读写文件、创建/删除目录、查询元数据与权限。
---

# std::fs

> [!abstract] 一句话
> `std::fs` 是标准库的文件系统入口：整文件读写、`File` 句柄、目录遍历、元数据与权限。

## 模块简介

`std::fs` 提供的是**同步**文件系统 API。大多数函数是一次性操作（打开、读整个文件、创建目录），需要精细控制时用 [[fs.File|File]] 配合 [[io.Read|Read]] / [[io.Write|Write]] / [[io.Seek|Seek]] 手动读写。

几个使用频率最高的函数：

- `fs::read` / `fs::read_to_string`：一次读入整个文件，最省事。
- `fs::write`：一次写入整个文件（覆盖）。
- `fs::read_dir`：遍历目录，返回 `ReadDir` 迭代器。
- `fs::create_dir_all` / `fs::remove_dir_all`：递归建目录 / 删目录。
- `fs::metadata` / `fs::symlink_metadata`：查文件类型、大小、权限、修改时间。

所有操作都返回 `io::Result<T>`，错误类型是 `std::io::Error`，可以直接用 `?` 传播。

## 快速上手

```rust
use std::fs;
use std::io;

fn main() -> io::Result<()> {
    let path = std::env::temp_dir().join("rust_vault_fs_demo.txt");

    // 写整个文件（不存在则创建，存在则覆盖）
    fs::write(&path, "你好，Rust\n")?;

    // 读整个文件为 String（要求内容是合法 UTF-8）
    let text = fs::read_to_string(&path)?;
    assert_eq!(text, "你好，Rust\n");

    // 追加内容
    use std::io::Write;
    let mut f = fs::OpenOptions::new().append(true).open(&path)?;
    writeln!(f, "第二行")?;

    let meta = fs::metadata(&path)?;
    assert!(meta.is_file());
    println!("大小 = {} 字节", meta.len());

    fs::remove_file(&path)?;
    Ok(())
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[fs.File|File]] | 打开的文件句柄，实现 `Read`/`Write`/`Seek`。 |
| [[fs.OpenOptions|OpenOptions]] | 细粒度控制打开模式（读/写/追加/创建/截断）。 |
| `fs::read` | 读整个文件为 `Vec<u8>`。 |
| [[fs.read_to_string|fs::read_to_string]] | 读整个文件为 `String`。 |
| [[fs.write|fs::write]] | 一次写入整个文件。 |
| `fs::read_dir` | 遍历目录条目。 |
| `fs::create_dir` / `fs::create_dir_all` | 创建单层 / 多层目录。 |
| `fs::remove_file` / `fs::remove_dir_all` | 删除文件 / 递归删除目录。 |
| `fs::metadata` | 获取元数据（跟随符号链接）。 |
| `fs::canonicalize` | 解析为绝对路径并消除 `..`、符号链接。 |
| `fs::copy` / `fs::rename` | 复制 / 移动（重命名）。 |

## 注意事项

> [!warning] 平台差异
> - 路径分隔符、大小写敏感性、权限位都随平台不同；用 [[path.PathBuf|PathBuf]] 拼接路径，不要手写 `/`。
> - Windows 上目录本身也是文件，`metadata().is_dir()` 比后缀判断可靠。

> [!tip] 性能
> - 小文件用 `fs::read` / `fs::read_to_string`；大文件或流式处理用 [[fs.File|File]] + [[io.BufReader|BufReader]]。
> - 大量小写入时，`BufWriter` 能显著减少系统调用。

> [!danger] 常见错误
> - `read_to_string` 遇到非 UTF-8 内容会返回 `InvalidData`，二进制文件请用 `fs::read`。
> - 打开不存在的文件不会自动创建，除非 `OpenOptions::create(true)`。
> - 删除正在被占用的文件（Windows）会失败，先关闭句柄。

## 相关

- [[io|std::io 模块]]：读写 trait 与标准流。
- [[path|std::path 模块]]：跨平台路径处理。
- [[env|std::env 模块]]：当前目录、临时目录。
- [[11-错误处理|错误处理]]：`io::Result` 与 `?` 的用法。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 33 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`DirBuilder`](https://doc.rust-lang.org/std/fs/struct.DirBuilder.html)
- [`DirEntry`](https://doc.rust-lang.org/std/fs/struct.DirEntry.html)
- [[fs.File|`File`]]
- [`FileTimes`](https://doc.rust-lang.org/std/fs/struct.FileTimes.html)
- [`FileType`](https://doc.rust-lang.org/std/fs/struct.FileType.html)
- [`Metadata`](https://doc.rust-lang.org/std/fs/struct.Metadata.html)
- [[fs.OpenOptions|`OpenOptions`]]
- [`Permissions`](https://doc.rust-lang.org/std/fs/struct.Permissions.html)
- [`ReadDir`](https://doc.rust-lang.org/std/fs/struct.ReadDir.html)
- [`Dir`](https://doc.rust-lang.org/std/fs/struct.Dir.html)

### 枚举

- [`TryLockError`](https://doc.rust-lang.org/std/fs/enum.TryLockError.html)

### 函数

- [`canonicalize`](https://doc.rust-lang.org/std/fs/fn.canonicalize.html)
- [`copy`](https://doc.rust-lang.org/std/fs/fn.copy.html)
- [`create_dir`](https://doc.rust-lang.org/std/fs/fn.create_dir.html)
- [`create_dir_all`](https://doc.rust-lang.org/std/fs/fn.create_dir_all.html)
- [`exists`](https://doc.rust-lang.org/std/fs/fn.exists.html)
- [`hard_link`](https://doc.rust-lang.org/std/fs/fn.hard_link.html)
- [`metadata`](https://doc.rust-lang.org/std/fs/fn.metadata.html)
- [`read`](https://doc.rust-lang.org/std/fs/fn.read.html)
- [`read_dir`](https://doc.rust-lang.org/std/fs/fn.read_dir.html)
- [`read_link`](https://doc.rust-lang.org/std/fs/fn.read_link.html)
- [[fs.read_to_string|`read_to_string`]]
- [`remove_dir`](https://doc.rust-lang.org/std/fs/fn.remove_dir.html)
- [`remove_dir_all`](https://doc.rust-lang.org/std/fs/fn.remove_dir_all.html)
- [`remove_file`](https://doc.rust-lang.org/std/fs/fn.remove_file.html)
- [`rename`](https://doc.rust-lang.org/std/fs/fn.rename.html)
- [`set_permissions`](https://doc.rust-lang.org/std/fs/fn.set_permissions.html)
- [`set_times`](https://doc.rust-lang.org/std/fs/fn.set_times.html)
- [`set_times_nofollow`](https://doc.rust-lang.org/std/fs/fn.set_times_nofollow.html)
- [`soft_link`](https://doc.rust-lang.org/std/fs/fn.soft_link.html)
- [`symlink_metadata`](https://doc.rust-lang.org/std/fs/fn.symlink_metadata.html)
- [[fs.write|`write`]]
- [`set_permissions_nofollow`](https://doc.rust-lang.org/std/fs/fn.set_permissions_nofollow.html)

<!-- END AUTO ITEMS -->
