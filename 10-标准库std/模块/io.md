---
title: "std::io"
type: std-模块
module: io
stable: "1.0.0"
unstable: false
tags:
  - std/模块
  - std/IO
aliases:
  - io
  - 输入输出
一句话: 字节流读写的基础设施：Read / Write / BufRead / Seek 特质、标准流句柄与缓冲适配器。
---

# std::io

> [!abstract] 一句话
> `std::io` 是标准库的输入输出核心：`Read` 与 `Write` 定义了「读」和「写」的最小契约，其余特质、句柄、缓冲器都围绕它们展开。

## 模块简介

`std::io` 的中心是两个特质：[[io.Read|Read]] 提供 `read` / `read_to_string` / `read_exact` 等读取方法，[[io.Write|Write]] 提供 `write` / `write_all` / `flush` 等写入方法。它们只是**字节层**的接口，不认识字符串也不认识行，所以任何实现了这两个特质的东西都能被同一段代码处理：[[fs.File|File]]、[[net.TcpStream|TcpStream]]、内存里的 `Vec<u8>`、甚至 `&[u8]`。这也是本模块文档里总是说「reader / writer」而不是「某个具体类型」的原因。

在它们之上叠了三类工具。第一类是**缓冲适配器**：[[io.BufReader|BufReader]] 给任意 reader 加一层内存缓冲，[[io.BufWriter|BufWriter]] 和 `LineWriter` 给 writer 加缓冲，显著减少系统调用。第二类是**额外特质**：[[io.BufRead|BufRead]] 在缓冲基础上提供 `read_line` / `lines` / `split`，[[io.Seek|Seek]] 让流支持移动游标，`IsTerminal` 判断句柄是不是终端。第三类是**标准流**：`io::stdin`、`io::stdout`、`io::stderr` 返回全局句柄，`lock()` 之后才能高效地连续读写。

错误处理也是本模块的一部分：所有 I/O 操作返回 `io::Result<T>`（即 `Result<T, io::Error>`），错误可以按 `ErrorKind` 分类（`NotFound`、`PermissionDenied`、`WouldBlock`…），配合 `?` 和[[11-错误处理|错误处理]]里的模式使用。

## 快速上手

```rust
use std::io::{self, BufRead, Read, Write};

fn main() -> io::Result<()> {
    // 1. 写：Vec<u8> 实现了 Write，write! 需要 Write 在作用域内
    let mut buf: Vec<u8> = Vec::new();
    write!(buf, "hello, {}\n", "io")?;

    // 2. 读：Read::read_to_string 把剩余字节读进 String
    let mut s = String::new();
    let mut slice = buf.as_slice();
    slice.read_to_string(&mut s)?;
    assert_eq!(s, "hello, io\n");

    // 3. 缓冲读：BufRead::lines 按行迭代
    let cursor = io::Cursor::new(b"a\nb\n".to_vec());
    let lines: Vec<String> = io::BufReader::new(cursor)
        .lines()
        .collect::<Result<_, _>>()?;
    assert_eq!(lines, vec!["a".to_string(), "b".to_string()]);

    // 4. io::copy：把 reader 的内容整体拷进 writer，返回字节数
    let mut src = io::Cursor::new(b"copy me".to_vec());
    let mut dst = Vec::new();
    let n = io::copy(&mut src, &mut dst)?;
    assert_eq!(n, 7);
    assert_eq!(dst, b"copy me".to_vec());

    // 5. 标准输出：lock 之后连续写入，最后 flush
    let stdout = io::stdout();
    let mut handle = stdout.lock();
    writeln!(handle, "已写入 {} 字节", n)?;
    Ok(())
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[io.Read\|Read]] | 读取字节的核心特质：`read`、`read_to_string`、`read_exact`。 |
| [[io.Write\|Write]] | 写入字节的核心特质：`write`、`write_all`、`flush`。 |
| [[io.BufRead\|BufRead]] | 带内部缓冲的 reader，提供 `read_line`、`lines`、`split`。 |
| [[io.Seek\|Seek]] | 在字节流中移动游标：`seek`、`rewind`、`stream_position`。 |
| [[io.BufReader\|BufReader]] | 为任意 reader 加缓冲，减少系统调用。 |
| [[io.BufWriter\|BufWriter]] | 缓冲写入，`flush` 或析构时落盘。 |
| `io::stdin` | 标准输入句柄，`lock()` 后配合 `read_line` 使用。 |
| `io::stdout` / `io::stderr` | 标准输出 / 标准错误句柄。 |
| `io::copy` | 把 reader 全部内容拷进 writer，返回字节数。 |
| `io::Error` | I/O 错误类型，`kind()` 返回 `ErrorKind`。 |
| `io::ErrorKind` | 错误分类枚举：`NotFound`、`PermissionDenied` 等。 |
| `io::Result` | `Result<T, io::Error>` 的类型别名。 |
| `io::SeekFrom` | 定位起点：`Start`、`End`、`Current`。 |
| `io::Cursor` | 包装内存缓冲区，同时实现 `Read` / `Write` / `Seek`。 |
| `io::repeat` / `io::empty` / `io::sink` | 无限重复字节 / 恒 EOF 读取 / 吞掉所有写入。 |

## 注意事项

> [!warning] trait 必须在作用域内
> `read`、`write`、`flush`、`read_line` 都是特质方法，调用前要 `use std::io::Read;` 等。忘了引入时报的是「method not found」，看着像方法不存在，其实是特质没导入。

> [!danger] 部分读写与 UTF-8
> `read` 和 `write` 都**不保证**处理完整个缓冲区：`write` 可能只写一部分，`read` 可能只读到几字节。要读满用 `read_exact`，要写完用 `write_all`，否则会静默丢数据。另外 `read_to_string` 要求内容是合法 UTF-8，二进制数据请读进 `Vec<u8>`。

> [!tip] 缓冲与锁
> 循环调用 `write!` 打印大量小片段时，未缓冲的 `stdout` 每次都要拿锁；先 `let out = io::stdout(); let mut h = out.lock();` 再写入，性能差别很大。文件读写用 `BufReader` + `BufWriter` 组合，并记得在作用域结束前 `flush()`——`BufWriter` 析构时虽然会尝试 flush，但错误会被吞掉。

## 相关

- [[fs|std::fs 模块]]：`File` 与文件系统操作，本模块最常见的搭档。
- [[net|std::net 模块]]：`TcpStream` 同样实现 `Read` / `Write`。
- [[string.String|String]]：文本读写的目标缓冲区。
- [[11-错误处理|错误处理]]：`io::Result` 与 `?` 的传播方式。
- [[fmt|std::fmt 模块]]：格式化输出与 `write!` 宏的底层。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 46 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [[io.BufReader|`BufReader`]]
- [[io.BufWriter|`BufWriter`]]
- [`Bytes`](https://doc.rust-lang.org/std/io/struct.Bytes.html)
- [`Chain`](https://doc.rust-lang.org/std/io/struct.Chain.html)
- [`Cursor`](https://doc.rust-lang.org/std/io/struct.Cursor.html)
- [`Empty`](https://doc.rust-lang.org/std/io/struct.Empty.html)
- [`Error`](https://doc.rust-lang.org/std/io/struct.Error.html)
- [`IntoInnerError`](https://doc.rust-lang.org/std/io/struct.IntoInnerError.html)
- [`IoSlice`](https://doc.rust-lang.org/std/io/struct.IoSlice.html)
- [`IoSliceMut`](https://doc.rust-lang.org/std/io/struct.IoSliceMut.html)
- [`LineWriter`](https://doc.rust-lang.org/std/io/struct.LineWriter.html)
- [`Lines`](https://doc.rust-lang.org/std/io/struct.Lines.html)
- [`PipeReader`](https://doc.rust-lang.org/std/io/struct.PipeReader.html)
- [`PipeWriter`](https://doc.rust-lang.org/std/io/struct.PipeWriter.html)
- [`Repeat`](https://doc.rust-lang.org/std/io/struct.Repeat.html)
- [`Sink`](https://doc.rust-lang.org/std/io/struct.Sink.html)
- [`Split`](https://doc.rust-lang.org/std/io/struct.Split.html)
- [`Stderr`](https://doc.rust-lang.org/std/io/struct.Stderr.html)
- [`StderrLock`](https://doc.rust-lang.org/std/io/struct.StderrLock.html)
- [`Stdin`](https://doc.rust-lang.org/std/io/struct.Stdin.html)
- [`StdinLock`](https://doc.rust-lang.org/std/io/struct.StdinLock.html)
- [`Stdout`](https://doc.rust-lang.org/std/io/struct.Stdout.html)
- [`StdoutLock`](https://doc.rust-lang.org/std/io/struct.StdoutLock.html)
- [`Take`](https://doc.rust-lang.org/std/io/struct.Take.html)
- [`WriterPanicked`](https://doc.rust-lang.org/std/io/struct.WriterPanicked.html)
- [`BorrowedBuf`](https://doc.rust-lang.org/std/io/struct.BorrowedBuf.html)
- [`BorrowedCursor`](https://doc.rust-lang.org/std/io/struct.BorrowedCursor.html)

### 枚举

- [`ErrorKind`](https://doc.rust-lang.org/std/io/enum.ErrorKind.html)
- [`SeekFrom`](https://doc.rust-lang.org/std/io/enum.SeekFrom.html)

### 特质

- [[io.BufRead|`BufRead`]]
- [`IsTerminal`](https://doc.rust-lang.org/std/io/trait.IsTerminal.html)
- [[io.Read|`Read`]]
- [[io.Seek|`Seek`]]
- [[io.Write|`Write`]]

### 类型别名

- [`Result`](https://doc.rust-lang.org/std/io/type.Result.html)
- [`RawOsError`](https://doc.rust-lang.org/std/io/type.RawOsError.html)

### 函数

- [[io.copy|`copy`]]
- [`empty`](https://doc.rust-lang.org/std/io/fn.empty.html)
- [`pipe`](https://doc.rust-lang.org/std/io/fn.pipe.html)
- [`read_to_string`](https://doc.rust-lang.org/std/io/fn.read_to_string.html)
- [`repeat`](https://doc.rust-lang.org/std/io/fn.repeat.html)
- [`sink`](https://doc.rust-lang.org/std/io/fn.sink.html)
- [`stderr`](https://doc.rust-lang.org/std/io/fn.stderr.html)
- [`stdin`](https://doc.rust-lang.org/std/io/fn.stdin.html)
- [`stdout`](https://doc.rust-lang.org/std/io/fn.stdout.html)

### 宏

- [`const_error`](https://doc.rust-lang.org/std/io/macro.const_error.html)

<!-- END AUTO ITEMS -->
