---
title: "std::net"
type: std-模块
module: net
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - net
一句话: "同步 TCP/UDP 网络编程：IP 与套接字地址类型，以及 TcpStream/TcpListener/UdpSocket。"
---

# std::net

> [!abstract] 一句话
> `std::net` 提供**阻塞式**的 TCP 与 UDP 原语，以及 IP 地址、套接字地址这两组地址类型；它不包含异步 IO。

## 模块简介

`std::net` 里的类型可以分成两组。第一组是地址：`IpAddr`（承载 v4 或 v6 的枚举）、`Ipv4Addr`、`Ipv6Addr`、`SocketAddr`（IP + 端口）、`SocketAddrV4`、`SocketAddrV6`。地址的解析有两条路：`"127.0.0.1:8080".parse::<SocketAddr>()` 只做格式解析不会查 DNS，`ToSocketAddrs`（`"example.com:80"` 也实现了它）才会做域名解析并返回多个地址。

第二组是套接字：`TcpListener` 监听并 `accept` 连接，`TcpStream` 表示一条已建立的连接，`UdpSocket` 是无连接的收发端。`TcpStream` 实现了 [[io.Read|Read]] 与 [[io.Write|Write]]，所以读写用标准库统一的 IO 接口，也可以套 [[io.BufReader|BufReader]]、设置 `read_timeout`、切换非阻塞模式。`TcpListener::incoming` 返回 `Incoming` 迭代器，让「一直接收连接」写成 `for stream in listener.incoming()`。

关键局限：全部是**同步阻塞** API。单线程一次只能处理一个连接，`accept` 或 `read` 会把整个线程挂住。做高并发要么每连接开一个 [[thread.spawn|spawn]]，要么换成异步运行时（标准库不含 async 网络）。另外 Rust 默认尽量不让套接字被继承给子进程（Unix 用 `CLOEXEC`，Windows 用 `HANDLE_FLAG_INHERIT`），所以通过 [[process.Command|Command]] 启动的子进程不会意外拿到监听句柄。

## 快速上手

```rust
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::thread;

fn main() -> std::io::Result<()> {
    // 端口 0 表示让系统挑一个空闲端口，便于本地测试
    let listener = TcpListener::bind("127.0.0.1:0")?;
    let addr = listener.local_addr()?;
    println!("监听在 {addr}");

    // 客户端放在另一个线程，避免和服务端互相阻塞
    let client = thread::spawn(move || {
        let mut stream = TcpStream::connect(addr).unwrap();
        stream.write_all(b"ping").unwrap();
        let mut buf = [0u8; 4];
        stream.read_exact(&mut buf).unwrap();
        assert_eq!(&buf, b"pong");
    });

    // 服务端：接收连接，按长度读满 4 字节，再回写
    let (mut stream, peer) = listener.accept()?;
    println!("收到来自 {peer} 的连接");
    let mut buf = [0u8; 4];
    stream.read_exact(&mut buf)?;
    assert_eq!(&buf, b"ping");
    stream.write_all(b"pong")?;
    stream.shutdown(std::net::Shutdown::Write)?;

    client.join().unwrap();

    // 地址解析不需要联网
    let ip: std::net::IpAddr = "192.168.1.1".parse().unwrap();
    assert!(ip.is_ipv4());
    Ok(())
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[net.TcpStream\|TcpStream]] | 已连接的 TCP 流，实现 `Read`/`Write`。 |
| [[net.TcpListener\|TcpListener]] | TCP 服务端，用 `accept` 接收连接。 |
| `net::UdpSocket` | 无连接的 UDP 套接字，`send_to`/`recv_from`。 |
| `net::IpAddr` | IP 地址枚举，v4 与 v6 的统一入口。 |
| `net::Ipv4Addr` / `net::Ipv6Addr` | 具体版本的 IP 地址。 |
| `net::SocketAddr` | IP + 端口，`parse` 的目标类型。 |
| `net::SocketAddrV4` / `net::SocketAddrV6` | 具体版本的套接字地址。 |
| `net::ToSocketAddrs` | 把 `"host:port"` 解析成一组 `SocketAddr`。 |
| `net::Shutdown` | 关闭方向：`Read` / `Write` / `Both`。 |
| `net::Incoming` | `TcpListener::incoming` 的连接迭代器。 |
| `net::AddrParseError` | 地址解析失败的错误类型。 |
| `net::hostname` | 返回本机主机名。 |

## 注意事项

> [!warning] 全是阻塞 API
> `accept`、`read`、`connect` 都会阻塞当前线程。用 `thread::spawn` 给每个连接开线程是最省事的做法，但要加连接数上限；否则一个慢客户端就能占住一个线程。

> [!tip] 一定设置超时
> `set_read_timeout` / `set_write_timeout` 能避免对端不发数据时永久卡死。需要自己驱动事件循环时用 `set_nonblocking(true)`，并正确处理 `ErrorKind::WouldBlock`。

> [!danger] DNS 解析同样是阻塞的
> `ToSocketAddrs` 背后的域名解析可能耗时几百毫秒甚至更久，而且失败时你不会知道是「域名不存在」还是「网络不通」。生产代码把解析放到独立线程或带超时的链路里，不要让它在主循环里直接调用。

## 相关

- [[io|std::io]]：`Read`/`Write` 特质与标准流。
- [[thread|std::thread]]：每连接一线程的并发模型。
- [[io.BufReader|BufReader]]：包一层减少系统调用。
- [[21-并发编程|并发编程]]：线程与共享状态的配合。
- [[22-异步编程|异步编程]]：标准库没有 async 网络，如何替代。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 16 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`AddrParseError`](https://doc.rust-lang.org/std/net/struct.AddrParseError.html)
- [`Incoming`](https://doc.rust-lang.org/std/net/struct.Incoming.html)
- [`Ipv4Addr`](https://doc.rust-lang.org/std/net/struct.Ipv4Addr.html)
- [`Ipv6Addr`](https://doc.rust-lang.org/std/net/struct.Ipv6Addr.html)
- [`SocketAddrV4`](https://doc.rust-lang.org/std/net/struct.SocketAddrV4.html)
- [`SocketAddrV6`](https://doc.rust-lang.org/std/net/struct.SocketAddrV6.html)
- [[net.TcpListener|`TcpListener`]]
- [[net.TcpStream|`TcpStream`]]
- [`UdpSocket`](https://doc.rust-lang.org/std/net/struct.UdpSocket.html)
- [`IntoIncoming`](https://doc.rust-lang.org/std/net/struct.IntoIncoming.html)

### 枚举

- [`IpAddr`](https://doc.rust-lang.org/std/net/enum.IpAddr.html)
- [`Shutdown`](https://doc.rust-lang.org/std/net/enum.Shutdown.html)
- [`SocketAddr`](https://doc.rust-lang.org/std/net/enum.SocketAddr.html)
- [`Ipv6MulticastScope`](https://doc.rust-lang.org/std/net/enum.Ipv6MulticastScope.html)

### 特质

- [`ToSocketAddrs`](https://doc.rust-lang.org/std/net/trait.ToSocketAddrs.html)

### 函数

- [`hostname`](https://doc.rust-lang.org/std/net/fn.hostname.html)

<!-- END AUTO ITEMS -->
