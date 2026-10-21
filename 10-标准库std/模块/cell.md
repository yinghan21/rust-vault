---
title: "std::cell"
type: std-模块
module: cell
stable: "1.0.0"
unstable: false
tags:
  - std/模块
  - std/特质
aliases:
  - cell
  - 内部可变性
一句话: 单线程下的内部可变性：通过共享引用修改数据，把借用检查从编译期推迟到运行期。
---

# std::cell

> [!abstract] 一句话
> `std::cell` 提供可共享的可变容器——`Cell<T>`、`RefCell<T>`、`OnceCell<T>`，让「多个引用 + 修改」在单线程中合法。

## 模块简介

Rust 的借用规则要求：同一个值要么有多个不可变引用，要么只有一个可变引用。这条规则由编译器强制执行，但有些数据结构（图、树、缓存、回调）天然需要「拿着 `&self` 也要改内部状态」。`std::cell` 就是为这种场景准备的受控例外，通称**内部可变性**（interior mutability）。

三种核心容器各有取舍：

- `Cell<T>`：只能整体 `get` / `set` / `replace`，没有借用守卫，零运行时开销，但只适合 `Copy` 类型。
- `RefCell<T>`：`borrow` / `borrow_mut` 在运行期检查借用规则，违反时 panic（或用 `try_borrow` 拿到错误），适合非 `Copy` 类型。
- `OnceCell<T>`：只能写入一次，之后只读，常用于延迟初始化。

这些类型都**不实现 `Sync`**，所以不能跨线程共享。多线程下需要的是 [[sync.Mutex|Mutex]]、[[sync.RwLock|RwLock]]、`OnceLock` 或原子类型——这是选择模块时的第一判据。

最常见的组合是与 [[rc|std::rc]] 搭配：`Rc<RefCell<T>>` 让多个所有者共享一份可变数据，代价是运行时借用检查。

## 快速上手

```rust
use std::cell::{Cell, RefCell};

fn main() {
    // Cell：无需借用，直接读写 Copy 值
    let counter = Cell::new(0);
    counter.set(counter.get() + 1);
    assert_eq!(counter.get(), 1);

    // replace 取出旧值，同时写入新值
    let old = counter.replace(10);
    assert_eq!(old, 1);
    assert_eq!(counter.get(), 10);

    // RefCell：运行时借用检查，可对 &self 的内部数据做可变修改
    let logs = RefCell::new(Vec::new());
    logs.borrow_mut().push("第一条");
    logs.borrow_mut().push("第二条");
    assert_eq!(logs.borrow().len(), 2);

    // 多个不可变借用可以同时存在
    let a = logs.borrow();
    let b = logs.borrow();
    assert_eq!(a.len(), b.len());

    // 已经不可变借用时，再借可变只能失败，而不是 UB
    assert!(logs.try_borrow_mut().is_err());
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[cell.Cell|Cell]] | 可变内存位置，`get`/`set` 直接读写，适合 `Copy` 类型。 |
| [[cell.RefCell|RefCell]] | 运行时检查借用规则的容器，`borrow`/`borrow_mut` 返回守卫。 |
| `cell::Ref` | `RefCell::borrow` 返回的不可变借用守卫，离开作用域自动释放。 |
| `cell::RefMut` | `RefCell::borrow_mut` 返回的可变借用守卫。 |
| `cell::BorrowError` | `try_borrow` 在已被可变借用时返回的错误。 |
| `cell::BorrowMutError` | `try_borrow_mut` 在已有借用时返回的错误。 |
| `cell::UnsafeCell` | 内部可变性的底层原语，解引用需要 `unsafe`。 |
| `cell::OnceCell` | 只能写入一次、之后只读的单元。 |
| `Cell::replace` | 写入新值并返回旧值。 |
| `Cell::take` | 取出值，在原地留下 `T::default()`。 |
| `RefCell::try_borrow` | 不 panic 的借用检查，失败时返回 `BorrowError`。 |
| `RefCell::borrow_mut` | 取得可变借用，已有借用时 panic。 |
| `RefCell::into_inner` | 消耗 `RefCell`，取回内部值。 |

## 注意事项

> [!warning] 它们都不是 `Sync`
> `Cell` / `RefCell` / `UnsafeCell` 不能跨线程共享，放进 `thread::spawn` 会直接编译失败。多线程场景请用 `Mutex`、`RwLock`、`OnceLock` 或原子类型。

> [!danger] `borrow_mut` 会 panic
> `RefCell` 的借用冲突在运行时才暴露：已有 `borrow` 守卫存活时调用 `borrow_mut` 会 panic。不确定时用 `try_borrow_mut`，或缩小守卫的作用域（用完立刻 `drop`）。

> [!tip] `Cell` 比 `RefCell` 便宜
> `Cell` 只做值替换，没有借用计数和守卫；只有确实需要「借用期间持续访问」时才用 `RefCell`。`Rc<RefCell<T>>` 很方便，但每次借用都有运行时检查开销。

## 相关

- [[cell.Cell|Cell]] 与 [[cell.RefCell|RefCell]]：两个最常用的容器。
- [[sync|std::sync 模块]]：多线程下的同类工具 `Mutex`、`RwLock`、`OnceLock`。
- [[rc|std::rc 模块]]：`Rc<RefCell<T>>` 是共享可变数据的经典组合。
- [[borrow|std::borrow 模块]]：`Borrow` / `BorrowMut` 与借用语义。
- [[20-智能指针|智能指针]]：运行时借用检查与内部可变性的完整讲解。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 12 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`BorrowError`](https://doc.rust-lang.org/std/cell/struct.BorrowError.html)
- [`BorrowMutError`](https://doc.rust-lang.org/std/cell/struct.BorrowMutError.html)
- [[cell.Cell|`Cell`]]
- [`LazyCell`](https://doc.rust-lang.org/std/cell/struct.LazyCell.html)
- [`OnceCell`](https://doc.rust-lang.org/std/cell/struct.OnceCell.html)
- [`Ref`](https://doc.rust-lang.org/std/cell/struct.Ref.html)
- [[cell.RefCell|`RefCell`]]
- [`RefMut`](https://doc.rust-lang.org/std/cell/struct.RefMut.html)
- [`UnsafeCell`](https://doc.rust-lang.org/std/cell/struct.UnsafeCell.html)
- [`CovariantUnsafeCell`](https://doc.rust-lang.org/std/cell/struct.CovariantUnsafeCell.html)
- [`SyncUnsafeCell`](https://doc.rust-lang.org/std/cell/struct.SyncUnsafeCell.html)

### 特质

- [`CloneFromCell`](https://doc.rust-lang.org/std/cell/trait.CloneFromCell.html)

<!-- END AUTO ITEMS -->
