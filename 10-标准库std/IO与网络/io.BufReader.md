---
title: "std::io::BufReader"
type: std-条目
kind: 结构体
module: io
slug: io.BufReader
stable: "1.0.0"
tags:
  - std/类型
  - std/IO
aliases:
  - BufReader
一句话: 给任意读取器加一层内存缓冲，把大量小块读合并成少数几次底层读取。
---

# `BufReader`

> [!abstract] 一句话
> `BufReader<R>` 在底层读取器之上维护一块内存缓冲区：一次向底层要一大块，之后的小读都从缓冲区里取。

## 简介

直接对 `TcpStream` 或 [[fs.File|File]] 调用 `read`，每次都是一次系统调用；循环里逐行、逐字节读时开销会被放大几十倍。`BufReader<R>` 的做法是先向底层读取器要一大块数据放进内存缓冲，后续的小读直接命中缓冲，只有缓冲耗尽时才再向底层要一次。

它只对**小而频繁**的读有用。一次就把整个文件读进来、或者对一个已经在内存里的 `Vec<u8>` 读取时，加缓冲没有收益。

因为 `BufReader` 自己持有一块预先读出的数据，丢掉包装会一起丢掉缓冲里还没被读走的内容：用 `into_inner` 取回底层读取器后再读、或在同一个流上套多个 `BufReader`，都可能导致数据丢失。

## 常用方法

### 构造

| 方法 | 说明 |
| --- | --- |
| `new(inner)` | 用默认容量（当前 8 KiB）包装底层读取器。 |
| `with_capacity(capacity, inner)` | 用指定大小的缓冲区包装底层读取器。 |

### 访问底层

| 方法 | 说明 |
| --- | --- |
| `get_ref()` | 返回底层读取器的共享引用。 |
| `get_mut()` | 返回底层读取器的可变引用。 |
| `into_inner()` | 解包，取出底层读取器（丢弃缓冲）。 |

### 缓冲与定位

| 方法 | 说明 |
| --- | --- |
| `buffer()` | 返回缓冲区中已读取但尚未消费的数据。 |
| `capacity()` | 返回缓冲区一次能容纳的字节数。 |
| `seek_relative(offset)` | 相对当前位置定位，位置在缓冲内时不刷新缓冲。 |

## 示例

### 逐行读取文件

```rust
use std::fs::File;
use std::io::{BufRead, BufReader, Read};

fn main() -> std::io::Result<()> {
    let mut path = std::env::temp_dir();
    path.push("rust_bufreader_demo.txt");
    std::fs::write(&path, "第一行\n第二行\n")?;

    let file = File::open(&path)?;
    let mut reader = BufReader::with_capacity(64, file);
    assert_eq!(reader.capacity(), 64);

    let mut line = String::new();
    let n = reader.read_line(&mut line)?;
    assert_eq!(line, "第一行\n");
    assert!(n > 0);

    // 整个文件都在缓冲里，所以剩余内容可以直接从缓冲看到
    assert!(!reader.buffer().is_empty());

    let mut rest = String::new();
    reader.read_to_string(&mut rest)?;
    assert_eq!(rest, "第二行\n");

    // 取回底层 File 前缓冲里的数据已读完，不会丢数据
    let file = reader.into_inner();
    drop(file);

    std::fs::remove_file(&path)?;
    Ok(())
}
```

### 在缓冲内做相对定位

```rust
use std::fs::File;
use std::io::{BufReader, Read};

fn main() -> std::io::Result<()> {
    let mut path = std::env::temp_dir();
    path.push("rust_bufreader_seek.txt");
    std::fs::write(&path, "abcdef")?;

    let mut reader = BufReader::with_capacity(16, File::open(&path)?);

    let mut head = [0u8; 3];
    reader.read_exact(&mut head)?;
    assert_eq!(&head, b"abc");

    // 相对当前位置前进 2 字节，命中缓冲时不触发底层 seek
    reader.seek_relative(2)?;

    let mut rest = String::new();
    reader.read_to_string(&mut rest)?;
    assert_eq!(rest, "f");

    drop(reader);
    std::fs::remove_file(&path)?;
    Ok(())
}
```

## 常见陷阱

1. **`into_inner` 会丢掉未读的缓冲**：缓冲里可能还躺着已从底层读出、但没交给你的数据，取回底层读取器前先读干净。
2. **同一个流套多个 `BufReader` 会丢数据**：每个包装各持一块缓冲，交叉读取时游标与数据都会错位。
3. **对大块一次性读取没有收益**：`read_to_end` 一次读几十 MB 时，缓冲只是多拷贝一次。
4. **`get_mut` 绕过缓冲读取会让缓冲区失效**：直接操作底层读取器后，缓冲里的旧数据与底层位置已不一致。
5. **`seek_relative` 不返回新位置**：需要位置时自己记账，或改用 `Seek::stream_position`。

## 相关

- [[io|std::io 模块]]：IO 特质与适配器总览。
- [[io.Read|Read]]：`BufReader` 实现的底层特质。
- [[io.BufRead|BufRead]]：`BufReader` 实现的行读取特质，提供 `read_line` 与 `lines`。
- [[io.BufWriter|BufWriter]]：写方向的对称包装。
- [[io.Seek|Seek]]：`seek_relative` 所属的定位特质。
- [[fs.File|File]]：最常见的 `BufReader` 内层类型，配合它做逐行读取。
