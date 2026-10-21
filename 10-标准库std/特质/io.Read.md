---
title: "std::io::Read"
type: std-条目
kind: 特质
module: io
slug: io.Read
stable: "1.0.0"
tags:
  - std/特质
  - std/IO
aliases:
  - Read
一句话: 定义字节来源的读取契约，只需实现 read 即可获得一整套读取辅助方法。
---

# `Read`

> [!abstract] 一句话
> `Read` 是「字节来源」的统一接口：实现者只写一个 `read`，就能免费得到 `read_to_end`、`read_to_string`、`bytes`、`chain`、`take` 等一整组方法。

## 简介

所有「能往外吐字节的东西」都实现 `Read`：[[fs.File|File]]、`TcpStream`、`&[u8]`、`Cursor`、`Stdin` 等等。正因为接口统一，`BufReader`、`Take`、`Chain` 这些适配器可以套在任意读取器上，组合出读取行为。

它只有一个必须实现的方法 `read`：从源里取出若干字节填进 `&mut [u8]`，返回读到的字节数。其余方法都是基于 `read` 的默认实现，比如 `read_to_end` 会循环调用 `read` 直到 EOF。

`Read` 的语义是「**至少**尽力读一些」而不是「读满」：返回的字节数可以小于缓冲区长度。想在固定长度上拿到完整数据，要用 `read_exact`；想读到结尾，要用 `read_to_end`。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `read(buf)` | 把字节读进缓冲区，返回读到的字节数。 |

返回 `Ok(0)` 表示数据源已到结尾（EOF）；返回 `Ok(n)` 表示本次只读到了 `n` 个字节。

## 提供的方法

### 读取数据

| 方法 | 说明 |
| --- | --- |
| `read_vectored(bufs)` | 像 `read`，但依次填满多个 `IoSliceMut` 缓冲区。 |
| `read_to_end(buf)` | 读到结尾，把字节追加进 `Vec<u8>`。 |
| `read_to_string(buf)` | 读到结尾，按 UTF-8 校验后追加进 `String`。 |
| `read_exact(buf)` | 读满整个缓冲区，提前遇到 EOF 则报错。 |

### 适配器

| 方法 | 说明 |
| --- | --- |
| `by_ref()` | 借用适配器，读取时不消耗读取器本身。 |
| `bytes()` | 转成逐字节产出的迭代器。 |
| `chain(next)` | 把两个读取器首尾相接。 |
| `take(limit)` | 最多读取 `limit` 个字节。 |

## 示例

### 组合现成的读取器

```rust
use std::io::Read;

fn main() -> std::io::Result<()> {
    let head: &[u8] = b"hello ";
    let tail: &[u8] = b"world";

    // chain 把两段字节接起来，read_to_string 一次读到结尾
    let mut all = String::new();
    head.chain(tail).read_to_string(&mut all)?;
    assert_eq!(all, "hello world");

    // take 只允许读前 5 个字节
    let mut five = String::new();
    head.take(5).read_to_string(&mut five)?;
    assert_eq!(five, "hello");
    Ok(())
}
```

### 自己实现 `Read`

```rust
use std::io::{self, Read};

struct Repeat {
    byte: u8,
    left: usize,
}

impl Read for Repeat {
    fn read(&mut self, buf: &mut [u8]) -> io::Result<usize> {
        let n = buf.len().min(self.left);
        for slot in &mut buf[..n] {
            *slot = self.byte;
        }
        self.left -= n;
        Ok(n)
    }
}

fn main() -> io::Result<()> {
    let mut src = Repeat { byte: b'a', left: 5 };

    let mut out = String::new();
    src.read_to_string(&mut out)?;
    assert_eq!(out, "aaaaa");

    // 数据源已耗尽，再读返回 0 字节
    let mut buf = [0u8; 4];
    assert_eq!(src.read(&mut buf)?, 0);
    Ok(())
}
```

## 常见陷阱

1. **把短读当成错误**：`read` 返回的字节数小于缓冲区长度是正常现象，要循环读或改用 `read_exact`。
2. **`read` 返回 `Ok(0)` 是 EOF**：不要当成「暂时没有数据」继续重试，否则会死循环。
3. **`read_to_string` 对非法 UTF-8 报错**：二进制数据用 `read_to_end`，别用字符串版本。
4. **`bytes()` 每个字节都是 `Result`**：迭代时要 `?` 或 `flatten`，而且逐字节读比读缓冲区慢得多。
5. **取走所有权后无法再用读取器**：在循环里反复读取时用 `by_ref()`，只借用而不消耗。

## 相关

- [[io|std::io 模块]]：IO 特质与适配器总览。
- [[io.Write|Write]]：写方向的对称特质。
- [[io.BufRead|BufRead]]：带缓冲的行读取扩展。
- [[io.BufReader|BufReader]]：最常见的 `Read` 包装类型。
- [[io.Seek|Seek]]：在同一数据流上移动读取位置。
