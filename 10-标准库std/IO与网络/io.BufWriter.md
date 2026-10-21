---
title: "std::io::BufWriter"
type: std-条目
kind: 结构体
module: io
slug: io.BufWriter
stable: "1.0.0"
tags:
  - std/类型
  - std/IO
aliases:
  - BufWriter
一句话: 给任意写入器加一层内存缓冲，把大量小块写合并成少数几次底层写入。
---

# `BufWriter`

> [!abstract] 一句话
> `BufWriter<W>` 先把数据攒在内存缓冲里，攒满或显式 `flush` 时才一次性写给底层写入器。

## 简介

对 `TcpStream` 或 [[fs.File|File]] 直接调用 `write`，每次都是一次系统调用；循环里逐条写小数据时开销会成倍放大。`BufWriter<W>` 把小块数据先追加进内存缓冲，只有缓冲满、显式刷新或缓冲区被替换时才真正写下去。

和 [[io.BufReader|BufReader]] 一样，它只对**小而频繁**的写有帮助：一次写很大一块、或者目标本来就在内存里（如 `Vec<u8>`）时，加缓冲没有收益。

它最大的坑是数据滞留在缓冲里：`BufWriter` 被丢弃时会尝试刷新，但**丢弃过程中的错误会被忽略**。所以关键数据必须在 `drop` 之前手动 `flush`，才能拿到可能发生的写入错误。

## 常用方法

### 构造

| 方法 | 说明 |
| --- | --- |
| `new(inner)` | 用默认容量（当前 8 KiB）包装底层写入器。 |
| `with_capacity(capacity, inner)` | 用至少指定容量的缓冲区包装底层写入器。 |

### 解包

| 方法 | 说明 |
| --- | --- |
| `into_inner()` | 先刷新再返回底层写入器，刷新失败返回错误。 |
| `into_parts()` | 拆成底层写入器与尚未写出的缓冲数据。 |

### 访问底层与缓冲

| 方法 | 说明 |
| --- | --- |
| `get_ref()` | 返回底层写入器的共享引用。 |
| `get_mut()` | 返回底层写入器的可变引用。 |
| `buffer()` | 返回缓冲区中尚未写出的数据。 |
| `capacity()` | 返回不刷新即可容纳的字节数。 |

## 示例

### 缓冲写入文件再读回

```rust
use std::fs::File;
use std::io::{BufWriter, Read, Write};

fn main() -> std::io::Result<()> {
    let mut path = std::env::temp_dir();
    path.push("rust_bufwriter_demo.txt");

    let file = File::create(&path)?;
    let mut writer = BufWriter::with_capacity(1024, file);
    writer.write_all(b"hello ")?;
    writer.write_all(b"buffered world")?;

    // 还没刷新时数据留在缓冲区里
    assert!(!writer.buffer().is_empty());
    assert!(writer.capacity() >= 1024);

    writer.flush()?;
    assert!(writer.buffer().is_empty());

    // into_inner 会再刷新一次，并把底层 File 交出来
    let file = writer.into_inner().expect("刷新缓冲失败");
    drop(file);

    let mut s = String::new();
    File::open(&path)?.read_to_string(&mut s)?;
    assert_eq!(s, "hello buffered world");

    std::fs::remove_file(&path)?;
    Ok(())
}
```

### 用 `into_parts` 抢救未写出的数据

```rust
use std::io::{self, BufWriter, Write};

struct Failing;

impl Write for Failing {
    fn write(&mut self, _buf: &[u8]) -> io::Result<usize> {
        Err(io::Error::new(io::ErrorKind::WriteZero, "磁盘已满"))
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

fn main() {
    let mut writer = BufWriter::with_capacity(8, Failing);
    writer.write_all(b"hi").unwrap();

    let (_inner, pending) = writer.into_parts();
    let pending = pending.expect("写入过程未发生 panic");
    assert_eq!(pending, b"hi");
}
```

## 常见陷阱

1. **忘记 `flush` 会丢数据**：程序在 `drop` 前异常退出时，缓冲里的内容还没到磁盘；关键写入要显式 `flush` 并处理错误。
2. **`flush` 不等于落盘**：它只保证数据交给操作系统，要真正写进磁盘还需 `File::sync_all`。
3. **`get_mut` 直接写底层会打乱顺序**：绕过缓冲写出的字节会插到缓冲区已有数据之前。
4. **`into_parts` 之后数据要自己管**：返回的 `Vec<u8>` 就是没写出去的内容，丢弃它就等于丢弃数据。
5. **对小数据量反而更慢**：只写一两次大块内容时，缓冲只是多了一次内存拷贝。

## 相关

- [[io|std::io 模块]]：IO 特质与适配器总览。
- [[io.Write|Write]]：`BufWriter` 实现的底层特质，`flush` 也来自它。
- [[io.BufReader|BufReader]]：读方向的对称包装。
- [[fs.File|File]]：最常见的 `BufWriter` 内层类型，落盘还需 `sync_all`。
- [[fs.OpenOptions|OpenOptions]]：决定文件以何种模式打开，配合 `BufWriter` 写入。
