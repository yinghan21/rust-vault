---
title: "std::marker"
type: std-模块
module: marker
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - marker
一句话: "标记特质与零大小标记类型：Copy、Send、Sync、Sized、Unpin 与 PhantomData。"
---

# std::marker

> [!abstract] 一句话
> `std::marker` 用「没有方法的特质」描述类型的内在属性——能不能复制、能不能跨线程、大小是否已知、能不能移动——并用零大小类型把这个信息带进泛型。

## 模块简介

这个模块里的特质几乎没有方法，它们的作用是**声明**而非「调用」。编译器看到 `T: Copy` 就知道赋值可以直接复制位模式，看到 `T: Send` 就允许把值移进另一个线程，看到 `T: Sized` 才允许在栈上按固定大小分配。这些属性大多数由编译器自动推导，所以你平时不需要写它们，只需要读懂它们。

三类特质要分清。**自动特质** `Send`、`Sync`、`Unpin` 由编译器按字段逐个推导：所有字段都满足，类型就满足。**手工特质** `Copy` 是显式声明的，而且必须先实现 `Clone`、并且不能实现 `Drop`。**边界特质** `Sized` 是所有泛型参数的默认约束，用 `?Sized` 可以放宽，从而接受 `str`、`[T]`、`dyn Trait` 这些编译期大小未知的类型。

零大小标记类型解决的是「泛型参数没被用到」的问题。`PhantomData<T>` 不占空间，却告诉编译器「这个类型逻辑上拥有一个 `T`」：自动特质的推导、drop check、以及协变/逆变都按 `T` 来算，这正是 `struct Handle<T> { id: u32, _marker: PhantomData<T> }` 的用途。`PhantomPinned` 则相反，它让类型**不**实现 `Unpin`，是自引用结构（异步状态机就是典型）的必备记号。

## 快速上手

```rust
use std::marker::{PhantomData, PhantomPinned};

#[derive(Clone, Copy, Debug, PartialEq)]
struct Point {
    x: i32,
    y: i32,
}

// 逻辑上「拥有」一个 T，但不需要真的存一个 T
struct Handle<T> {
    id: u32,
    _marker: PhantomData<T>,
}

fn assert_send<T: Send>() {}
fn assert_send_sync<T: Send + Sync>() {}

fn main() {
    // Copy：赋值是复制，原值仍然可用
    let p = Point { x: 1, y: 2 };
    let q = p;
    assert_eq!(p, q);
    assert_eq!(q.x, 1);

    // PhantomData 让 Handle<T> 的自动特质跟随 T
    assert_send::<Handle<i32>>();
    assert_send_sync::<Handle<i32>>();

    let h: Handle<i32> = Handle { id: 7, _marker: PhantomData };
    assert_eq!(h.id, 7);

    // PhantomData 本身是零大小类型，无论 T 多大
    assert_eq!(std::mem::size_of::<PhantomData<[u8; 4096]>>(), 0);

    // PhantomPinned 让包含它的类型不再实现 Unpin
    let _pinned = PhantomPinned;

    // std::rc::Rc 不是 Send：下面这行去掉注释就编译不过
    // assert_send::<std::rc::Rc<i32>>();
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[marker.Copy\|Copy]] | 逐位复制，赋值不移动，需同时实现 `Clone`。 |
| [[marker.Send\|Send]] | 值可以跨线程转移所有权。 |
| [[marker.Sync\|Sync]] | `&T` 可以跨线程共享。 |
| `marker::Sized` | 编译期已知大小，泛型参数的默认约束。 |
| `marker::Unpin` | 不依赖固定地址，可自由移动。 |
| `marker::PhantomData` | 零大小标记，声明逻辑上拥有 `T`。 |
| `marker::PhantomPinned` | 主动让类型不实现 `Unpin`。 |
| `#[derive(Copy, Clone)]` | 为小类型生成复制语义。 |
| `?Sized` 约束 | 放宽泛型，接受 `str`、`[T]`、`dyn Trait`。 |
| `unsafe impl Send for X` | 手动承诺线程安全，仅在确有依据时使用。 |

## 注意事项

> [!warning] `Copy` 与 `Drop` 互斥
> 实现了 `Drop` 的类型不能同时实现 `Copy`，否则一个值可能被析构多次。需要「复制 + 清理」时，把资源交给内部的 `Rc`/`Arc` 或手动 `clone`。

> [!danger] 手写 `unsafe impl Send/Sync` 是向编译器作担保
> 编译器不会验证你的承诺。`Rc`、`Cell`、`*const T` 这些天然不线程安全的类型，只有在能证明其内部访问已被锁或独占时才能这样做；否则等待你的是数据竞争而非编译错误。

> [!tip] `PhantomData<T>` 与 `PhantomData<*const T>` 语义不同
> 前者让类型表现得「拥有 `T`」，自动特质与 drop check 都跟随 `T`；后者让类型表现得「持有裸指针」，既不 `Send` 也不 `Sync`，也不会被当作拥有者。按你想表达的所有权关系选。

## 相关

- [[sync|std::sync]]：`Arc`、`Mutex` 依赖 `Send`/`Sync` 约束。
- [[rc|std::rc]]：`Rc` 是典型的非 `Send` 类型。
- [[cell|std::cell]]：`Cell`/`RefCell` 是非 `Sync` 的内部可变性。
- [[21-并发编程|并发编程]]：`Send`/`Sync` 如何决定线程边界。
- [[24-unsafe 与 FFI|unsafe 与 FFI]]：`unsafe impl` 的适用场景与风险。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 33 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`PhantomData`](https://doc.rust-lang.org/std/marker/struct.PhantomData.html)
- [`PhantomPinned`](https://doc.rust-lang.org/std/marker/struct.PhantomPinned.html)
- [`PhantomContravariant`](https://doc.rust-lang.org/std/marker/struct.PhantomContravariant.html)
- [`PhantomContravariantLifetime`](https://doc.rust-lang.org/std/marker/struct.PhantomContravariantLifetime.html)
- [`PhantomCovariant`](https://doc.rust-lang.org/std/marker/struct.PhantomCovariant.html)
- [`PhantomCovariantLifetime`](https://doc.rust-lang.org/std/marker/struct.PhantomCovariantLifetime.html)
- [`PhantomInvariant`](https://doc.rust-lang.org/std/marker/struct.PhantomInvariant.html)
- [`PhantomInvariantLifetime`](https://doc.rust-lang.org/std/marker/struct.PhantomInvariantLifetime.html)

### 特质

- [[marker.Copy|`Copy`]]
- [[marker.Send|`Send`]]
- [`Sized`](https://doc.rust-lang.org/std/marker/trait.Sized.html)
- [[marker.Sync|`Sync`]]
- [`Unpin`](https://doc.rust-lang.org/std/marker/trait.Unpin.html)
- [`CoerceShared`](https://doc.rust-lang.org/std/marker/trait.CoerceShared.html)
- [`ConstParamTy_`](https://doc.rust-lang.org/std/marker/trait.ConstParamTy_.html)
- [`Destruct`](https://doc.rust-lang.org/std/marker/trait.Destruct.html)
- [`DiscriminantKind`](https://doc.rust-lang.org/std/marker/trait.DiscriminantKind.html)
- [`FnPtr`](https://doc.rust-lang.org/std/marker/trait.FnPtr.html)
- [`Freeze`](https://doc.rust-lang.org/std/marker/trait.Freeze.html)
- [`MetaSized`](https://doc.rust-lang.org/std/marker/trait.MetaSized.html)
- [`PointeeSized`](https://doc.rust-lang.org/std/marker/trait.PointeeSized.html)
- [`Reborrow`](https://doc.rust-lang.org/std/marker/trait.Reborrow.html)
- [`StructuralPartialEq`](https://doc.rust-lang.org/std/marker/trait.StructuralPartialEq.html)
- [`Tuple`](https://doc.rust-lang.org/std/marker/trait.Tuple.html)
- [`UnsafeUnpin`](https://doc.rust-lang.org/std/marker/trait.UnsafeUnpin.html)
- [`Unsize`](https://doc.rust-lang.org/std/marker/trait.Unsize.html)
- [`Variance`](https://doc.rust-lang.org/std/marker/trait.Variance.html)

### 函数

- [`variance`](https://doc.rust-lang.org/std/marker/fn.variance.html)

### 其他

- [[marker.Copy|`Copy`]]
- [`CoercePointee`](https://doc.rust-lang.org/std/marker/derive.CoercePointee.html)
- [`CoerceShared`](https://doc.rust-lang.org/std/marker/derive.CoerceShared.html)
- [`ConstParamTy`](https://doc.rust-lang.org/std/marker/derive.ConstParamTy.html)
- [`Reborrow`](https://doc.rust-lang.org/std/marker/derive.Reborrow.html)

<!-- END AUTO ITEMS -->
