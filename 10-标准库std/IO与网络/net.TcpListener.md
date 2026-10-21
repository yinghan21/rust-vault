---
title: "std::net::TcpListener"
type: std-条目
kind: 结构体
module: net
slug: net.TcpListener
stable: "1.0.0"
tags:
  - std/类型
  - std/IO
aliases:
  - TcpListener
一句话: 监听某个本地地址上的 TCP 连接，用 accept 或 incoming 把连接一条条接进来。
---

# `TcpListener`

> [!abstract] 一句话
> `TcpListener` 是 TCP 的**服务端入口**：先 `bind` 到本地地址开始监听，再用 `accept`（或 `incoming` 迭代器）接住进来的每一条连接，得到 [[net.TcpStream|TcpStream]]。

## 简介

`TcpListener::bind` 干两件事：占用本地地址端口、把套接字切到监听状态。端口写 `0` 表示「随便挑一个空闲端口」，绑定后可以用 `local_addr()` 问出实际端口，这对测试和多实例部署很有用。

接连接有两种写法：`accept` 一次返回 `(TcpStream, SocketAddr)`；`incoming()` 返回一个迭代器，`for stream in listener.incoming()` 就是最朴素的「串行处理每个连接」。两者本质上都是调 `accept`，区别只是写法。

监听套接字在值被 `drop` 时关闭。`TcpListener` 是可共享的：`accept` 只借 `&self`，所以配合 [[sync.Arc|Arc]] 就能让多个线程共用同一个监听器。

## 常用方法

### 绑定与地址

| 方法 | 说明 |
| --- | --- |
| `bind(addr)` | 绑定地址并开始监听，返回监听器。 |
| `local_addr()` | 返回本端监听的套接字地址。 |
| `try_clone()` | 复制出独立句柄，共享同一监听套接字。 |

### 接收连接

| 方法 | 说明 |
| --- | --- |
| `accept()` | 阻塞等待新连接，返回流与对端地址。 |
| `incoming()` | 返回按顺序产出连接结果的迭代器。 |

`accept` 的返回类型是 `io::Result<(TcpStream, SocketAddr)>`，`incoming` 的每一项是 `io::Result<TcpStream>`——单个连接出错不会终止监听，所以迭代器里仍然要 `?` 或 `match`。

### 套接字选项

| 方法 | 说明 |
| --- | --- |
| `set_ttl(ttl)` | 设置 `IP_TTL` 跳数上限。 |
| `ttl()` | 返回 `IP_TTL` 当前值。 |
| `set_only_v6(only_v6)` | 设置是否只接收 IPv6 连接。 |
| `only_v6()` | 返回是否只接收 IPv6 连接。 |
| `take_error()` | 取出并清空挂起的套接字错误。 |
| `set_nonblocking(nonblocking)` | 切换阻塞与非阻塞模式。 |

> [!tip] 想同时监听 IPv4 和 IPv6
> `bind("0.0.0.0:8080")` 只覆盖 IPv4，`bind("[::]:8080")` 在多数系统上能同时接受两者，具体行为取决于 `IPV6_V6ONLY`，可用 `only_v6` 查看。

## 示例

本机回环 + 只演示 API：绑定随机端口、开成非阻塞，`accept` 立刻返回而不会真的等待。

```rust
use std::io::ErrorKind;
use std::net::TcpListener;

fn main() -> std::io::Result<()> {
    // 端口 0：由系统挑一个空闲端口
    let listener = TcpListener::bind("127.0.0.1:0")?;
    println!("监听地址: {}", listener.local_addr()?);
    println!("TTL: {}", listener.ttl()?);

    // 非阻塞模式下没有连接会立刻返回 WouldBlock，不会卡住
    listener.set_nonblocking(true)?;
    match listener.accept() {
        Ok((stream, peer)) => println!("收到来自 {peer} 的连接: {stream:?}"),
        Err(e) if e.kind() == ErrorKind::WouldBlock => println!("暂无连接（非阻塞立即返回）"),
        Err(e) => return Err(e),
    }

    // incoming 只是 accept 的迭代器包装
    for conn in listener.incoming() {
        match conn {
            Ok(stream) => println!("新连接: {:?}", stream.peer_addr()?),
            Err(_) => break,
        }
        break;
    }
    Ok(())
}
```

## 常见陷阱

1. **固定端口可能绑定失败**：端口被占用会返回 `AddrInUse`，对策是测试里统一用端口 `0`，再从 `local_addr` 读实际端口。
2. **`accept` 默认一直阻塞**：单线程里 `accept` 卡住就干不了别的事，对策是每连接开一个线程，或改用非阻塞 + 事件循环。
3. **迭代器会吞掉单次错误**：`incoming()` 的 `Err` 若被忽略就会一直空转，对策是显式判断后 `break` 或记录日志。
4. **监听器被 drop 就关闭**：把 `TcpListener` 移进线程后主线程拿不到它，对策是 `try_clone` 或 `Arc` 共享。
5. **`bind` 成功不等于端口立刻可用**：加入监听队列需要内核时间，短命测试里连续占用同一端口建议加随机化。

## 相关

- [[net|std::net 模块]]：`SocketAddr`、`Shutdown`、`Incoming` 都在这里。
- [[net.TcpStream|TcpStream]]：`accept` 产出的连接，真正读写数据的地方。
- [[io.Read|Read]]、[[io.Write|Write]]：对 `TcpStream` 读写要用这两个特质。
- [[sync.Arc|Arc]]：多线程共享同一个监听器时套一层 `Arc`。
- [[21-并发编程|并发编程]]：服务端「一连接一线程」的完整写法。
