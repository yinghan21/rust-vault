---
title: "std::sync::Arc"
type: std-条目
kind: 结构体
module: sync
slug: sync.Arc
stable: "1.0.0"
tags:
  - std/类型
  - std/并发
aliases:
  - Arc
一句话: 线程安全的引用计数指针（Atomically Reference Counted），clone 只加计数，最后一个指针销毁时释放堆上的值。
---

# `Arc`

> [!abstract] 一句话
> `Arc<T>` 把值放在堆上，用**原子**引用计数实现共享所有权：`clone` 只是把计数加一，所有副本指向同一块内存，计数归零时才 drop 内部值。

## 简介

`Arc` 是 `Atomically Reference Counted` 的缩写，语义与单线程的 [[rc.Rc|Rc]] 完全一致，区别只在于计数用原子操作维护，因此 `Arc<T>` 在 `T: Send + Sync` 时是 `Send + Sync`，可以 `clone` 之后 move 进 [[thread|std::thread]] 的闭包。`Arc` 自己负责「谁还活着」，内部的 `T` 仍然遵守借用规则：默认你拿不到 `&mut T`。

想通过 `Arc` 修改数据有三条路：外面套 [[sync.Mutex|Mutex]] 或 [[sync.RwLock|RwLock]]（`Arc<Mutex<T>>` 是最常见的共享可变状态写法）、用原子类型（`Arc<AtomicUsize>`）、或者用 `Arc::make_mut` / `get_mut` 做「写时复制」——只有当没有别的强引用时才原地改，否则先克隆一份。

`Arc` 用两个计数：强引用计数（`Arc` 本身）和弱引用计数（`Weak`）。`Arc::downgrade` 产生 `Weak`，它不阻止值被释放，`Weak::upgrade` 在值已释放时返回 `None`，这是打破双向链表、父子节点循环引用的标准手段。另外 `Arc` 在等号左边的 `clone` 是原子自增，热点路径上频繁 clone 是真实开销，能借用就别 clone。

```rust
use std::sync::Arc;
use std::thread;

fn main() {
    let data = Arc::new(vec![1, 2, 3]);

    // clone 只复制指针并做一次原子自增，堆上的 Vec 不复制
    let shared = Arc::clone(&data);
    let handle = thread::spawn(move || shared.iter().sum::<i32>());

    // 子线程持有一份时，主线程照样能用
    assert_eq!(data.iter().sum::<i32>(), 6);
    assert_eq!(handle.join().unwrap(), 6);
    assert_eq!(Arc::strong_count(&data), 1);
    println!("内容 = {:?}", *data);
}
```

## 常用方法

### 构造

| 方法 | 说明 |
| --- | --- |
| `new(data)` | 在堆上分配并创建新的 `Arc<T>`。 |
| `new_cyclic(data_fn)` | 构造自引用的 `Arc`，回调里拿到指向自己的 `Weak`。 |
| `new_uninit()` | 创建内容未初始化的 `Arc<MaybeUninit<T>>`。 |
| `new_zeroed()` | 创建内容按零字节填充的 `Arc<MaybeUninit<T>>`。 |
| `pin(data)` | 创建 `Pin<Arc<T>>`，`T` 不可 `Unpin` 时被钉住。 |
| `new_uninit_slice(len)` | 创建长度为 `len` 的未初始化共享切片。 |
| `new_zeroed_slice(len)` | 创建长度为 `len` 的零填充共享切片。 |

### 初始化与向下转型

| 方法 | 说明 |
| --- | --- |
| `assume_init(self)` | 转成 `Arc<T>`，调用者保证已初始化。 |
| `assume_init(self)` | 转成 `Arc<[T]>`，调用者保证已初始化。 |
| `downcast<T>(self)` | 转成具体类型 `T`，用于 `Any + Send + Sync`。 |

### 引用计数与弱引用

| 方法 | 说明 |
| --- | --- |
| `strong_count(this)` | 返回当前强引用（`Arc`）的个数。 |
| `weak_count(this)` | 返回当前弱引用（`Weak`）的个数。 |
| `downgrade(this)` | 创建指向同一分配的 `Weak` 弱引用。 |
| `ptr_eq(this, other)` | 判断两个 `Arc` 是否指向同一分配。 |

### 取出与修改内部值

| 方法 | 说明 |
| --- | --- |
| `try_unwrap(this)` | 只剩一个强引用时取回内部值，否则返还 `Arc`。 |
| `into_inner(this)` | 只剩一个强引用时取回内部值，否则返回 `None`。 |
| `unwrap_or_clone(this)` | 唯一引用就取出，否则克隆一份返回。 |
| `get_mut(this)` | 无其他强/弱引用时给出 `&mut T`。 |
| `make_mut(this)` | 给出 `&mut T`，需要时先克隆（写时复制）。 |

### 裸指针

| 方法 | 说明 |
| --- | --- |
| `into_raw(this)` | 消耗 `Arc`，返回裸指针且不减少计数。 |
| `from_raw(ptr)` | 从 `into_raw` 得到的裸指针重建 `Arc`。 |
| `as_ptr(this)` | 返回指向数据的裸指针，不改变计数。 |
| `increment_strong_count(ptr)` | 增加指针所属分配的强引用计数。 |
| `decrement_strong_count(ptr)` | 减少指针所属分配的强引用计数。 |

> [!warning] 裸指针那一组必须成对使用且都是 `unsafe`
> `into_raw` 之后引用计数不会自动归还，只调用 `from_raw` 一次才能抵消；`increment_strong_count` / `decrement_strong_count` 少配一次就是泄漏或提前释放，属于未定义行为。

## 示例

```rust
use std::sync::Arc;

fn main() {
    let mut a = Arc::new(vec![1, 2, 3]);
    let b = Arc::clone(&a);

    // 还有别的强引用时，get_mut 拿不到可变引用
    assert!(Arc::get_mut(&mut a).is_none());
    // make_mut 走写时复制：克隆一份再返回可变引用
    Arc::make_mut(&mut a).push(4);
    assert_eq!(*a, vec![1, 2, 3, 4]);
    assert_eq!(*b, vec![1, 2, 3]); // b 仍指向旧数据

    // 弱引用不阻止释放
    let weak = Arc::downgrade(&b);
    assert_eq!(Arc::strong_count(&b), 1);
    assert_eq!(Arc::weak_count(&b), 1);
    assert_eq!(*weak.upgrade().unwrap(), vec![1, 2, 3]);
    drop(b);
    assert!(weak.upgrade().is_none());

    // 只剩一个强引用，try_unwrap 取回内部值
    assert_eq!(Arc::try_unwrap(a).unwrap(), vec![1, 2, 3, 4]);

    // 没有弱引用干扰时 into_inner 也能取回
    let solo = Arc::new(String::from("唯一"));
    assert_eq!(Arc::into_inner(solo).unwrap(), "唯一");
}
```

## 常见陷阱

1. **以为 `Arc` 能改内容**：它只解决「共享所有权」，要改数据得配 `Mutex` / `RwLock` / 原子类型，或用 `make_mut` 走写时复制。
2. **循环引用**：两个 `Arc` 互相指向，强引用计数永远不归零，内存永不释放；让其中一方持有 `Weak`。
3. **在热点路径反复 clone**：每次 clone 是一次原子操作，能传 `&Arc<T>` 或借用内部数据时别 clone。
4. **`Arc<Rc<T>>` 这类混搭**：`Rc` 不是线程安全的，整个类型因此不能跨线程，编译器会拦住，不要用 `unsafe impl` 强行绕过。
5. **`try_unwrap` / `get_mut` 失败**：只要存在任何 `Weak` 也不成功，因为弱引用随时可能 upgrade；想独占就先确保计数都是 1。

## 相关

- [[sync|std::sync 模块]]：本模块全部条目。
- [[rc.Rc|Rc]]：单线程版本的引用计数指针。
- [[sync.Mutex|Mutex]]：`Arc<Mutex<T>>` 是共享可变状态的标准组合。
- [[sync.RwLock|RwLock]]：读多写少时替代 `Mutex`。
- [[20-智能指针|智能指针]]：`Box` / `Rc` / `Arc` 的取舍与实现原理。
