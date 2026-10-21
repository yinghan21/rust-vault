---
title: "std::fs::File"
type: std-条目
kind: 结构体
module: fs
slug: fs.File
stable: "1.0.0"
tags:
  - std/类型
  - std/IO
aliases:
  - File
一句话: 表示一个已打开文件的句柄，支持读写、定位与元数据操作。
---

# `File`

> [!abstract] 一句话
> `File` 是**已打开文件**的句柄：打开时选的模式决定它能读、能写还是两者皆可，用完离开作用域自动关闭。

## 简介

`File` 本身不存放文件内容，它持有操作系统返回的文件句柄，因此真正的读写、定位、权限查询都由系统调用完成。能做什么取决于用什么方式打开：`File::open` 得到只读句柄，`File::create` 得到只写且会清空旧内容的句柄，需要「读 + 写 + 追加 + 自定义创建」时改走 [[fs.OpenOptions|OpenOptions]]。

`File` 实现了 `Read`、`Write`、`Seek` 三个 [[io|std::io]] 特质，所以既能当普通读取器，也能定位到任意字节偏移再继续读写；同一个文件句柄上的读写位置是共享的。

它默认**不做任何缓冲**：每次 `read` / `write` 都是一次系统调用。大量小块的读写应该外包一层 [[io.BufReader|BufReader]] 或 [[io.BufWriter|BufWriter]]；相反，一次读整块大文件时缓冲反而是多余的。

## 常用方法

### 打开与创建

| 方法 | 说明 |
| --- | --- |
| `open(path)` | 以只读模式打开已有文件。 |
| `create(path)` | 以只写模式创建文件，已存在则清空。 |
| `create_new(path)` | 创建新文件，已存在则返回错误。 |
| `options()` | 返回空白的 `OpenOptions`，用于自定义打开方式。 |

### 落盘与长度

| 方法 | 说明 |
| --- | --- |
| `sync_all()` | 把文件内容与元数据都刷到磁盘。 |
| `sync_data()` | 只刷内容，可能不同步元数据。 |
| `set_len(size)` | 把文件截断或扩展到指定字节长度。 |

### 文件锁

| 方法 | 说明 |
| --- | --- |
| `lock()` | 获取独占锁，阻塞直到成功。 |
| `lock_shared()` | 获取共享锁，阻塞直到成功。 |
| `try_lock()` | 尝试获取独占锁，不阻塞。 |
| `try_lock_shared()` | 尝试获取共享锁，不阻塞。 |
| `unlock()` | 释放该文件上的全部锁。 |

### 元数据与属性

| 方法 | 说明 |
| --- | --- |
| `metadata()` | 查询文件元数据（长度、类型、时间等）。 |
| `try_clone()` | 克隆句柄，与原句柄共享读写位置。 |
| `set_permissions(perm)` | 修改文件权限。 |
| `set_times(times)` | 修改访问时间与修改时间。 |
| `set_modified(time)` | 只修改最后修改时间。 |

## 示例

### 创建、写入、读回、定位

```rust
use std::fs::File;
use std::io::{Read, Seek, SeekFrom, Write};
use std::path::PathBuf;

fn main() -> std::io::Result<()> {
    let mut path: PathBuf = std::env::temp_dir();
    path.push("rust_fs_file_demo.txt");

    // 创建（已存在则清空）并写入内容
    let mut file = File::create(&path)?;
    file.write_all(b"hello file")?;
    file.sync_all()?;
    drop(file);

    // 只读打开，读回全部内容
    let mut file = File::open(&path)?;
    let mut all = String::new();
    file.read_to_string(&mut all)?;
    assert_eq!(all, "hello file");

    // File 实现了 Seek：从第 6 个字节继续读
    file.seek(SeekFrom::Start(6))?;
    let mut tail = String::new();
    file.read_to_string(&mut tail)?;
    assert_eq!(tail, "file");

    assert_eq!(file.metadata()?.len(), 10);
    drop(file);

    std::fs::remove_file(&path)?;
    Ok(())
}
```

### `set_len` 与 `try_clone`

```rust
use std::fs::OpenOptions;
use std::io::{Read, Seek, SeekFrom, Write};
use std::path::PathBuf;

fn main() -> std::io::Result<()> {
    let mut path: PathBuf = std::env::temp_dir();
    path.push("rust_fs_file_len.txt");

    // 必须用读写模式打开：File::create 是只写句柄，读不出内容
    let file = OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .truncate(true)
        .open(&path)?;
    file.set_len(4)?; // 由 0 字节扩展为 4 个 0 字节
    assert_eq!(file.metadata()?.len(), 4);

    // 两个句柄共享同一个读写位置
    let mut writer = file.try_clone()?;
    let mut reader = file;
    writer.write_all(b"rust")?;
    reader.seek(SeekFrom::Start(0))?;

    let mut s = String::new();
    reader.read_to_string(&mut s)?;
    assert_eq!(s, "rust");

    drop(writer);
    drop(reader);
    std::fs::remove_file(&path)?;
    Ok(())
}
```

## 常见陷阱

1. **`File::create` 会清空旧文件**：想保留原内容请用 `OpenOptions::new().append(true)` 或 `create(true).truncate(false)`。
2. **`Drop` 里的关闭错误被忽略**：要确认数据真的落盘，就显式调用 `sync_all()` 并检查返回值。
3. **默认无缓冲导致系统调用过多**：循环里逐行、逐字节读写时，先包一层 [[io.BufReader|BufReader]] 或 [[io.BufWriter|BufWriter]]。
4. **`try_clone` 共享读写位置**：克隆出的句柄不是一个独立游标，任意一个移动位置都会影响另一个。
5. **文件锁只在协作进程间有效**：`lock` / `try_lock` 依赖操作系统支持，不是所有平台、所有文件系统都提供同等语义。

## 相关

- [[fs|std::fs 模块]]：文件系统相关条目总览。
- [[fs.OpenOptions|OpenOptions]]：需要读 + 写、追加或独占创建时的打开方式。
- [[io.Read|Read]]、[[io.Write|Write]]、[[io.Seek|Seek]]：`File` 实现的三个 IO 特质。
- [[io.BufReader|BufReader]]、[[io.BufWriter|BufWriter]]：给 `File` 加缓冲的包装类型。
- [[path.Path|Path]]：`open`、`create` 的路径参数类型。
