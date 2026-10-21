---
title: "std::sync::Mutex"
type: std-条目
kind: 结构体
module: sync
slug: sync.Mutex
stable: "1.0.0"
tags:
  - std/类型
  - std/并发
aliases:
  - Mutex
一句话: 互斥锁，把数据和锁绑在一起，只有拿到守卫才能访问数据，离开作用域自动解锁。
---

# `Mutex`

> [!abstract] 一句话
> `Mutex<T>` 是「互斥 + 数据」的组合体：想读写 `T` 必须先 `lock()` 拿到 `MutexGuard`，守卫析构时自动解锁，忘记解锁这件事从语言层面被消灭了。

## 简介

`Mutex`（mutual exclusion）用来保护被多个线程共享、需要串行访问的数据。与 C 里「一把锁 + 一个裸指针」的写法不同，Rust 的 `Mutex<T>` 把**数据和锁绑成一个整体**：构造时把 `T` 移进锁里，之后只能通过 `lock` / `try_lock` 返回的 RAII 守卫访问。编译器因此能保证「访问数据时一定持锁」，这也是标准库并发安全的基石。

`lock()` 会**阻塞**当前线程直到拿到锁；`try_lock()` 立刻返回，锁被占用时给 `Err(TryLockError::WouldBlock)`，被毒化时给 `Err(TryLockError::Poisoned)`。锁还实现了「中毒」（poisoning）机制：持锁线程 panic 后锁被标记为中毒，后续 `lock()` 返回 `Err(PoisonError)`，因为受保护的不变量可能已被破坏；确认数据没坏时可以 `unwrap_or_else(|e| e.into_inner())` 继续用，或调用 `clear_poison` 清除标记。

`Mutex` 本身不可重入：同一线程重复 `lock()` 会死锁。它的公平性不作保证，死锁也不会被检测。跨线程共享时通常写成 `Arc<Mutex<T>>`（见 [[sync.Arc|Arc]]）；读多写少的场景可以用 [[sync.RwLock|RwLock]]，纯计数或标志位用 `std::sync::atomic` 更便宜。

```rust
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let counter = Arc::new(Mutex::new(0usize));
    let mut handles = Vec::new();

    for _ in 0..8 {
        let counter = Arc::clone(&counter);
        handles.push(thread::spawn(move || {
            for _ in 0..1000 {
                // 非原子的加法之所以安全，是因为同一时刻只有一个线程持锁
                let mut guard = counter.lock().unwrap();
                *guard += 1;
            }
        }));
    }

    for h in handles {
        h.join().unwrap();
    }

    assert_eq!(*counter.lock().unwrap(), 8000);
    println!("最终计数 = {}", *counter.lock().unwrap());
}
```

## 常用方法

### 构造与获取锁

| 方法 | 说明 |
| --- | --- |
| `new(t)` | 创建一把未加锁的互斥锁并包住 `t`。 |
| `lock()` | 获取锁，拿不到就阻塞当前线程。 |
| `try_lock()` | 尝试获取锁，失败立即返回而不阻塞。 |

### 中毒状态

| 方法 | 说明 |
| --- | --- |
| `is_poisoned()` | 判断锁是否因持锁线程 panic 而中毒。 |
| `clear_poison()` | 清除中毒标记，恢复正常使用。 |

### 取出与借用内部数据

| 方法 | 说明 |
| --- | --- |
| `get_mut()` | 借用内部数据，需要独占引用，无需加锁。 |
| `into_inner()` | 消耗锁，取出内部数据。 |

> [!tip] `try_lock` 的错误要分开看
> `WouldBlock` 表示「别人正持有，稍后再试」，`Poisoned` 表示「上一个持锁者 panic 了」，前者可以重试，后者要先决定数据还能不能用。

## 示例

```rust
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    // try_lock：锁被占用时立即返回 Err，不会卡住
    let m = Mutex::new(1);
    {
        let guard = m.lock().unwrap();
        assert_eq!(*guard, 1);
        assert!(m.try_lock().is_err());
    }
    assert!(m.try_lock().is_ok());

    // 线程持锁时 panic，锁会被标记为中毒
    let shared = Arc::new(Mutex::new(String::from("旧值")));
    let worker = Arc::clone(&shared);
    let _ = thread::spawn(move || {
        let mut guard = worker.lock().unwrap();
        guard.push('!');
        panic!("故意 panic");
    })
    .join();

    assert!(shared.is_poisoned());
    {
        // 中毒后 lock 仍然给出守卫，只是附带一个 PoisonError
        let guard = shared.lock().unwrap_or_else(|e| e.into_inner());
        assert_eq!(*guard, "旧值!");
    }

    shared.clear_poison();
    assert!(!shared.is_poisoned());
    assert_eq!(*shared.lock().unwrap(), "旧值!");

    // get_mut 与 into_inner 都要求独占所有权，因此不需要加锁
    let mut owned = Mutex::new(5);
    *owned.get_mut().unwrap() += 1;
    assert_eq!(owned.into_inner().unwrap(), 6);
}
```

## 常见陷阱

1. **同一线程重复加锁**：`Mutex` 不可重入，守卫还没 drop 就再 `lock()` 必然死锁；把临界区缩小成一个花括号内的表达式。
2. **持锁做 I/O 或耗时计算**：所有线程都会排队等这一把锁，锁内只改内存，把写文件、发请求放到锁外。
3. **多把锁乱序获取**：两个线程分别先拿 A 后拿 B、先拿 B 后拿 A，就会互等；全局约定统一的加锁顺序。
4. **中毒后直接 `unwrap`**：会把 panic 传播到当前线程；确认数据可用时用 `unwrap_or_else(|e| e.into_inner())` 或先 `clear_poison`。
5. **跨 `.await` 持有守卫**：`MutexGuard` 不是 `Send`，异步任务里持锁跨越 `.await` 通常编译不过，应先算出结果再 drop 守卫。

## 相关

- [[sync|std::sync 模块]]：本模块全部条目。
- [[sync.RwLock|RwLock]]：读多写少时的读写锁。
- [[sync.Arc|Arc]]：跨线程共享 `Mutex` 的标准组合。
- [[thread|std::thread]]：线程创建与 `join`。
- [[21-并发编程|并发编程]]：共享状态与锁的系统讲法。
