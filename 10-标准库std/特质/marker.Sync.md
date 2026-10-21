---
title: "std::marker::Sync"
type: std-条目
kind: 特质
module: marker
slug: marker.Sync
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - Sync
一句话: 标记「引用可以安全地跨线程共享」，等价于 &T: Send，由编译器自动推导。
---

# `Sync`

> [!abstract] 一句话
> `Sync` 是自动特质：`T: Sync` 表示把 `&T` 同时递给多个线程是安全的，精确说法是「`T: Sync` 当且仅当 `&T: Send`」。它没有方法，只在类型检查期约束共享引用。

## 简介

`Send` 管「值搬走」，`Sync` 管「引用被共享」。多线程里 `Arc::clone` 之后各线程持有的都是 `&T`，能不能同时读同一块数据，就由 `Sync` 决定。

判定的直觉是「有没有无锁的内部可变状态」。`i32`、`String`、`Vec<T>`（`T: Sync` 时）都是只读共享安全的；`Cell<T>`、`RefCell<T>` 通过 `UnsafeCell` 在 `&self` 下就能改值，如果没有外部锁，两个线程同时改就是数据竞争，所以它们不是 `Sync`。`Mutex<T>` 反而可以是——它把内部可变包装在锁后面，访问必须串行。

一个容易记反的对照：`&T` 是 `Send` 当且仅当 `T: Sync`；`&mut T` 是 `Send` 当且仅当 `T: Send`。前者是共享引用能否跨线程，后者是独占引用能否搬家。

## 必须实现

无需实现，也没有方法可写。`Sync` 由编译器按类型的组成自动推导：

| 类型构造 | 是否 `Sync` |
| --- | --- |
| `i32`、`String`、`&T` | 是（`&T` 需要 `T: Sync`） |
| `Vec<T>`、`Box<T>`、`Option<T>` | `T: Sync` 时是 |
| `Cell<T>`、`RefCell<T>`、`UnsafeCell<T>` | 永远不是 |
| `Mutex<T>`、`RwLock<T>`、`AtomicUsize` | 是（内部已同步） |
| `Rc<T>` | 永远不是 |

## 与相邻 trait 的关系

| trait | 关系 |
| --- | --- |
| `Send` | 定义上互补：`T: Sync` ⇔ `&T: Send`。 |
| `Arc` | `Arc<T>` 是 `Send + Sync` 当且仅当 `T: Send + Sync`。 |
| `Mutex` / `RwLock` | 把 `!Sync` 的内部可变状态包成 `Sync`。 |
| `Cell` / `RefCell` | 无锁内部可变，典型 `!Sync` 类型。 |

## 示例

### 只读共享与编译期断言

```rust
use std::cell::Cell;
use std::rc::Rc;
use std::sync::{Arc, Mutex};
use std::thread;

fn assert_sync<T: Sync>() {}

fn main() {
    assert_sync::<i32>();
    assert_sync::<String>();
    assert_sync::<Arc<str>>();
    // Mutex 内部可变，但访问受锁保护，所以是 Sync
    assert_sync::<Mutex<Vec<u8>>>();

    // 下面两行取消注释会编译失败：
    // assert_sync::<Cell<i32>>();
    // assert_sync::<Rc<i32>>();

    // 多个线程同时读同一份数据：靠 Arc<Vec<i32>> 的 Sync 成立
    let data = Arc::new(vec![1, 2, 3]);
    let mut handles = Vec::new();
    for _ in 0..3 {
        let data = Arc::clone(&data);
        handles.push(thread::spawn(move || data.iter().sum::<i32>()));
    }
    for h in handles {
        assert_eq!(h.join().unwrap(), 6);
    }
}
```

### `unsafe impl Sync` 的责任

```rust
// 一张只读查找表：只被读、永不被写
struct SharedTable(*const u8);

// SAFETY: 这里承诺「指向的数据在运行期只读，且不会在别的线程被写」。
// 一旦有人能通过别的路径修改它，多线程同时读就是未定义行为
unsafe impl Sync for SharedTable {}

fn assert_sync<T: Sync>() {}

fn main() {
    assert_sync::<SharedTable>();

    let table = SharedTable(std::ptr::null());
    assert!(table.0.is_null());
}
```

## 常见陷阱

1. **`Cell` / `RefCell` 是 `Send` 却不是 `Sync`**：能把整个值搬走，但不能共享 `&` 给别人改。要共享就换 `Mutex` / `RwLock`。
2. **`unsafe impl Sync` 一旦写错就是数据竞争**：编译器不会再检查，即使是「只读」承诺，只要存在任何可能的写入路径就是 UB。
3. **以为 `Send` 蕴含 `Sync`**：反例是 `MutexGuard`（`Sync` 但不是 `Send`）、`Cell<T>`（`Send` 但不是 `Sync`）。
4. **容器的 `Sync` 靠元素传递**：`Vec<T>`、`HashMap<K, V>` 只有在元素都 `Sync` 时才 `Sync`，`Vec<RefCell<u8>>` 会拖垮整个结构。
5. **`static` 要求 `Sync`**：共享的可变全局必须包在 `Mutex` / `RwLock` / 原子类型里，否则连 `static` 都放不进去。
6. **为了过编译随手加锁**：`Mutex` 能让类型变 `Sync`，但每次访问都要拿锁，热路径上先考虑原子类型或分片。

## 相关

- [[marker.Send|Send]]：把所有权搬去别的线程的对应特质。
- [[sync.Arc|Arc]]：`Sync` 类型最常用的跨线程共享载体。
- [[sync.Mutex|Mutex]]：把内部可变状态包装成 `Sync` 的互斥锁。
- [[cell.RefCell|RefCell]]：运行时借用检查的 `!Sync` 内部可变类型。
- [[cell.Cell|Cell]]：`Send` 但 `!Sync` 的最小例子。
- [[21-并发编程|并发编程]]：线程与同步原语的完整图景。
- [[marker|std::marker 模块]]：标记特质一览。
