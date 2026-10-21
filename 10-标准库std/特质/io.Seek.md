---
title: "std::io::Seek"
type: std-条目
kind: 特质
module: io
slug: io.Seek
stable: "1.0.0"
tags:
  - std/特质
  - std/IO
aliases:
  - Seek
一句话: 定义在字节流中移动读取位置的能力，是随机访问的基础。
---

# `Seek`

> [!abstract] 一句话
> `Seek` 提供一个可以前后移动的「游标」：定位之后，后续的读写就从新位置开始。

## 简介

[[io.Read|Read]] 和 [[io.Write|Write]] 是单向推进的，读一个字节就往前走一格。需要回头重读、跳到文件中间、或者从末尾往前取数据时，就要用 `Seek` 显式移动这个游标。

定位的基准由 `SeekFrom` 决定：从开头算（`Start`）、从末尾算（`End`，通常传负数）或从当前位置算（`Current`）。`seek` 返回新位置相对开头的字节偏移。

实现了 `Seek` 的典型类型是 [[fs.File|File]]、`Cursor<Vec<u8>>` 和 [[io.BufReader|BufReader]]（内层也实现 `Seek` 时）。注意网络流一般不可定位，`Seek` 不适合用在 `TcpStream` 上。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `seek(pos)` | 移动到 `SeekFrom` 指定的位置，返回新偏移。 |

## 提供的方法

| 方法 | 说明 |
| --- | --- |
| `rewind()` | 回到流开头，等价于 `seek(Start(0))`。 |
| `stream_position()` | 返回当前相对开头的偏移。 |
| `seek_relative(offset)` | 相对当前位置移动，不返回新位置。 |

## 示例

### 用 `Cursor` 在内存里定位

```rust
use std::io::{Cursor, Read, Seek, SeekFrom};

fn main() -> std::io::Result<()> {
    let mut cur = Cursor::new(b"hello world".to_vec());

    // 从末尾往回 5 字节，即第 6 个字节处
    cur.seek(SeekFrom::End(-5))?;
    assert_eq!(cur.stream_position()?, 6);

    let mut tail = String::new();
    cur.read_to_string(&mut tail)?;
    assert_eq!(tail, "world");

    // 回到开头，再相对前进 6 字节
    cur.rewind()?;
    assert_eq!(cur.stream_position()?, 0);

    cur.seek_relative(6)?;
    let mut rest = String::new();
    cur.read_to_string(&mut rest)?;
    assert_eq!(rest, "world");
    Ok(())
}
```

### 在文件里覆盖指定位置

```rust
use std::fs::OpenOptions;
use std::io::{Read, Seek, SeekFrom, Write};
use std::path::PathBuf;

fn main() -> std::io::Result<()> {
    let mut path: PathBuf = std::env::temp_dir();
    path.push("rust_seek_demo.txt");
    std::fs::write(&path, "0123456789")?;

    // 读写模式打开，定位到第 5 个字节后覆盖两个字节
    let mut f = OpenOptions::new().read(true).write(true).open(&path)?;
    f.seek(SeekFrom::Start(5))?;
    f.write_all(b"XY")?;
    assert_eq!(f.stream_position()?, 7);

    f.rewind()?;
    let mut all = String::new();
    f.read_to_string(&mut all)?;
    assert_eq!(all, "01234XY789");

    drop(f);
    std::fs::remove_file(&path)?;
    Ok(())
}
```

## 常见陷阱

1. **`SeekFrom::End` 的偏移通常是负数**：写 `End(5)` 会定位到末尾之后 5 字节，文件会被撑大。
2. **越过末尾不会报错**：`seek` 允许定位到文件长度之外，随后写入会留下空洞（用 0 填充）。
3. **`BufReader` 定位后缓冲状态会变**：包装读取器时优先用 `seek_relative`，普通 `seek` 会丢弃缓冲。
4. **`Seek` 不适用于网络流**：`TcpStream` 没有实现 `Seek`，网络数据只能顺序读。
5. **`seek` 返回的是绝对偏移**：`stream_position` 是它的便捷写法，但 `seek_relative` 不返回位置，需要自己记账。

## 相关

- [[io|std::io 模块]]：IO 特质与适配器总览。
- [[io.Read|Read]]、[[io.Write|Write]]：定位之后继续读写所用的特质。
- [[io.BufReader|BufReader]]：同样提供 `seek_relative`，可在缓冲内做廉价定位。
- [[fs.File|File]]：最常用的 `Seek` 实现者，支持随机读写。
- [[fs.OpenOptions|OpenOptions]]：示例中用读写模式打开文件后再定位覆盖。
