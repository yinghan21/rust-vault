---
title: "std::future::Future"
type: std-条目
kind: 特质
module: future
slug: future.Future
stable: "1.36.0"
tags:
  - std/特质
aliases:
  - Future
一句话: 异步计算的统一表示，poll 一次不阻塞，未就绪时注册唤醒并返回 Pending。
---

# `Future`

> [!abstract] 一句话
> `Future` 表示「一个还没算完的值」：`poll` 尝试推进一步，就绪就返回 `Ready(值)`，没就绪就登记唤醒并返回 `Pending`，绝不阻塞当前线程。

## 简介

异步的核心抽象只有一句签名：`poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output>`。`Poll` 是只有 `Ready` 和 `Pending` 两个变体的枚举，`Context` 里装着 `Waker`，也就是「怎么叫醒我」的句柄。

流程是这样的：executor 调 `poll`，future 没就绪就把 `cx.waker()` 存下来（或直接唤醒自己）然后返回 `Pending`；等到数据真的到了，某处调用 `waker.wake()`，executor 重新把任务排进队列，再次 `poll`。**丢失唤醒**（返回 `Pending` 却没登记 waker）会让任务永远停在那里，这是异步里最经典的卡死原因。

`self: Pin<&mut Self>` 不是装饰：`async` 块生成的 future 往往自引用（局部变量被跨 `.await` 的引用指向），一旦被移动，指针就悬空了。`Pin` 保证它固定在原地，因此 `&mut fut` 不能直接 poll，得先 `Box::pin` 或 `std::pin::pin!`。

日常写代码时几乎不直接 `poll`，`async` / `.await` 已经把状态机生成好了；手写 `Future` 只出现在底层组件里。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `poll(self, cx)` | 推进一步：返回 `Ready` 或登记唤醒后返回 `Pending`。 |
| `type Output` | 关联类型，声明最终产出的值类型。 |

完整签名：`fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output>`。

## 与相邻 trait 的关系

| trait | 关系 |
| --- | --- |
| `Pin` | `poll` 的接收者必须是固定住的引用，`Future` 与 `Pin` 绑定使用。 |
| `task::Wake` / `Waker` | 唤醒机制的实现端，`Waker::from(Arc<W>)` 由 `Wake` 构造。 |
| `IntoFuture` | `.await` 真正调用的转换特质，`Future` 自身也实现它。 |
| `Iterator` | 对称的同步抽象：`poll_next` 对应 `poll`，`Poll<T>` 两者共用。 |

## 示例

### 手写 `Future`，配一个最小 executor

```rust
use std::future::Future;
use std::pin::Pin;
use std::sync::Arc;
use std::task::{Context, Poll, Wake, Waker};

// 前几次 poll 返回 Pending，倒数结束后 Ready
struct Countdown {
    left: u8,
}

impl Future for Countdown {
    type Output = &'static str;

    fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        if self.left == 0 {
            Poll::Ready("liftoff")
        } else {
            self.left -= 1;
            // 登记唤醒：告诉 executor「稍后再 poll 我」
            cx.waker().wake_by_ref();
            Poll::Pending
        }
    }
}

// 最小 waker：靠立即自我唤醒驱动轮询，wake 里无需做事
struct NoopWaker;

impl Wake for NoopWaker {
    fn wake(self: Arc<Self>) {}
}

// 极简 executor：把 future 钉在堆上，循环 poll 直到 Ready
fn block_on<F: Future>(fut: F) -> F::Output {
    let waker = Waker::from(Arc::new(NoopWaker));
    let mut cx = Context::from_waker(&waker);
    let mut fut = Box::pin(fut);

    loop {
        match fut.as_mut().poll(&mut cx) {
            Poll::Ready(value) => return value,
            Poll::Pending => continue, // 真实 executor 会挂起线程等唤醒
        }
    }
}

fn main() {
    assert_eq!(block_on(Countdown { left: 3 }), "liftoff");

    // async 块本身就是一个 Future，同一个 block_on 就能驱动
    assert_eq!(block_on(async { 1 + 1 }), 2);
}
```

### 不同 future 类型要装箱才能同放

```rust
use std::future::Future;
use std::pin::Pin;

fn main() {
    // 每个 async 块都是独立的匿名类型，放进同一个集合必须装箱
    let tasks: Vec<Pin<Box<dyn Future<Output = i32>>>> =
        vec![Box::pin(async { 1 }), Box::pin(async { 2 + 3 })];

    assert_eq!(tasks.len(), 2);
}
```

## 常见陷阱

1. **直接 `&mut fut` 去 poll**：报「`fut` cannot be unpinned」，用 `Box::pin(fut)` 或 `std::pin::pin!(fut)` 固定。
2. **返回 `Pending` 却没登记 waker**：丢失唤醒，任务永久挂起；要么 `cx.waker().wake_by_ref()`，要么把 waker 存给将来会触发的一方。
3. **在 `poll` 里做阻塞操作**：`thread::sleep`、同步读文件会把 executor 的线程占死，其它任务一起卡住。
4. **忘记 future 是惰性的**：`async` 块创建后不 `.await` / 不 poll 就什么也不做，末尾不等待等于丢弃任务。
5. **跨 `.await` 持有非 `Send` 的守卫**：`MutexGuard` 让整个 future 不是 `Send`，多线程 executor 的 `spawn` 会拒绝。
6. **以为 `poll` 会被反复调到 ready 为止**：executor 只在被唤醒后才再 poll，没有唤醒就没有下一次机会。

## 相关

- [[future|std::future 模块]]：`Future`、`IntoFuture` 与 `Pending`。
- [[task|std::task 模块]]：`Context`、`Poll`、`Waker` 与 `Wake`。
- [[pin|std::pin 模块]]：`Pin`、`Unpin` 与自引用结构。
- [[22-异步编程|异步编程]]：`async` / `.await` 与 executor 的完整链路。
- [[marker.Send|Send]]：future 能否交给多线程 executor 的前提。
- [[iter.Iterator|Iterator]]：同步世界的对称抽象。
