---
title: "std::io::Write"
type: std-条目
kind: 特质
module: io
slug: io.Write
stable: "1.0.0"
tags:
  - std/特质
  - std/IO
aliases:
  - Write
一句话: 定义字节去向的写入契约，必须实现 write 与 flush。
---

# `Write`

> [!abstract] 一句话
> `Write` 是「字节去向」的统一接口：文件、网络流、内存缓冲都实现它，因此 `write_all`、`write!` 这类工具对所有目标通用。

## 简介

和 [[io.Read|Read]] 对称，`Write` 描述一个可以接收字节的对象。标准库里的实现者包括 [[fs.File|File]]、`TcpStream`、`Vec<u8>`、`Stdout`、`BufWriter` 等；`std::io` 中的写适配器也都在这个特质上工作。

它有两个必须实现的方法：`write` 负责把缓冲区里的字节送出去并返回写出的字节数，`flush` 负责把中间层缓存的内容推到最终目的地。其余方法都是默认实现。

`write` 的语义同样是「**尽力**写一部分」：返回的字节数可能小于输入长度，甚至可能为 0。需要保证整段写完时用 `write_all`；要格式化输出时用 `write!` 宏，它底层就调用 `write_fmt`。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `write(buf)` | 写入缓冲区，返回本次写出的字节数。 |
| `flush()` | 刷新输出流，让缓存内容抵达目的地。 |

## 提供的方法

### 写入数据

| 方法 | 说明 |
| --- | --- |
| `write_vectored(bufs)` | 像 `write`，但依次写出多个 `IoSlice` 缓冲区。 |
| `write_all(buf)` | 反复调用 `write`，直到整个缓冲区写完。 |
| `write_fmt(args)` | 写入格式化后的字符串，`write!` 宏的底层实现。 |

### 适配器

| 方法 | 说明 |
| --- | --- |
| `by_ref()` | 借用适配器，写入时不消耗写入器本身。 |

## 示例

### 用 `write_all` 与 `write!` 写进内存

```rust
use std::io::{self, Write};

fn main() -> io::Result<()> {
    // Vec<u8> 实现了 Write，适合当作测试用的目的地
    let mut buf: Vec<u8> = Vec::new();

    buf.write_all(b"answer = ")?;
    write!(buf, "{}", 42)?;
    assert_eq!(buf, b"answer = 42");

    // by_ref 只借用，写完之后 buf 还能继续用
    buf.by_ref().write_all(b"!")?;
    assert_eq!(buf, b"answer = 42!");
    Ok(())
}
```

### 自己实现 `Write`

```rust
use std::io::{self, Write};

struct Counter {
    bytes: usize,
}

impl Write for Counter {
    fn write(&mut self, buf: &[u8]) -> io::Result<usize> {
        self.bytes += buf.len();
        Ok(buf.len())
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

fn main() -> io::Result<()> {
    let mut counter = Counter { bytes: 0 };
    counter.write_all(b"hello")?;
    counter.write_all(b" world")?;
    assert_eq!(counter.bytes, 11);

    // write! 通过 write_fmt 走的还是同一个 write 实现
    write!(counter, "!")?;
    assert_eq!(counter.bytes, 12);
    Ok(())
}
```

## 常见陷阱

1. **`write` 可能只写一部分**：手动循环 `write` 时必须用返回的字节数推进偏移，否则会重复写或漏写。
2. **忘记 `flush`**：`BufWriter`、`Stdout` 会缓存数据，不刷新就可能丢内容，而且 `flush` 的错误要显式处理。
3. **`flush` 不保证落盘**：它只把数据交给操作系统，真正写进磁盘还需 `File::sync_all`。
4. **`write!` 需要特质在作用域内**：只 `use std::io;` 而没引入 `Write` 时，宏展开找不到 `write_fmt`。
5. **混用 `fmt::Write` 会歧义**：两个 `Write` 同名，同时引入时要么写全路径，要么只引入其中一个。

## 相关

- [[io|std::io 模块]]：IO 特质与适配器总览。
- [[io.Read|Read]]：读方向的对称特质。
- [[io.BufWriter|BufWriter]]：最常见的 `Write` 包装类型，记得手动刷新。
- [[io.BufRead|BufRead]]：读侧带缓冲的特质。
- [[fmt|std::fmt 模块]]：`write_fmt` 接收的 `Arguments` 来自格式化系统。
