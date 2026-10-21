---
title: "std::marker::Send"
type: std-条目
kind: 特质
module: marker
slug: marker.Send
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - Send
一句话: 标记「值可以整体搬到另一个线程」，由编译器逐字段自动推导，跨线程传递的前提。
---

# `Send`

> [!abstract] 一句话
> `Send` 是自动特质：`T: Send` 表示 `T` 的值可以安全地把所有权移交给另一个线程。它不带任何方法，只在类型检查期起作用——`thread::spawn` 的闭包要求它，`Arc<T>` 跨线程共享也要求它。

## 简介

`Send` 回答的问题是「这个值整个搬过去安全吗」。搬的是所有权，不涉及共享，所以典型反例是 `Rc<T>`：它的引用计数用普通整数自增，两个线程同时克隆就会丢掉计数更新（不是数据竞争那么明显，而是直接算错，进而提前释放或泄漏），标准库因此没有给 `Rc` 实现 `Send`。

对照的 `Arc<T>` 用原子操作维护计数，代价是每次克隆多几条原子指令，换来的是可以跨线程。

`Send` 是**自动特质**（auto trait）：编译器逐字段推导，字段全 `Send` 结构体就 `Send`。你只能在极少数情况下用 `unsafe impl Send for MyType {}` 手动声明，一旦这么做，编译器的那层检查就失效了，正确性全部由你负责。

## 必须实现

无需实现，也没有方法可写。`Send` 的实现完全由编译器根据类型的组成自动推导：

| 类型构造 | 是否 `Send` |
| --- | --- |
| `i32`、`String`、`Vec<T>`、`Box<T>` | `T: Send` 时是 |
| `&T` | `T: Sync` 时是 |
| `&mut T` | `T: Send` 时是 |
| `Rc<T>`、`*const T`、`*mut T` | 永远不是 |
| 结构体 / 枚举 / 元组 | 每个字段都是 `Send` 时才是 |

## 与相邻 trait 的关系

| trait | 关系 |
| --- | --- |
| `Sync` | 孪生标记：`T: Sync` 等价于 `&T: Send`，一个管搬家一个管共享。 |
| `Copy` / `Clone` | 与 `Send` 正交：能复制不代表能跨线程。 |
| `Arc` | 用原子计数换取 `Send + Sync`，替代 `Rc` 的跨线程方案。 |
| `Mutex` | `Mutex<T>` 在 `T: Send` 时是 `Send + Sync`，靠锁把并发访问串行化。 |

## 示例

### 跨线程移交所有权

```rust
use std::sync::Arc;
use std::thread;

fn main() {
    // Arc<Vec<i32>> 是 Send + Sync，可以克隆句柄分发到多个线程
    let shared = Arc::new(vec![1, 2, 3]);

    let mut handles = Vec::new();
    for _ in 0..2 {
        let shared = Arc::clone(&shared);
        // move 把 Arc 句柄搬进新线程
        handles.push(thread::spawn(move || shared.iter().sum::<i32>()));
    }

    let total: i32 = handles.into_iter().map(|h| h.join().unwrap()).sum();
    assert_eq!(total, 12);
    // 主线程手里的 Arc 依然有效
    assert_eq!(shared.len(), 3);
}
```

### 编译期断言与 `unsafe impl`

```rust
use std::rc::Rc;
use std::sync::{Arc, Mutex};

// 只有 T: Send 时这个函数才能被实例化，用来做编译期断言
fn assert_send<T: Send>() {}

// 裸指针本身不是 Send，包一层也不行；必须手动声明
struct Handle(*mut u8);

// SAFETY: 真实代码必须论证「这块内存独占且不会跨线程并发访问」，
// 这里只为演示语法，不加论证的 unsafe impl 就是数据竞争隐患
unsafe impl Send for Handle {}

fn main() {
    assert_send::<i32>();
    assert_send::<String>();
    assert_send::<Vec<String>>();
    assert_send::<Arc<Mutex<Vec<u8>>>>();
    assert_send::<Handle>();

    // 下面两行取消注释就会编译失败，说明它们不是 Send：
    // assert_send::<Rc<i32>>();
    // assert_send::<*const i32>();
}
```

## 常见陷阱

1. **`unsafe impl Send` 是义务不是开关**：编译器不再替你检查，类型里只要有一个非同步的可变状态，写错就是数据竞争——而且往往在线上偶发崩，测试很难抓到。
2. **自动推导看的是字段**：结构体里藏一个 `Rc` 字段，整个结构体都不是 `Send`，错误常常到 `thread::spawn` 处才暴露。
3. **把 `Send` 当 `Sync`**：`Cell<T>` 是 `Send`（能搬走）但不是 `Sync`（不能共享引用），两者不能互换。
4. **`Send` 与 `'static` 混为一谈**：`spawn` 要求的是 `Send + 'static`，短生命周期的引用即使 `Send` 也进不了线程。
5. **`MutexGuard` 不是 `Send`**：锁守卫不能跨线程，跨 `.await` 持有会让整个 future 失去 `Send`。
6. **为了消错随手 `unsafe impl`**：先想清楚真正的制约——多数情况该换 `Arc`、加 `Mutex`，或者把数据 `clone` 一份。

## 相关

- [[marker.Sync|Sync]]：共享引用的对应标记特质。
- [[sync.Arc|Arc]]：以原子计数换取 `Send + Sync` 的共享指针。
- [[rc.Rc|Rc]]：单线程引用计数，`Send` 的经典反例。
- [[thread.spawn|spawn]]：`F: FnOnce + Send + 'static` 的实际调用点。
- [[sync.Mutex|Mutex]]：把 `!Sync` 的内部可变状态变成可共享。
- [[21-并发编程|并发编程]]：线程、共享与同步的整体图景。
- [[marker|std::marker 模块]]：`Sized`、`Send`、`Sync` 等标记特质。
