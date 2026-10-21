---
title: "std::net::TcpStream"
type: std-条目
kind: 结构体
module: net
slug: net.TcpStream
stable: "1.0.0"
tags:
  - std/类型
  - std/IO
aliases:
  - TcpStream
一句话: 一条已建立的 TCP 连接，可像文件一样读写字节，并带有超时与套接字选项。
---

# `TcpStream`

> [!abstract] 一句话
> `TcpStream` 表示本地与远端之间**已经建立**的 TCP 连接。它不是「配置」，而是实打实的双向字节通道：拿到它就能读、能写、能设超时。

## 简介

`TcpStream` 有两种来路：客户端用 `TcpStream::connect` 主动连出去，服务端从 [[net.TcpListener|TcpListener]] 的 `accept` 里接住一条新连接。两条路得到的都是同一个类型，用起来没有区别。

它本身不定义读写方法，而是实现了 [[io.Read|Read]] 和 [[io.Write|Write]] 两个特质，所以能直接套上 `BufReader`、`BufWriter`、`read_to_end`、`write_all` 这些现成的工具。

连接在值被 `drop` 时关闭；如果只想关掉「读」或「写」的其中一半，用 `shutdown`。TCP 协议本身就是字节流，没有消息边界——一次 `read` 拿到的可能只是半个「消息」，这是写业务协议时必须自己处理的事。

## 常用方法

### 建立连接

| 方法 | 说明 |
| --- | --- |
| `connect(addr)` | 连接到远端地址，返回可读写的流。 |
| `connect_timeout(addr, timeout)` | 带超时连接，超时即返回错误。 |

`connect` 的 `addr` 只要实现 `ToSocketAddrs`：`"127.0.0.1:8080"`、`("localhost", 8080)`、`SocketAddr` 都可以。

### 地址与句柄

| 方法 | 说明 |
| --- | --- |
| `peer_addr()` | 返回对端套接字地址。 |
| `local_addr()` | 返回本端套接字地址。 |
| `try_clone()` | 复制出独立句柄，共享同一套接字。 |
| `shutdown(how)` | 关闭读端、写端或两端。 |

`shutdown` 的参数是 `Shutdown::Read`、`Shutdown::Write`、`Shutdown::Both`。`try_clone` 不是深拷贝：两个句柄指向同一个套接字，一端 `shutdown` 会同时影响另一端。

### 超时控制

| 方法 | 说明 |
| --- | --- |
| `set_read_timeout(dur)` | 设置读超时，`None` 表示不限时。 |
| `read_timeout()` | 返回当前读超时设置。 |
| `set_write_timeout(dur)` | 设置写超时，`None` 表示不限时。 |
| `write_timeout()` | 返回当前写超时设置。 |

### 读取与套接字选项

| 方法 | 说明 |
| --- | --- |
| `peek(buf)` | 窥视数据但不出队，返回字节数。 |
| `set_nodelay(nodelay)` | 设置 `TCP_NODELAY`，关闭 Nagle 算法。 |
| `nodelay()` | 返回 `TCP_NODELAY` 当前值。 |
| `set_ttl(ttl)` | 设置 `IP_TTL` 跳数上限。 |
| `ttl()` | 返回 `IP_TTL` 当前值。 |
| `take_error()` | 取出并清空挂起的套接字错误。 |
| `set_nonblocking(nonblocking)` | 切换阻塞与非阻塞模式。 |

> [!tip] 真正的读写方法来自 `Read` / `Write`
> `TcpStream` 不提供 `read`、`write` 以外的业务方法，需要 `use std::io::{Read, Write};` 才能调用它们。

## 示例

本机回环 + 只演示 API：绑定随机端口、连上去、读一下本端/对端地址和选项，不发送数据也不等待应答，所以不会卡住。

```rust
use std::net::{Shutdown, TcpListener, TcpStream};

fn main() -> std::io::Result<()> {
    // 端口写 0，让系统分配一个空闲端口，避免占用固定端口
    let listener = TcpListener::bind("127.0.0.1:0")?;
    let addr = listener.local_addr()?;

    // 客户端连到本机回环地址
    let stream = TcpStream::connect(addr)?;
    println!("对端地址: {}", stream.peer_addr()?);
    println!("本端地址: {}", stream.local_addr()?);

    // 套接字选项：关掉 Nagle、设置 TTL
    stream.set_nodelay(true)?;
    assert_eq!(stream.nodelay()?, true);
    stream.set_ttl(64)?;
    assert_eq!(stream.ttl()?, 64);

    // 读超时以 Option<Duration> 往返
    stream.set_read_timeout(Some(std::time::Duration::from_secs(1)))?;
    assert_eq!(stream.read_timeout()?, Some(std::time::Duration::from_secs(1)));

    // 只关写端，连接的另一半仍然可用
    stream.shutdown(Shutdown::Write)?;
    Ok(())
}
```

## 常见陷阱

1. **默认没有超时**：对端不发数据时 `read` 会一直阻塞，对策是先用 `set_read_timeout` 或改用 `connect_timeout`。
2. **`write` 不保证写完**：它返回实际写入的字节数，可能小于缓冲区长度，对策是用 `write_all`。
3. **TCP 没有消息边界**：一次 `read` 可能只读到半个包，对策是自己在协议里加长度前缀或分隔符，循环读到完整为止。
4. **`try_clone` 不是复制数据流**：两个句柄共享同一个套接字，一端 `shutdown(Both)` 后另一端也读写失败。
5. **非阻塞模式要自己重试**：`set_nonblocking(true)` 后 `read` 常返回 `WouldBlock`，对策是配合事件循环或改回阻塞模式。

## 相关

- [[net|std::net 模块]]：TCP/UDP 相关类型的总入口。
- [[net.TcpListener|TcpListener]]：服务端用它监听并 `accept` 出 `TcpStream`。
- [[io.Read|Read]]、[[io.Write|Write]]：`TcpStream` 的读写能力来自这两个特质。
- [[io.BufReader|BufReader]]、[[io.BufWriter|BufWriter]]：给小包频繁读写加缓冲。
- [[21-并发编程|并发编程]]：每条连接一个线程的经典写法。
