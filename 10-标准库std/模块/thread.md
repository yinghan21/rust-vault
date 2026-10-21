---
title: "std::thread"
type: std-模块
module: thread
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - thread
  - 线程模块
一句话: 原生 OS 线程：spawn 创建、JoinHandle 等待、scope 借用、sleep 与 TLS。
---

# std::thread

> [!abstract] 一句话
> `std::thread` 管理操作系统原生线程：[[thread.spawn|spawn]] 起一个线程并拿到 `JoinHandle`，`join` 等它结束，`thread::scope` 让子线程安全借用局部变量。

## 模块简介

Rust 程序的执行单位是**原生 OS 线程**，每个线程有自己的栈和局部状态，由操作系统调度。`thread::spawn` 接收一个 `FnOnce` 闭包，在新线程里执行它，返回 `JoinHandle<T>`——`T` 是闭包的返回值。`JoinHandle::join` 阻塞当前线程直到目标线程结束，返回 `thread::Result<T>`，也就是 `Result<T, Box<dyn Any + Send>>`：`Err` 里装的是那个线程 panic 时携带的载荷，所以「从别的线程检测到崩溃」是可行的。

闭包要跨越线程边界，所以必须是 `Send + 'static`：`Send` 保证移动过去不会出问题，`'static` 表示不能借用当前栈上的临时数据（线程可能活得更久）。这就是为什么 `spawn` 的闭包通常写成 `move ||`，把需要的数据**转移**进去。想共享同一份数据，用 [[sync.Arc|Arc]] 克隆后 move 进去；想在多个子线程里读同一份局部变量，则用 `thread::scope`——作用域保证所有 scoped 线程在 `scope` 结束前 join 完，于是借用检查器允许它们借用栈上的数据，不需要 `Arc` 也不需要 `'static`。

线程之间的通信有两条路：`std::sync::mpsc` 通道（把值 move 给接收方，最不容易出锁问题），或者共享内存加锁（`Arc<Mutex<T>>`、`Arc<RwLock<T>>`、原子类型）。前者见 [[sync|std::sync]]。`spawn` 的返回值被丢弃也不会泄漏线程，但你会失去 `join` 的机会，也就无法感知它是否 panic、何时结束。

模块里还有几件周边工具：`thread::sleep` 让当前线程至少睡指定时长；`Builder` 用来给线程起名字、指定栈大小，然后用 `builder.spawn`；`park` / `park_timeout` 配合 `unpark` 做轻量级的挂起唤醒；`yield_now` 主动让出时间片；`available_parallelism` 给出建议的并行度；`LocalKey`（配合 `thread_local!` 宏）提供线程局部存储——每个线程一份独立副本。

## 快速上手

```rust
use std::sync::mpsc;
use std::thread;
use std::time::{Duration, Instant};

fn main() {
    // spawn 返回 JoinHandle，join 阻塞并取出闭包的返回值
    let handle = thread::spawn(|| 6 * 7);
    assert_eq!(handle.join().unwrap(), 42);

    // move 闭包把数据所有权移进新线程
    let msg = String::from("hello");
    let h = thread::spawn(move || msg.len());
    assert_eq!(h.join().unwrap(), 5);

    // 线程间通信：多生产者单消费者通道
    let (tx, rx) = mpsc::channel();
    thread::spawn(move || {
        tx.send(1 + 1).unwrap();
    });
    assert_eq!(rx.recv().unwrap(), 2);

    // Builder 可以给线程起名字（便于日志排查）
    let (tx2, rx2) = mpsc::channel();
    thread::Builder::new()
        .name("worker".into())
        .spawn(move || {
            let name = thread::current().name().unwrap_or("").to_string();
            tx2.send(name).unwrap();
        })
        .unwrap()
        .join()
        .unwrap();
    assert_eq!(rx2.recv().unwrap(), "worker");

    // scoped 线程可以直接借用局部变量，不必上 Arc
    let mut data = vec![1, 2, 3];
    thread::scope(|s| {
        s.spawn(|| println!("长度 = {}", data.len()));
        s.spawn(|| println!("首元素 = {}", data[0]));
    }); // 作用域结束时自动 join，借用随之结束
    data.push(4);
    assert_eq!(data, vec![1, 2, 3, 4]);

    // sleep 至少阻塞指定时长
    let start = Instant::now();
    thread::sleep(Duration::from_millis(20));
    assert!(start.elapsed() >= Duration::from_millis(20));

    // 主动让出时间片，适合忙等循环
    thread::yield_now();

    // 建议并行度至少是 1
    assert!(thread::available_parallelism().unwrap().get() >= 1);

    println!("当前线程 id = {:?}", thread::current().id());
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[thread.spawn\|spawn]] | 创建线程并返回 `JoinHandle`。 |
| [[thread.sleep\|sleep]] | 让当前线程至少睡指定时长。 |
| `thread::JoinHandle` | 线程句柄，`join()` 等待结束并取返回值。 |
| `thread::Builder` | 配置线程名、栈大小后再 `spawn`。 |
| `thread::Thread` | 线程自身的句柄，含 id 与名字。 |
| `thread::ThreadId` | 线程的唯一标识。 |
| `thread::current` | 取得当前线程的 `Thread`。 |
| `thread::scope` | 创建作用域，允许子线程借用局部变量。 |
| `thread::Scope` / `ScopedJoinHandle` | 作用域本体与其线程句柄。 |
| `thread::park` / `park_timeout` | 阻塞当前线程，等 token 或用 `unpark` 唤醒。 |
| `thread::yield_now` | 主动让出时间片给调度器。 |
| `thread::available_parallelism` | 建议使用的并行度估计值。 |
| `thread::LocalKey` | 线程局部存储的键，配合 `thread_local!` 使用。 |
| `thread::Result` | `Result<T, Box<dyn Any + Send>>` 的别名。 |

## 注意事项

> [!warning] `join()` 要检查 `Err`
> 子线程 panic 时 `join()` 返回 `Err`，`unwrap()` 会把 panic 继续在主线程抛出来；直接丢弃 `JoinHandle` 则等于「发出去就不管了」，线程崩溃你也不会知道。库代码里通常把 `join` 的 `Err` 转成自己的错误返回。

> [!danger] 闭包必须 `Send + 'static`
> 借用栈上数据的闭包过不了编译：`spawn` 要求 `'static`。解决方式有三种——用 `move` 把所有权转进去、用 `Arc` 克隆共享、或者改用 `thread::scope` 借用。跨线程共享还需 `T: Sync`，编译器会用 [[marker.Send|Send]] / [[marker.Sync|Sync]] 帮你把关。

> [!tip] 线程不是免费的
> 每个 OS 线程都有独立的栈（默认约 2 MiB 虚拟内存）和内核调度开销，开上万个就会变慢。CPU 密集型任务用 `available_parallelism()` 量级的工作线程池；I/O 密集型、需要海量并发时改用异步（[[task|std::task]] + 运行时）。`sleep` 的精度受系统时钟影响，只保证「至少」，不保证准时。

## 相关

- [[thread.spawn|spawn]] / [[thread.sleep|sleep]]：两个最常用的函数。
- [[sync|std::sync]]：`Arc`、`Mutex`、`RwLock`、`mpsc` 通道。
- [[marker.Send|Send]] / [[marker.Sync|Sync]]：跨线程移动与共享的约束。
- [[21-并发编程|并发编程]]：线程、消息传递、共享状态的系统讲法。
- [[task|std::task]]：异步任务模型，对比线程模型的取舍。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 23 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`AccessError`](https://doc.rust-lang.org/std/thread/struct.AccessError.html)
- [`Builder`](https://doc.rust-lang.org/std/thread/struct.Builder.html)
- [`JoinHandle`](https://doc.rust-lang.org/std/thread/struct.JoinHandle.html)
- [`LocalKey`](https://doc.rust-lang.org/std/thread/struct.LocalKey.html)
- [`Scope`](https://doc.rust-lang.org/std/thread/struct.Scope.html)
- [`ScopedJoinHandle`](https://doc.rust-lang.org/std/thread/struct.ScopedJoinHandle.html)
- [`Thread`](https://doc.rust-lang.org/std/thread/struct.Thread.html)
- [`ThreadId`](https://doc.rust-lang.org/std/thread/struct.ThreadId.html)

### 类型别名

- [`Result`](https://doc.rust-lang.org/std/thread/type.Result.html)

### 函数

- [`available_parallelism`](https://doc.rust-lang.org/std/thread/fn.available_parallelism.html)
- [`current`](https://doc.rust-lang.org/std/thread/fn.current.html)
- [`panicking`](https://doc.rust-lang.org/std/thread/fn.panicking.html)
- [`park`](https://doc.rust-lang.org/std/thread/fn.park.html)
- [`park_timeout`](https://doc.rust-lang.org/std/thread/fn.park_timeout.html)
- [`park_timeout_ms`](https://doc.rust-lang.org/std/thread/fn.park_timeout_ms.html)
- [`scope`](https://doc.rust-lang.org/std/thread/fn.scope.html)
- [[thread.sleep|`sleep`]]
- [`sleep_ms`](https://doc.rust-lang.org/std/thread/fn.sleep_ms.html)
- [[thread.spawn|`spawn`]]
- [`yield_now`](https://doc.rust-lang.org/std/thread/fn.yield_now.html)
- [`add_spawn_hook`](https://doc.rust-lang.org/std/thread/fn.add_spawn_hook.html)
- [`current_id`](https://doc.rust-lang.org/std/thread/fn.current_id.html)
- [`sleep_until`](https://doc.rust-lang.org/std/thread/fn.sleep_until.html)

<!-- END AUTO ITEMS -->
