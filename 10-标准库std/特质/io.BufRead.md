---
title: "std::io::BufRead"
type: std-条目
kind: 特质
module: io
slug: io.BufRead
stable: "1.0.0"
tags:
  - std/特质
  - std/IO
aliases:
  - BufRead
一句话: 带内部缓冲的读取器特质，让按行读、按分隔符读成为可能。
---

# `BufRead`

> [!abstract] 一句话
> `BufRead` 是「有内部缓冲的 `Read`」：它能直接交出缓冲区里的数据，因此可以高效地按行或按分隔符切分输入。

## 简介

[[io.Read|Read]] 只关心「把字节吐给我」，但它不知道分行在哪里。要按行读，就需要一个能先把数据攒进缓冲、再在缓冲里找换行的类型，这正是 `BufRead` 的职责：`fill_buf` 借出缓冲区当前内容，`consume` 告诉它已经用掉了多少字节。

`BufRead` 是 [[io.Read|Read]] 的扩展特质（`BufRead: Read`），所以实现了 `BufRead` 的类型自动拥有全部读取方法。标准库里最常见的实现者是 [[io.BufReader|BufReader]] 和标准输入的锁 `StdinLock`。

有了它，`read_line`、`lines`、`split`、`read_until`、`skip_until` 这些按行、按分隔符的方法才有意义；直接在无缓冲的 `TcpStream` 上调用它们会退化成逐字节读。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `fill_buf()` | 返回缓冲区内容，空了就先从底层读取。 |
| `consume(amount)` | 标记缓冲区前 `amount` 个字节已被读走。 |

这两个方法成对使用：先 `fill_buf` 拿到可读数据，处理完再 `consume` 相应长度，下一轮才能看到后面的内容。

## 提供的方法

### 按分隔符读取

| 方法 | 说明 |
| --- | --- |
| `read_until(byte, buf)` | 读到分隔字节或结尾，追加进 `Vec<u8>`。 |
| `skip_until(byte)` | 跳过数据直到分隔字节或结尾。 |
| `read_line(buf)` | 读到换行（`0xA`），追加进 `String`。 |

### 迭代器

| 方法 | 说明 |
| --- | --- |
| `split(byte)` | 按分隔字节切分成迭代器，产出 `Vec<u8>`。 |
| `lines()` | 按行切分成迭代器，产出 `String`。 |

## 示例

### 按行读取内存中的文本

```rust
use std::io::{BufRead, BufReader};

fn main() -> std::io::Result<()> {
    let data = b"alpha\nbeta\ngamma";
    let reader = BufReader::new(&data[..]);

    let mut count = 0;
    for line in reader.lines() {
        let line = line?; // 每行都不含结尾的换行符
        assert!(!line.contains('\n'));
        count += 1;
    }
    assert_eq!(count, 3);
    Ok(())
}
```

### 手动用 `fill_buf` / `consume` 切分字段

```rust
use std::io::{BufRead, BufReader};

fn main() -> std::io::Result<()> {
    let mut reader = BufReader::new(&b"1,2,3"[..]);
    let mut fields: Vec<String> = Vec::new();

    loop {
        let buf = reader.fill_buf()?; // 借出缓冲区
        if buf.is_empty() {
            break; // 已到结尾
        }
        let (end, used) = match buf.iter().position(|&b| b == b',') {
            Some(i) => (i, i + 1),
            None => (buf.len(), buf.len()),
        };
        fields.push(String::from_utf8_lossy(&buf[..end]).to_string());
        reader.consume(used); // 告诉缓冲区用掉了多少字节
    }

    assert_eq!(fields, ["1", "2", "3"]);
    Ok(())
}
```

## 常见陷阱

1. **`fill_buf` 的借用未结束就 `consume`**：返回的切片借用了读取器，必须先复制或处理完数据，再调用 `consume`。
2. **`consume` 只能标记真正读走的字节**：给多了会让后面的数据被跳过，给少了会重复读取同一段内容。
3. **`read_line` 是追加而不是覆盖**：同一个 `String` 反复传入会越积越长，每次循环要新建或 `clear`。
4. **`lines` 会去掉行尾**：`\n` 与 `\r\n` 都不会出现在结果里，需要原样保留行尾就别用它。
5. **在无缓冲的流上按行读很慢**：直接对 `TcpStream` 用这些方法会逐字节触发系统调用，先套 [[io.BufReader|BufReader]]。

## 相关

- [[io|std::io 模块]]：IO 特质与适配器总览。
- [[io.Read|Read]]：`BufRead` 的父特质，提供底层字节读取。
- [[io.BufReader|BufReader]]：把任意 `Read` 变成 `BufRead` 的包装类型。
- [[io.Seek|Seek]]：在流上移动位置，与按行读配合时注意缓冲。
- [[string.String|String]]：`read_line` 与 `lines` 产出的行文本类型。
