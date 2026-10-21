---
title: "std::sync"
type: std-模块
module: sync
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - sync
  - 同步原语模块
一句话: 并发同步原语：Arc 共享所有权、Mutex/RwLock 互斥、mpsc 通道、atomic 原子类型。
---

# std::sync

> [!abstract] 一句话
> `std::sync` 是跨线程共享数据的工具箱：[[sync.Arc|Arc]] 让所有权可共享，[[sync.Mutex|Mutex]] 与 [[sync.RwLock|RwLock]] 保证互斥访问，`mpsc` 负责传消息，`atomic` 提供无锁原子操作。

## 模块简介

多线程编程绕不开两个问题：**数据怎么共享**、**访问怎么排序**。`std::sync` 给出标准库层面的答案。共享所有权用 [[sync.Arc|Arc]]（Atomically Reference Counted）：它和 [[rc|std::rc]] 的 `Rc` 语义相同，只是计数改成原子操作，因此 `Arc<T>` 在 `T: Send + Sync` 时是 `Send + Sync`，可以安全地 `clone` 后 move 进 [[thread|std::thread]] 的 `spawn` 闭包。代价是每次 `clone` 一次原子自增，比 `Rc` 贵，但仍然是常数开销。

互斥访问用 [[sync.Mutex|Mutex]] 和 [[sync.RwLock|RwLock]]。`Mutex<T>` 把数据和锁绑成一个整体：`lock()` 返回 `MutexGuard`，RAII 保证离开作用域自动解锁，想忘记解锁都难；锁被某个 panic 的线程持有过会被标记为「中毒」（poisoned），`lock()` 返回 `Err(PoisonError)`，提示你数据可能处于不一致状态。`RwLock<T>` 区分读锁与写锁：多个读者可同时进入，写者独占，适合读多写少的配置或缓存。两者都不保证公平，也不做死锁检测——**两个锁的获取顺序必须全局一致**，否则迟早互等。

不想共享内存就用消息传递：`std::sync::mpsc`（multi-producer, single-consumer）提供通道，`Sender::send` 把值 move 进通道，`Receiver::recv` 阻塞等待。通道在发送端全部 drop 后返回 `Err`，所以 `while let Ok(v) = rx.recv()` 是很自然的多生产者收尾写法。标准库的口头禅是「**共享内存来通信，还是通信来共享内存**」，能用通道表达的所有权转移，往往比一把大锁更不容易错。

最底层是 `std::sync::atomic`：`AtomicBool`、`AtomicUsize`、`AtomicPtr` 等，用 `load` / `store` / `fetch_add` / `compare_exchange` 配合 `Ordering` 做无锁计数、标志位、简单状态机。除此之外还有 `Condvar`（条件变量，配合 `Mutex` 实现「等某个条件成立」）、`Barrier`（让 N 个线程在同一个点汇合）、`Once` / `OnceLock` / `LazyLock`（全局只初始化一次）。

## 快速上手

```rust
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{mpsc, Arc, Mutex, OnceLock, RwLock};
use std::thread;

fn main() {
    // Arc + atomic：4 个线程各加 1000 次，无锁计数
    let counter = Arc::new(AtomicUsize::new(0));
    let mut handles = Vec::new();
    for _ in 0..4 {
        let counter = Arc::clone(&counter);
        handles.push(thread::spawn(move || {
            for _ in 0..1000 {
                counter.fetch_add(1, Ordering::Relaxed);
            }
        }));
    }
    for h in handles {
        h.join().unwrap();
    }
    assert_eq!(counter.load(Ordering::Relaxed), 4000);

    // Mutex：把数据和锁绑在一起，guard 离开作用域自动解锁
    let data = Arc::new(Mutex::new(Vec::new()));
    let writer = Arc::clone(&data);
    thread::spawn(move || {
        writer.lock().unwrap().push(1);
    })
    .join()
    .unwrap();
    assert_eq!(*data.lock().unwrap(), vec![1]);

    // RwLock：写锁独占，读锁可并发
    let config = Arc::new(RwLock::new(10));
    {
        let mut w = config.write().unwrap();
        *w += 5;
    }
    let reader = Arc::clone(&config);
    let seen = thread::spawn(move || *reader.read().unwrap()).join().unwrap();
    assert_eq!(seen, 15);

    // mpsc：多个生产者、一个消费者，发送端全 drop 后 recv 返回 Err
    let (tx, rx) = mpsc::channel();
    for id in 0..3 {
        let tx = tx.clone();
        thread::spawn(move || {
            tx.send(id * 10).unwrap();
        });
    }
    drop(tx);
    let mut got: Vec<i32> = Vec::new();
    while let Ok(v) = rx.recv() {
        got.push(v);
    }
    got.sort();
    assert_eq!(got, vec![0, 10, 20]);

    // OnceLock：全局值只初始化一次
    static INIT: OnceLock<String> = OnceLock::new();
    let value = INIT.get_or_init(|| String::from("已初始化"));
    assert_eq!(value, "已初始化");

    println!("计数 = {}", counter.load(Ordering::Relaxed));
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[sync.Arc\|Arc]] | 线程安全的引用计数指针，共享所有权。 |
| `sync::Weak` | `Arc` 的弱引用，打破循环、避免泄漏。 |
| [[sync.Mutex\|Mutex]] | 互斥锁，`lock()` 返回 `MutexGuard`。 |
| `sync::MutexGuard` | RAII 锁守卫，drop 时自动解锁。 |
| [[sync.RwLock\|RwLock]] | 读写锁，多读单写。 |
| `sync::RwLockReadGuard` / `RwLockWriteGuard` | 读 / 写守卫，drop 时释放。 |
| `sync::Condvar` | 条件变量，配合 `Mutex` 等待条件成立。 |
| `sync::Barrier` | 让固定数量的线程在一点汇合。 |
| `sync::OnceLock` | 只写一次、可全局共享的初始化容器。 |
| `sync::LazyLock` | 首次访问时初始化，之后只读。 |
| `sync::Once` | 底层的「全局只执行一次」原语。 |
| `sync::mpsc` | 子模块，多生产者单消费者通道。 |
| `sync::atomic` | 子模块，`AtomicUsize` 等原子类型与 `Ordering`。 |
| `sync::PoisonError` / `sync::LockResult` | 锁中毒的错误类型与结果别名。 |

## 注意事项

> [!warning] 锁中毒与死锁
> 线程持锁期间 panic 会把 `Mutex` / `RwLock` 标记为中毒，之后 `lock()` 返回 `Err(PoisonError)`；确实要继续用可以 `unwrap_or_else(|e| e.into_inner())`，但要先确认数据没被写坏。死锁更常见：两把锁以不同顺序获取就会互等，标准库不会帮你检测，规矩是**全局固定加锁顺序**，且临界区别做耗时 I/O。

> [!danger] 持锁跨越 `.await` 或长操作
> `MutexGuard` 不是 `Send`，在异步任务里跨 `.await` 持锁通常编译不过；同步代码里持锁做网络请求、文件读写则会让所有线程排队。正确做法是：锁内只做内存修改，尽快 drop guard，把 I/O 放到锁外。

> [!tip] 先想通道，再想锁
> `mpsc` 能把数据所有权 move 给接收方，天然避免共享可变状态；真的需要多方读写同一块内存才上 `Mutex` / `RwLock`。纯计数、标志位这类场景优先用 `atomic`，比加锁便宜得多；`Ordering` 拿不准时先用 `SeqCst`（最严格、最易读），确认热点后再放宽。

## 相关

- [[sync.Arc|Arc]]：跨线程共享所有权的核心类型。
- [[sync.Mutex|Mutex]] / [[sync.RwLock|RwLock]]：两种锁的完整方法。
- [[thread|std::thread]]：线程创建、`join`、scoped 线程。
- [[marker.Send|Send]] / [[marker.Sync|Sync]]：共享与移动的编译期约束。
- [[21-并发编程|并发编程]]：线程、通道、共享状态的系统讲法。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 27 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [[sync.Arc|`Arc`]]
- [`Barrier`](https://doc.rust-lang.org/std/sync/struct.Barrier.html)
- [`BarrierWaitResult`](https://doc.rust-lang.org/std/sync/struct.BarrierWaitResult.html)
- [`Condvar`](https://doc.rust-lang.org/std/sync/struct.Condvar.html)
- [`LazyLock`](https://doc.rust-lang.org/std/sync/struct.LazyLock.html)
- [[sync.Mutex|`Mutex`]]
- [`MutexGuard`](https://doc.rust-lang.org/std/sync/struct.MutexGuard.html)
- [`Once`](https://doc.rust-lang.org/std/sync/struct.Once.html)
- [`OnceLock`](https://doc.rust-lang.org/std/sync/struct.OnceLock.html)
- [`OnceState`](https://doc.rust-lang.org/std/sync/struct.OnceState.html)
- [`PoisonError`](https://doc.rust-lang.org/std/sync/struct.PoisonError.html)
- [[sync.RwLock|`RwLock`]]
- [`RwLockReadGuard`](https://doc.rust-lang.org/std/sync/struct.RwLockReadGuard.html)
- [`RwLockWriteGuard`](https://doc.rust-lang.org/std/sync/struct.RwLockWriteGuard.html)
- [`WaitTimeoutResult`](https://doc.rust-lang.org/std/sync/struct.WaitTimeoutResult.html)
- [`Weak`](https://doc.rust-lang.org/std/sync/struct.Weak.html)
- [`MappedMutexGuard`](https://doc.rust-lang.org/std/sync/struct.MappedMutexGuard.html)
- [`MappedRwLockReadGuard`](https://doc.rust-lang.org/std/sync/struct.MappedRwLockReadGuard.html)
- [`MappedRwLockWriteGuard`](https://doc.rust-lang.org/std/sync/struct.MappedRwLockWriteGuard.html)
- [`ReentrantLock`](https://doc.rust-lang.org/std/sync/struct.ReentrantLock.html)
- [`ReentrantLockGuard`](https://doc.rust-lang.org/std/sync/struct.ReentrantLockGuard.html)
- [`SyncView`](https://doc.rust-lang.org/std/sync/struct.SyncView.html)
- [`UniqueArc`](https://doc.rust-lang.org/std/sync/struct.UniqueArc.html)

### 枚举

- [`TryLockError`](https://doc.rust-lang.org/std/sync/enum.TryLockError.html)

### 类型别名

- [`LockResult`](https://doc.rust-lang.org/std/sync/type.LockResult.html)
- [`TryLockResult`](https://doc.rust-lang.org/std/sync/type.TryLockResult.html)

### 常量

- [`ONCE_INIT`](https://doc.rust-lang.org/std/sync/constant.ONCE_INIT.html)

<!-- END AUTO ITEMS -->
