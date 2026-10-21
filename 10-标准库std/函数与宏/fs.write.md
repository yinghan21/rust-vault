---
title: "std::fs::write"
type: std-条目
kind: 函数
module: fs
slug: fs.write
stable: "1.26.0"
tags:
  - std/IO
  - std/类型
aliases:
  - "write 函数"
  - "fs::write"
一句话: "把一段字节整体写成文件内容：文件不存在就创建，已存在就整个覆盖；成功返回 io::Result<()>。"
---

# `write`

> [!abstract] 一句话
> `std::fs::write(path, contents)` 把 `contents` 整体写进文件：不存在就创建，存在则**从头覆盖**（不是追加）。它是 `File::create` 加 `write_all` 的便捷组合，成功时返回 `Ok(())`。

## 简介

需要「把结果存到文件」时，手写的版本是 `File::create(path)?` 再 `file.write_all(bytes)?`，还要 `use std::io::Write`。`fs::write` 把这两步合并成一次调用，是写配置、导出文本、生成测试数据的最短路径。

两个参数都很宽容。`path: P` 只要实现 `AsRef<Path>`，`&str`、`String`、`PathBuf` 都行；`contents: C` 只要实现 `AsRef<[u8]>`，`&str`、`String`、`&[u8]`、`Vec<u8>`、`[u8; N]` 都可以，所以既能写文本也能写字节。

行为上有三点要记住。**第一，它会覆盖**：文件原有内容被截断，长度以这次写入为准，不是追加；追加要用 `OpenOptions::new().append(true).open(path)?`。**第二，目录必须已存在**：父目录不存在时在多数平台上会失败（`NotFound`），需要自己先 `fs::create_dir_all`。**第三，写入是「全部写成功」语义**：内部用 `write_all`，返回 `Ok(())` 表示所有字节都交给内核了，但这不等于数据已经落盘——要保证掉电不丢，还得对 `File` 调 `sync_all`。

它没有 `unsafe`，也不会 panic；所有失败都走 `io::Result`：权限不足、磁盘满、路径是目录、父目录缺失都在 `Err` 里。

## 签名与参数

```text
pub fn write<P: AsRef<Path>, C: AsRef<[u8]>>(path: P, contents: C) -> io::Result<()>
```

| 参数 | 说明 |
| --- | --- |
| `path` | 目标文件路径，`&str`、`String`、`PathBuf`、`&Path` 均可。 |
| `contents` | 要写入的字节序列，`&str`、`String`、`&[u8]`、`Vec<u8>`、`[u8; N]` 都实现 `AsRef<[u8]>`。 |
| 返回 `Ok(())` | 全部字节写入成功。 |
| 返回 `Err(io::Error)` | 创建/打开失败、权限不足、磁盘满、路径是目录等。 |

| 需求 | 用什么 |
| --- | --- |
| 整体覆盖，文本 | `fs::write(path, "text")` |
| 整体覆盖，字节 | `fs::write(path, &bytes)` |
| 追加到末尾 | `OpenOptions::new().append(true).open(path)?` 再 `write_all` |
| 多次小块写、减少系统调用 | `File::create` 加 [[io.BufWriter|BufWriter]] |
| 读回来 | [[fs.read_to_string|read_to_string]] 或 `fs::read` |

## 示例

### 写文本与写字节

```rust
use std::fs;

fn main() -> std::io::Result<()> {
    let path = "demo_write.txt";

    fs::write(path, b"Lorem ipsum")?;   // &[u8; N]
    fs::write(path, "dolor sit")?;      // &str，整体覆盖上一个内容

    assert_eq!(fs::read_to_string(path)?, "dolor sit");

    // String 与 Vec<u8> 也能直接传
    let owned = String::from("第三版内容");
    fs::write(path, &owned)?;
    assert_eq!(fs::read(path)?.len(), owned.len());

    fs::remove_file(path)?;
    println!("写入并校验完成");
    Ok(())
}
```

### 覆盖而不是追加

```rust
use std::fs;

fn main() -> std::io::Result<()> {
    let path = "demo_overwrite.txt";

    fs::write(path, "第一行\n")?;
    // 再写一次是「从头覆盖」，不是追加：文件里只剩这一行
    fs::write(path, "只有这一行\n")?;
    assert_eq!(fs::read_to_string(path)?, "只有这一行\n");

    // 父目录不存在会失败，先建目录
    fs::create_dir_all("demo_dir/sub")?;
    fs::write("demo_dir/sub/a.txt", "ok")?;
    assert_eq!(fs::read_to_string("demo_dir/sub/a.txt")?, "ok");

    fs::remove_dir_all("demo_dir")?;
    fs::remove_file(path)?;
    println!("覆盖与目录创建都正常");
    Ok(())
}
```

## 常见陷阱

1. **以为 `fs::write` 会追加**：它是 `File::create` 语义，每次调用都截断重写；追加要用 `OpenOptions::append(true)`。
2. **父目录不存在直接写**：多数平台上会返回 `NotFound`，写之前先 `fs::create_dir_all(parent)?`。
3. **路径指向一个目录**：返回 `IsADirectory` 之类的错误，`fs::write` 只能写文件。
4. **写完就以为已经落盘**：`Ok(())` 只说明交给了操作系统缓冲，要抗掉电得 `File::sync_all()`，那时就不能用这个便捷函数了。
5. **大文件一次 `fs::write`**：会把整个 `contents` 留在内存里，几十 GB 的场景应该流式写，用 [[io.BufWriter|BufWriter]] 分块。
6. **用相对路径做测试**：`cargo test` 的工作目录是 crate 根，可能与你手跑 `cargo run` 时不同，写文件前用 `env::temp_dir()` 或 `env::current_dir` 拼绝对路径更可靠。

## 相关

- [[fs|std::fs 模块]]：文件、目录、元数据相关的全部入口。
- [[fs.read_to_string|read_to_string]]：把刚写的内容读回来验证。
- [[fs.File|File]]：需要追加、`sync_all`、分段写时用它。
- [[io.BufWriter|BufWriter]]：大量小写入时套一层缓冲。
- [[11-错误处理|错误处理]]：`io::Result` 与 `?` 的标准处理方式。
