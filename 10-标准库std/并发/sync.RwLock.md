---
title: "std::sync::RwLock"
type: std-条目
kind: 结构体
module: sync
slug: sync.RwLock
stable: "1.0.0"
tags:
  - std/类型
  - std/并发
aliases:
  - RwLock
一句话: 读写锁，允许多个读者同时进入，写者独占，适合读多写少的共享配置或缓存。
---

# `RwLock`

> [!abstract] 一句话
> `RwLock<T>` 区分读锁和写锁：任意时刻要么多个读者同时在读，要么最多一个写者在改，读多写少的场景比 [[sync.Mutex|Mutex]] 并行度高得多。

## 简介

`RwLock` 是 reader-writer lock 的缩写。`read()` 拿共享读锁，多个线程可以同时持读锁；`write()` 拿独占写锁，此时既没有读者也没有其他写者。[[sync.Mutex|Mutex]] 不区分读写，无论你只想看一眼还是想改一笔，都得排队；`RwLock` 把「只读的可以并行」这条信息利用了起来。

代价是更复杂的状态管理和稍高的开销：读锁也要做原子操作与计数，短小的临界区用 `RwLock` 未必比 `Mutex` 快。**优先级策略由所在操作系统决定**，标准库不作保证：一个正在等写锁的线程会不会挡住后续 `read()` 调用，取决于底层实现，可能出现写者饥饿，也可能出现读者被阻塞。

它同样有中毒机制：持锁线程 panic 后 `read` / `write` 返回 `Err(PoisonError)`，`try_read` / `try_write` 在锁被占时返回 `TryLockError::WouldBlock`。与 `Mutex` 一样，读锁和写锁都不保证可重入——同一线程在没有写者时嵌套 `read()` 通常能成功，但只要还有写者在等待，递归读就可能死锁，不要依赖这个行为。

```rust
use std::sync::{Arc, RwLock};
use std::thread;

fn main() {
    let data = Arc::new(RwLock::new(vec![1, 2, 3]));

    // 多个读者可以同时进入临界区
    let mut readers = Vec::new();
    for _ in 0..4 {
        let data = Arc::clone(&data);
        readers.push(thread::spawn(move || {
            let guard = data.read().unwrap();
            guard.iter().sum::<i32>()
        }));
    }
    for r in readers {
        assert_eq!(r.join().unwrap(), 6);
    }

    // 写者独占，改完释放
    {
        let mut guard = data.write().unwrap();
        guard.push(4);
    }
    assert_eq!(*data.read().unwrap(), vec![1, 2, 3, 4]);
    println!("长度 = {}", data.read().unwrap().len());
}
```

## 常用方法

### 构造与读锁

| 方法 | 说明 |
| --- | --- |
| `new(t)` | 创建一把未加锁的读写锁并包住 `t`。 |
| `read()` | 获取共享读锁，必要时阻塞当前线程。 |
| `try_read()` | 尝试获取读锁，失败立即返回。 |

### 写锁

| 方法 | 说明 |
| --- | --- |
| `write()` | 获取独占写锁，必要时阻塞当前线程。 |
| `try_write()` | 尝试获取写锁，失败立即返回。 |

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

> [!tip] 读锁不等于「快」
> 初始化、批量修改这类高频写的场景用 `RwLock` 反而更慢，因为它还要维护读者计数。先估读写比例，再看要不要换回 `Mutex`。

## 示例

```rust
use std::sync::{Arc, RwLock};
use std::thread;

fn main() {
    let config = Arc::new(RwLock::new(10));

    // 读者并发读取
    let mut readers = Vec::new();
    for _ in 0..3 {
        let config = Arc::clone(&config);
        readers.push(thread::spawn(move || *config.read().unwrap()));
    }

    // 写者独占修改，守卫离开作用域即释放
    {
        let mut writer = config.write().unwrap();
        *writer += 5;
        // 已有读锁时，try_write 立即失败而不是阻塞
        assert!(config.try_write().is_err());
    }

    for r in readers {
        let seen = r.join().unwrap();
        assert!(seen == 10 || seen == 15);
    }
    assert_eq!(*config.read().unwrap(), 15);

    // get_mut：独占引用下无需加锁；into_inner：消耗锁取出数据
    let mut owned = RwLock::new(vec![1]);
    owned.get_mut().unwrap().push(2);
    assert_eq!(owned.into_inner().unwrap(), vec![1, 2]);
}
```

## 常见陷阱

1. **把读锁当「无锁」用**：读者也要做原子计数，极短的临界区里 `Mutex` 往往更快，别默认 `RwLock` 更优。
2. **递归获取读锁**：有写者在等待时，同一线程再次 `read()` 可能死锁；不要假设读锁可重入。
3. **依赖公平性**：谁先拿到锁由操作系统决定，写者可能饥饿，需要公平性时自己在上层排队。
4. **持写锁做耗时操作**：写锁是独占的，期间所有读写全部停摆；把计算挪到锁外，只把最终赋值放进临界区。
5. **中毒后直接 `unwrap`**：读锁也可能中毒；确认数据可用时用 `unwrap_or_else(|e| e.into_inner())`。

## 相关

- [[sync|std::sync 模块]]：本模块全部条目。
- [[sync.Mutex|Mutex]]：不区分读写的互斥锁，写多读少时更简单。
- [[sync.Arc|Arc]]：跨线程共享 `RwLock` 的标准组合。
- [[thread|std::thread]]：线程创建与 `join`。
- [[21-并发编程|并发编程]]：锁与共享状态的系统讲法。
