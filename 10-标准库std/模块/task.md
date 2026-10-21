---
title: "std::task"
type: std-模块
module: task
stable: "1.36.0"
unstable: false
tags:
  - std/模块
aliases:
  - task
  - 异步任务模块
一句话: 异步任务的底层接口：Poll 表示「还没好/好了」，Context 与 Waker 让执行器在就绪时重新调度任务。
---

# std::task

> [!abstract] 一句话
> `std::task` 是 `async/.await` 之下的那层机关：[[future.Future|Future]] 的 `poll` 方法接收 `Context`、返回 `Poll<T>`，而 `Context` 里揣着的 `Waker` 是任务把「我准备好了」通知给执行器的唯一通道。

## 模块简介

一个 `async fn` 编译后就是一个实现了 [[future.Future|Future]] 的状态机，而 `Future` 的全部接口只有一句：`poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output>`。执行器（executor）反复调用 `poll`，每次都可能得到两种结果——`Poll::Ready(v)` 表示算完了，`Poll::Pending` 表示「卡住了，等会儿再来问」。`Poll<T>` 就是这个二选一的枚举，`Ready` 带值、`Pending` 不带。所以 `std::task` 定义的不是「怎么写异步函数」，而是「执行器和 Future 之间怎么对话」。

对话的另一半是唤醒。返回 `Pending` 之后执行器不会原地空转，而是转去跑别的任务；等某个事件（socket 可读、定时器到期、另一个任务发来消息）发生时，需要有人把「这个任务可以再 poll 一次」的消息送回去，靠的就是 `Waker`。`Future` 在返回 `Pending` 之前应该把 `cx.waker()` 克隆一份存好，事件就绪时调用 `wake()`；执行器则在自己的 `Waker` 实现里把任务重新塞进就绪队列。`Context` 因此只是个「装着 waker 的信封」，`Context::waker()` 取它，`Context::from_waker` 造一个——后者在自己手写 poll 循环或写测试时特别有用。

手写 `Future` 时 `Pin` 是绕不开的：异步状态机内部可能自引用（一个 `await` 之后的局部变量借用了之前的局部变量），一旦被移走，那些指针就悬空了。所以 `poll` 的 `self` 是 `Pin<&mut Self>`，约定「实现方不得移动内部数据」，`Box::pin` 则把值固定在堆上。日常写 `async fn` 不用操心这些，编译器生成的状态机已经处理好，这也是 [[pin|std::pin]] 存在的原因。

模块里其余类型是给**执行器作者**用的：`RawWaker` / `RawWakerVTable` 是手工构造 `Waker` 的底层表示（全 `unsafe`，手写运行时才用），`Wake` 是把任意 `Arc<W>` 变成 `Waker` 的便捷特质。普通业务代码几乎只会碰到 `Poll`、`Context`、`Waker` 这三个名字。

## 快速上手

```rust
use std::future::Future;
use std::pin::Pin;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::task::{Context, Poll, Wake, Waker};

// 执行器一侧：被唤醒时把标志位立起来
struct Flag(AtomicBool);

impl Wake for Flag {
    fn wake(self: Arc<Self>) {
        self.0.store(true, Ordering::SeqCst);
    }
}

// 手写一个 Future：倒数到 0 才返回 Ready
struct Countdown {
    remaining: u32,
    last_waker: Option<Waker>,
}

impl Future for Countdown {
    type Output = &'static str;

    fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        if self.remaining == 0 {
            return Poll::Ready("完成");
        }
        self.remaining -= 1;
        // 这次没好：把 waker 存下来，等条件满足后再调用它
        self.last_waker = Some(cx.waker().clone());
        Poll::Pending
    }
}

fn main() {
    let flag = Arc::new(Flag(AtomicBool::new(false)));
    let waker: Waker = Waker::from(Arc::clone(&flag));
    let mut cx = Context::from_waker(&waker);

    // Box::pin 把值固定在堆上，才能得到 Pin<&mut Self>
    let mut fut = Box::pin(Countdown { remaining: 2, last_waker: None });

    // 手动轮询：前两次 Pending，第三次 Ready
    for _ in 0..2 {
        match fut.as_mut().poll(&mut cx) {
            Poll::Pending => {}
            Poll::Ready(_) => panic!("还不该完成"),
        }
    }
    assert!(fut.last_waker.is_some()); // Pending 时存下了 waker

    match fut.as_mut().poll(&mut cx) {
        Poll::Ready(v) => assert_eq!(v, "完成"),
        Poll::Pending => panic!("应该已经完成"),
    }

    // 事件就绪时唤醒任务，执行器据此重新入队
    waker.wake_by_ref();
    assert!(flag.0.load(Ordering::SeqCst));

    println!("轮询结束");
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| `task::Poll` | `Ready(T)` 或 `Pending`，`poll` 的返回值。 |
| `task::Context` | 任务上下文，主要用 `waker()` 取唤醒句柄。 |
| `task::Waker` | 唤醒句柄，`wake` / `wake_by_ref` 通知执行器。 |
| `task::Wake` | 实现唤醒逻辑的特质，配合 `Waker::from` 使用。 |
| `task::RawWaker` | 手工构造 `Waker` 的低层表示（`unsafe`）。 |
| `task::RawWakerVTable` | `RawWaker` 的函数指针表，定义克隆/唤醒/释放。 |
| `Waker::wake` | 消耗自身并唤醒任务。 |
| `Waker::wake_by_ref` | 借用唤醒，句柄仍可继续用。 |
| `Context::waker` | 取出当前任务的 `Waker`。 |
| `Context::from_waker` | 由现成 `Waker` 构造 `Context`，手写轮询时用。 |
| `Waker::from` | 由 `Arc<W>`（`W: Wake`）构造 `Waker`。 |
| [[future.Future\|Future]] | `poll` 的定义者，`async` 块的背后类型。 |

## 注意事项

> [!warning] `Pending` 之后必须能被唤醒
> 如果 `poll` 返回 `Pending` 却没存下 waker、也没安排任何唤醒，任务就永远挂在那里——不会报错，也不会 panic，只是「不动了」。手写 `Future` 的第一原则：**每次返回 `Pending` 前，确认唤醒路径已经存在**。

> [!danger] `Pin` 不是装饰品
> `Pin<&mut Self>` 承诺内部数据不会被移动。用 `unsafe` 的 `get_unchecked_mut` 绕过它、或在 poll 里把 `self` 移出去，都会破坏自引用状态机的前提，属于未定义行为。日常写 `async fn` 由编译器生成状态机，不要手写 `unsafe` 移动。

> [!tip] 执行器不在标准库
> `std::task` 只有「协议」，没有「运行时」：标准库不提供把 `Future` 跑起来的执行器，也不提供 `spawn` 函数。单线程简单场景可以像上面那样手写 poll 循环；真实项目用 `tokio`、`async-std`、`smol` 之类的 crate，它们负责生成 `Waker`、维护就绪队列、调度任务。

## 相关

- [[future|std::future]]：`async` / `await` 与 `Future` 特质的定义。
- [[future.Future|Future]]：`poll`、`Output`、组合子的完整说明。
- [[pin|std::pin]]：`Pin`、`Unpin`，为什么异步需要固定地址。
- [[22-异步编程|异步编程]]：从 `async fn` 到执行器的完整脉络。
- [[sync.Arc|Arc]]：`Waker` 常由 `Arc` 包裹，实现跨线程唤醒。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 12 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`Context`](https://doc.rust-lang.org/std/task/struct.Context.html)
- [`RawWaker`](https://doc.rust-lang.org/std/task/struct.RawWaker.html)
- [`RawWakerVTable`](https://doc.rust-lang.org/std/task/struct.RawWakerVTable.html)
- [`Waker`](https://doc.rust-lang.org/std/task/struct.Waker.html)
- [`ContextBuilder`](https://doc.rust-lang.org/std/task/struct.ContextBuilder.html)
- [`LocalWaker`](https://doc.rust-lang.org/std/task/struct.LocalWaker.html)

### 枚举

- [`Poll`](https://doc.rust-lang.org/std/task/enum.Poll.html)

### 特质

- [`Wake`](https://doc.rust-lang.org/std/task/trait.Wake.html)
- [`LocalWake`](https://doc.rust-lang.org/std/task/trait.LocalWake.html)

### 函数

- [`local_waker_fn`](https://doc.rust-lang.org/std/task/fn.local_waker_fn.html)
- [`waker_fn`](https://doc.rust-lang.org/std/task/fn.waker_fn.html)

### 宏

- [`ready`](https://doc.rust-lang.org/std/task/macro.ready.html)

<!-- END AUTO ITEMS -->
