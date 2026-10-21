---
title: "std::io::copy"
type: std-条目
kind: 函数
module: io
slug: io.copy
stable: "1.0.0"
tags:
  - std/IO
aliases:
  - copy
一句话: "把 reader 的全部内容流式搬到 writer，直到 reader 读到 EOF，返回复制的字节数。"
---

# `copy`

> [!abstract] 一句话
> `std::io::copy(&mut reader, &mut writer)` 反复从 `reader` 读、往 `writer` 写，直到 `reader` 返回 EOF；成功时返回**总共复制了多少字节**（`u64`）。

## 简介

读写之间搬数据本来要自己写循环：`read` 到一块缓冲区、`write_all` 出去、处理 `Ok(0)` 和 `Interrupted`。`io::copy` 把这些都包好了，一行就能完成「把一个流整体倒进另一个流」：文件拷进内存、内存写进 `TcpStream`、一个 `Cursor` 灌进另一个 `Cursor`。

它只认特质，不认具体类型：第一个参数要 `Read`，第二个要 `Write`，所以 `File`、`&[u8]`、[[io.BufReader|BufReader]]、`Cursor<Vec<u8>>`、`TcpStream` 这些都能直接传（用 `&mut`）。内部按块搬运、自带缓冲区，不套 [[io.BufReader|BufReader]] / [[io.BufWriter|BufWriter]] 也不会退化成逐字节读写。

要在**两个文件路径**之间复制，应该用 `std::fs::copy`（会复制权限、自动截断目标）；`io::copy` 面向的是「已经打开的流」，不处理路径，也不负责截断或刷新——`writer` 的缓冲由它自己的类型决定，`BufWriter` 还需要你手动 `flush` 或让它 `drop`。

它没有 `unsafe`、不会 panic，出错一律走 `io::Result`。`Ok(n)` 里的 `n` 是 `u64`，因为文件可以比一台机器能寻址的内存还大；转成 `usize` 时记得 `as usize` 或 `try_into`。

## 签名与参数

```text
pub fn copy<R, W>(reader: &mut R, writer: &mut W) -> io::Result<u64>
where
    R: Read + ?Sized,
    W: Write + ?Sized,
```

| 参数 | 说明 |
| --- | --- |
| `reader` | 任何实现了 `Read` 的可变引用，如 `File`、`&[u8]`、`Cursor`、`TcpStream`。 |
| `writer` | 任何实现了 `Write` 的可变引用，如 `Vec<u8>`、`File`、`Cursor`、`TcpStream`。 |
| 返回 `Ok(n)` | 成功复制并写出的总字节数为 `n`（`u64`）。 |
| 返回 `Err(io::Error)` | 读或写过程中出错，如磁盘满、连接断开、权限不足。 |

| 需求 | 用什么 |
| --- | --- |
| 流到流，内容整体搬运 | `io::copy(&mut reader, &mut writer)` |
| 路径到路径 | `fs::copy(src, dst)`，不要先 `File::open` 再 `io::copy` |
| 复制到内存 | 让 `writer` 是 `Vec<u8>`，或先读成 `String`（文本） |
| 只复制前 N 个字节 | `reader.take(n)` 后再 `io::copy` |
| 需要进度或可中断 | 自己写 `read` / `write_all` 循环，`io::copy` 不暴露进度 |

## 示例

### 文件复制到 `Vec<u8>`

```rust
use std::fs;
use std::io;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let path = "demo_io_copy.txt";
    fs::write(path, "第一行\n第二行\n")?;

    // File 实现 Read，Vec<u8> 实现 Write
    let mut file = fs::File::open(path)?;
    let mut buf = Vec::new();
    let n = io::copy(&mut file, &mut buf)?;

    // 返回值就是复制出的字节数，和缓冲区长度一致
    assert_eq!(n as usize, buf.len());
    assert_eq!(String::from_utf8(buf)?, "第一行\n第二行\n");

    fs::remove_file(path)?;
    println!("复制了 {} 个字节", n);
    Ok(())
}
```

### `Cursor` 到 `Cursor`

```rust
use std::io::{self, Cursor};

fn main() -> io::Result<()> {
    let mut src = Cursor::new(b"hello".to_vec());
    let mut dst = Cursor::new(Vec::new());

    let n = io::copy(&mut src, &mut dst)?;
    assert_eq!(n, 5);

    // 源已经读到末尾，目标里是完整内容
    assert_eq!(src.position(), 5);
    assert_eq!(dst.into_inner(), b"hello");
    Ok(())
}
```

## 常见陷阱

1. **目标文件不会自动截断**：`io::copy` 从 `writer` 的当前位置开始写，不缩短文件。用 `File::open` 打开已存在的长文件再复制，旧内容的尾部会残留；要覆盖就先 `File::create`（会截断），或用 `fs::copy`。
2. **以为它会顺手 `flush`**：写到 `BufWriter` 的数据还在缓冲里，复制完要 `flush()`（或让 `BufWriter` 离开作用域）才算真正交给下层。
3. **复制完还想复用 `reader`**：此时它已在 EOF，继续读只会拿到 `Ok(0)`；要重来就 `seek(SeekFrom::Start(0))` 或重新打开。
4. **目标写内存**：`writer` 是 `Vec<u8>` 时整个内容都留在内存里，几个 GB 的文件要改成直接写 `File`，让数据流过去。
5. **错误后已写部分不会回滚**：中途返回 `Err` 时，之前写出的字节还在 `writer` 里，需要重试就得自己记录进度并做幂等处理。
6. **把路径复制写成这个函数**：`io::copy` 不处理路径、权限和元数据；路径对路径用 `fs::copy` 更省事也更快。

## 相关

- [[io|std::io 模块]]：本条目所属模块，`Read`、`Write` 与各种流都在这里。
- [[io.Read|Read]]：第一个参数要实现的特质，提供 `read` 与 `read_to_end`。
- [[io.Write|Write]]：第二个参数要实现的特质，提供 `write` 与 `write_all`。
- [[io.BufReader|BufReader]]：从同一流大量小块读时套一层，减少系统调用。
- [[io.BufWriter|BufWriter]]：目标方向的小块写缓冲，记得 `flush`。
- [[fs.File|File]]：常见的两端类型，`open` 读、`create` 写。
- [[fs.read_to_string|read_to_string]]：只想把文本整体读成 `String` 时的捷径。
- [[11-错误处理|错误处理]]：`io::Result` 与 `?` 的标准处理方式。
