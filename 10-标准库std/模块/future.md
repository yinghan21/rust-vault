---
title: "std::future"
type: std-模块
module: future
stable: "1.36.0"
unstable: false
tags:
  - std/模块
  - std/并发
aliases:
  - future
一句话: 异步计算的基础设施：Future 特质、IntoFuture，以及 ready/pending/poll_fn 三个构造器。
---

# std::future

> [!abstract] 一句话
> `std::future` 定义异步计算的通用抽象 [[future.Future|Future]]（一个可被反复 `poll` 的状态机），并提供构造现成 Future 的小工具；真正的执行器不在标准库里。

## 模块简介

`Future` 是一个**惰性**的计算：它不自己跑，而是由执行器反复调用 `poll` 推进，每次要么返回 `Poll::Ready(值)`，要么返回 `Poll::Pending` 并登记「完成时唤醒我」的 `Waker`。`async fn` / `async {}` 会被编译器改写成实现了 `Future` 的状态机，`.await` 则是在状态机内部嵌套地 `poll` 子 Future。

模块本身很小，只有三类东西。第一是特质：`Future`（关联类型 `Output` + 方法 `poll`）和 `IntoFuture`（让自定义类型也能出现在 `.await` 右边）。第二是三个构造器：`ready(v)` 立刻完成、`pending()` 永不完成、`poll_fn(f)` 把闭包变成 Future——写组合器、写测试时特别好用。第三是 `join!`、`AsyncDrop` 等少量仍在 nightly 上的接口。

标准库**没有执行器**。`Future` 只有在被轮询时才前进，而「谁来轮询、`Pending` 时怎么挂起线程」是运行时（tokio、async-std、smol）的职责。标准库只提供到 [[pin|std::pin]] 和 [[task|std::task]] 为止的底层零件，这让生态可以自选调度策略，代价是新手需要自己引入一个运行时。

日常写业务代码时你很少直接碰这个模块：`async fn` 和 `.await` 已经够用。但写库、写手动 `Future` 实现、或想理解 `&mut` 为什么在 `async` 里会打架时，必须回到 `poll` 和 `Pin` 这一层。

## 快速上手

```rust
use std::future::Future;
use std::pin::Pin;
use std::sync::Arc;
use std::task::{Context, Poll, Wake, Waker};

// 最小 Waker：收到唤醒通知什么也不做
struct NoopWaker;

impl Wake for NoopWaker {
    fn wake(self: Arc<Self>) {}
}

// 手写 Future：立刻返回 42
struct Ready42;

impl Future for Ready42 {
    type Output = i32;

    fn poll(self: Pin<&mut Self>, _cx: &mut Context<'_>) -> Poll<i32> {
        Poll::Ready(42)
    }
}

// 一个真的会 Pending 的 Future：每次 poll 减一
struct Countdown {
    left: u32,
}

impl Future for Countdown {
    type Output = &'static str;

    fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<&'static str> {
        if self.left == 0 {
            Poll::Ready("发射")
        } else {
            self.left -= 1;
            cx.waker().wake_by_ref(); // 通知执行器稍后再轮询我
            Poll::Pending
        }
    }
}

// 极简执行器：轮询到 Ready 为止
fn block_on<F: Future>(fut: F) -> F::Output {
    let waker = Waker::from(Arc::new(NoopWaker));
    let mut cx = Context::from_waker(&waker);
    let mut fut = Box::pin(fut); // Future 默认 !Unpin，先钉住
    loop {
        match fut.as_mut().poll(&mut cx) {
            Poll::Ready(v) => return v,
            // 真实执行器会在这里把线程挂起，等 Waker 唤醒
            Poll::Pending => continue,
        }
    }
}

fn main() {
    assert_eq!(block_on(Ready42), 42);
    assert_eq!(block_on(Countdown { left: 3 }), "发射");

    // 标准库提供的现成 Future
    assert_eq!(block_on(std::future::ready(7)), 7);

    // 闭包也能变成 Future
    let mut n = 0;
    let fut = std::future::poll_fn(move |_cx| {
        n += 1;
        if n < 3 { Poll::Pending } else { Poll::Ready(n) }
    });
    assert_eq!(block_on(fut), 3);
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[future.Future\|Future]] | 异步计算的核心特质，唯一必需方法是 `poll`。 |
| `Future::Output` | 关联类型，`Poll::Ready` 时产出的值。 |
| `Future::poll` | 由执行器调用，推进状态机。 |
| `IntoFuture` | 让自定义类型也能放在 `.await` 右边。 |
| `future::ready` | 创建立刻完成的 Future。 |
| `future::pending` | 创建永不完成的 Future，可当占位或类型推断锚点。 |
| `future::poll_fn` | 把 `FnMut(&mut Context) -> Poll<T>` 闭包包装成 Future。 |
| `Ready<T>` / `Pending<T>` | `ready` / `pending` 返回的具体类型。 |
| `PollFn<F>` | `poll_fn` 返回的具体类型。 |
| `future::join!` | 同时轮询多个 Future，全部完成时返回元组（不稳定，仅 nightly）。 |
| `AsyncDrop` / `async_drop_in_place` | 异步析构支持（不稳定，仅 nightly）。 |

## 注意事项

> [!warning] Future 是惰性的，创建不等于执行
> `let f = async { println!("跑了"); };` 什么都不会打印，直到有人 `poll` 它。常见错误是 `async_fn();` 丢掉返回值——如果那个返回值是 `#[must_use]` 的 Future，编译器会警告；手上没有运行时的话，用 `block_on` 或运行时提供的 `spawn` 才真正执行。

> [!danger] `Future` 默认 `!Unpin`，要用 `Pin`
> `async` 块生成的状态机可能自引用（跨 `.await` 持有 `&mut` 时），所以不能随便移动。手工 `poll` 前要先 `Box::pin(fut)` 或 `pin!` 钉在内存里；把 Future 直接放进 `Vec` 再取出后 `poll` 会编译不过。这也是「`&mut` 引用不能跨 `.await` 长期持有」这类报错的根源。

> [!tip] 别在 `async` 里做阻塞
> [[thread.sleep|sleep]]、`std::fs` 的同步读写、CPU 密集循环都会卡住执行器所在线程，让同一线程上的其他任务全部停摆。阻塞操作请放进专用线程池，或改用运行时的异步 IO 接口。

## 相关

- [[pin|std::pin]]：`Pin` 与 `!Unpin`，手工轮询的前提。
- [[task|std::task]]：`Context`、`Poll`、`Waker` 所在模块。
- [[22-异步编程|异步编程]]：`async`/`.await`、执行器与常见陷阱的系统笔记。
- [[marker.Send|Send]]：`spawn` 要求 Future 是 `Send`。
- [[thread|std::thread]]：`Future` 之前的那套并发模型，可作对照。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 11 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`Pending`](https://doc.rust-lang.org/std/future/struct.Pending.html)
- [`PollFn`](https://doc.rust-lang.org/std/future/struct.PollFn.html)
- [`Ready`](https://doc.rust-lang.org/std/future/struct.Ready.html)

### 特质

- [[future.Future|`Future`]]
- [`IntoFuture`](https://doc.rust-lang.org/std/future/trait.IntoFuture.html)
- [`AsyncDrop`](https://doc.rust-lang.org/std/future/trait.AsyncDrop.html)

### 函数

- [`pending`](https://doc.rust-lang.org/std/future/fn.pending.html)
- [`poll_fn`](https://doc.rust-lang.org/std/future/fn.poll_fn.html)
- [`ready`](https://doc.rust-lang.org/std/future/fn.ready.html)
- [`async_drop_in_place`](https://doc.rust-lang.org/std/future/fn.async_drop_in_place.html)

### 宏

- [`join`](https://doc.rust-lang.org/std/future/macro.join.html)

<!-- END AUTO ITEMS -->
