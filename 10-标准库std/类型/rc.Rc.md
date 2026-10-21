---
title: "std::rc::Rc"
type: std-条目
kind: 结构体
module: rc
slug: rc.Rc
stable: "1.0.0"
tags:
  - std/类型
aliases:
  - Rc
一句话: 单线程引用计数指针，clone 只把计数加一，多个所有者共享同一份堆数据，计数归零才释放。
---

# `Rc`

> [!abstract] 一句话
> `Rc<T>` 提供**单线程**的共享所有权：`clone` 一次只是把引用计数加一，所有 `Rc` 指向同一块堆内存，最后一个销毁时内部值才被 drop。

## 简介

`Rc` 是 `Reference Counted` 的缩写。它解决的是「同一份数据、多个所有者」的问题：[[boxed.Box|Box]] 只能有一个主人，想让两处代码都持有同一个值，要么克隆数据（浪费），要么用 `Rc` 共享（零拷贝）。典型场景是图、树的多个父节点指向同一个子节点、观察者列表，以及多个结构体共享同一份只读配置。

`Rc` 的计数是**非原子**的普通整数，所以它只能在单线程内使用：`Rc<T>` 既不实现 `Send` 也不实现 `Sync`，把它 move 进 [[thread|std::thread]] 会被编译器拒绝。多线程共享请换 [[sync.Arc|Arc]]，语义一模一样，代价是每次 clone 一次原子操作。

`Rc` 默认也是**只读**的：拿不到 `&mut T`。需要修改时套一层 [[cell.RefCell|RefCell]]（`Rc<RefCell<T>>`，常见于双向链表、图），或在独占时用 `Rc::get_mut` / `Rc::make_mut`。注意 `Rc` 的所有固有方法都是**关联函数**而不是方法，必须写成 `Rc::get_mut(&mut value)`，这样可以避免和内部类型 `T` 的同名方法冲突。

```rust
use std::rc::Rc;

fn main() {
    let a = Rc::new(vec![1, 2, 3]);
    assert_eq!(Rc::strong_count(&a), 1);

    // clone 只加计数，不复制 Vec
    let b = Rc::clone(&a);
    assert_eq!(Rc::strong_count(&a), 2);
    assert!(Rc::ptr_eq(&a, &b));

    drop(b);
    assert_eq!(Rc::strong_count(&a), 1);
    println!("内容 = {:?}", *a);
}
```

## 常用方法

### 构造

| 方法 | 说明 |
| --- | --- |
| `new(value)` | 在堆上分配并创建新的 `Rc<T>`。 |
| `new_cyclic(data_fn)` | 构造自引用的 `Rc`，回调里拿到指向自己的 `Weak`。 |
| `new_uninit()` | 创建内容未初始化的 `Rc<MaybeUninit<T>>`。 |
| `new_zeroed()` | 创建内容按零字节填充的 `Rc<MaybeUninit<T>>`。 |
| `pin(value)` | 创建 `Pin<Rc<T>>`，`T` 不可 `Unpin` 时被钉住。 |
| `new_uninit_slice(len)` | 创建长度为 `len` 的未初始化共享切片。 |
| `new_zeroed_slice(len)` | 创建长度为 `len` 的零填充共享切片。 |

### 初始化与向下转型

| 方法 | 说明 |
| --- | --- |
| `assume_init(self)` | 转成 `Rc<T>`，调用者保证已初始化。 |
| `assume_init(self)` | 转成 `Rc<[T]>`，调用者保证已初始化。 |
| `downcast<T>(self)` | 转成具体类型 `T`，用于 `dyn Any` 装箱。 |

### 引用计数与弱引用

| 方法 | 说明 |
| --- | --- |
| `strong_count(this)` | 返回当前强引用（`Rc`）的个数。 |
| `weak_count(this)` | 返回当前弱引用（`Weak`）的个数。 |
| `downgrade(this)` | 创建指向同一分配的 `Weak` 弱引用。 |
| `ptr_eq(this, other)` | 判断两个 `Rc` 是否指向同一分配。 |

### 取出与修改内部值

| 方法 | 说明 |
| --- | --- |
| `try_unwrap(this)` | 只剩一个强引用时取回内部值，否则返还 `Rc`。 |
| `into_inner(this)` | 只剩一个强引用时取回内部值，否则返回 `None`。 |
| `unwrap_or_clone(this)` | 唯一引用就取出，否则克隆一份返回。 |
| `get_mut(this)` | 无其他强/弱引用时给出 `&mut T`。 |
| `make_mut(this)` | 给出 `&mut T`，需要时先克隆（写时复制）。 |

### 裸指针

| 方法 | 说明 |
| --- | --- |
| `into_raw(this)` | 消耗 `Rc`，返回裸指针且不减少计数。 |
| `from_raw(ptr)` | 从 `into_raw` 得到的裸指针重建 `Rc`。 |
| `as_ptr(this)` | 返回指向数据的裸指针，不改变计数。 |
| `increment_strong_count(ptr)` | 增加指针所属分配的强引用计数。 |
| `decrement_strong_count(ptr)` | 减少指针所属分配的强引用计数。 |

## 示例

`Rc` 自身不做借用检查，真正的「运行时借用检查 panic」出现在 `Rc<RefCell<T>>` 这种组合里：

```rust
use std::cell::RefCell;
use std::rc::Rc;

fn main() {
    let shared = Rc::new(RefCell::new(vec![1, 2, 3]));

    let a = Rc::clone(&shared);
    let mut first = a.borrow_mut();
    first.push(4);

    // 已有可变借用时，任何新借用都会被运行时检查拒绝
    let b = Rc::clone(&shared);
    assert!(b.try_borrow().is_err());
    assert!(b.try_borrow_mut().is_err());

    drop(first);
    b.borrow_mut().push(5);
    assert_eq!(*shared.borrow(), vec![1, 2, 3, 4, 5]);

    // 若这里直接写 shared.borrow()，运行时会 panic：already mutably borrowed
    let guard = shared.borrow_mut();
    let caught = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        let _ = shared.borrow();
    }));
    assert!(caught.is_err());
    drop(guard);

    // 不想 panic 就用 try_borrow / try_borrow_mut
    assert!(shared.try_borrow().is_ok());
    println!("最终内容 = {:?}", shared.borrow());
}
```

## 常见陷阱

1. **多线程用 `Rc`**：`Rc` 不是 `Send`，编译器会直接报错；跨线程共享用 [[sync.Arc|Arc]]。
2. **循环引用**：两个 `Rc` 互相持有，计数永不归零导致内存泄漏；让其中一方用 `Weak`。
3. **以为 `Rc` 可写**：默认拿不到 `&mut T`，要改内容套 [[cell.RefCell|RefCell]]，或独占时用 `get_mut` / `make_mut`。
4. **`Rc<RefCell<T>>` 里忘记 drop 守卫**：守卫存活期间再 borrow 会 panic，甚至只是 `borrow()` 也会；把守卫作用域缩到最小。
5. **写成 `value.get_mut()`**：`Rc` 的固有方法都是关联函数，正确写法是 `Rc::get_mut(&mut value)`。

## 相关

- [[rc|std::rc 模块]]：本模块全部条目。
- [[sync.Arc|Arc]]：线程安全版本，语义相同、计数改为原子操作。
- [[cell.RefCell|RefCell]]：与 `Rc` 组合实现「共享 + 可变」。
- [[cell.Cell|Cell]]：不需要引用、只做整体替换时的更轻选择。
- [[20-智能指针|智能指针]]：`Box` / `Rc` / `Arc` / `Weak` 的整体脉络。
