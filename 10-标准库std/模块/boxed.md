---
title: "std::boxed"
type: std-模块
module: boxed
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - boxed
一句话: 堆分配指针 `Box<T>` 及其配套类型，提供最简单的唯一所有权堆装箱。
---

# std::boxed

> [!abstract] 一句话
> `std::boxed` 就是 `Box<T>` 的家：把值放到堆上、栈上只留一个指针，离开作用域时自动析构并释放内存。

## 模块简介

`Box<T>` 是 Rust 里最简单的堆分配形式：`Box::new(v)` 把 `v` 搬到堆上，栈上的 `Box` 只是一个指针；`Box` 唯一拥有那块内存，所以不需要引用计数，`Drop` 时直接释放。它保证不会申请超过 `isize::MAX` 字节的内存，这一点比手写 `alloc` 省心。

它的三个高频用途：一是**递归类型**，`enum List { Cons(i32, Box<List>) }` 之所以能编译，就是因为 `Box` 把无限大小变成了固定大小的指针；二是**大对象搬家**，把几百 KB 的结构体装进 `Box`，避免在栈上反复复制、也避免函数返回时的大块 memcpy；三是**trait 对象**，`Box<dyn Error>`、`Box<dyn Fn()>` 是最常见的动态分发容器，所有权仍然唯一。

它和 [[rc|std::rc]]、[[sync|std::sync]] 里的 `Arc` 构成一组：`Box` 独占、`Rc` 单线程共享、`Arc` 多线程共享。模块里另外两个条目是配套设施——`ThinBox` 是更薄的装箱指针，`BoxedArrayIntoIter` 是 `Box<[T; N]>` 的按值迭代器。日常最常用的仍然是 `Box` 本身加上 `Deref` 带来的自动解引用。

## 快速上手

```rust
use std::boxed::Box;

// 递归类型必须借助 Box 才能在编译期确定大小
enum List {
    Cons(i32, Box<List>),
    Nil,
}

fn main() {
    // 最简单的一次堆分配：值搬到堆上，栈上只留指针
    let boxed = Box::new(5i32);
    assert_eq!(*boxed, 5);

    // 解引用把值移回栈上，原来的 Box 随之失效
    let moved = *boxed;
    assert_eq!(moved, 5);

    let list = List::Cons(1, Box::new(List::Cons(2, Box::new(List::Nil))));
    let mut sum = 0;
    let mut cur = &list;
    while let List::Cons(value, next) = cur {
        sum += value;
        cur = next;
    }
    assert_eq!(sum, 3);

    // 大数组装箱，避免整个数组在栈上搬来搬去
    let buffer: Box<[i32; 1024]> = Box::new([0; 1024]);
    println!("{moved} / {sum} / 缓冲区长 {}", buffer.len());
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[boxed.Box|Box]] | 唯一拥有堆分配的指针类型，析构时自动释放。 |
| `Box::new` | 把值从栈搬到堆上，返回 `Box<T>`。 |
| `Box::into_raw` / `Box::from_raw` | 与裸指针互转，用于 FFI，需要 `unsafe`。 |
| `Box::leak` | 泄漏装箱，得到 `&'static mut T`。 |
| `Box::pin` | 装箱并得到 `Pin<Box<T>>`，异步与自引用结构常用。 |
| `Box<dyn Trait>` | 独占所有权的 trait 对象，实现动态分发。 |
| `Box<[T]>` | 定长堆切片，指针 + 长度的胖指针，比 `Vec` 少一个字段。 |
| `Deref` / `Drop` | 自动解引用到 `T`，作用域结束时释放堆内存。 |
| `ThinBox` | 更薄的装箱指针，减少指针宽度带来的额外开销。 |
| `BoxedArrayIntoIter` | `Box<[T; N]>` 的按值迭代器。 |

## 注意事项

> [!warning] `*b` 会把值移出去
> 对 `Box<T>` 解引用得到的 `T` 会被移回栈上（`Box` 特例支持这种移出），此后这个 `Box` 就不能再用了；如果 `T` 是 `Copy`，则只是复制一份，`Box` 仍然有效。

> [!danger] 递归类型不装箱就是编译错误
> 直接写 `enum List { Cons(i32, List) }` 会因为「大小无限」被编译器拒绝。`Box<List>` 把递归字段换成固定大小的指针，这才是递归数据结构的正解。

> [!tip] 大小开销
> `Box<T>` 只占一个指针的宽度，没有 `Vec`/`String` 那样的容量字段；`Box<[T]>` 是「指针 + 长度」的胖指针，仍比 `Vec<T>` 省一个字段。把 `Vec` 用 `into_boxed_slice()` 收紧，能省内存也更明确表达「长度不再变」。

## 相关

- [[模块索引]]
- [[alloc|std::alloc 模块]]：`Box` 底下的分配原语。
- [[rc|std::rc 模块]]：需要共享所有权时的单线程方案。
- [[sync|std::sync 模块]]：`Arc` 用于多线程共享。
- [[20-智能指针|智能指针]]：`Box`、`Rc`、`RefCell` 的对比。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 3 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [[boxed.Box|`Box`]]
- [`BoxedArrayIntoIter`](https://doc.rust-lang.org/std/boxed/struct.BoxedArrayIntoIter.html)
- [`ThinBox`](https://doc.rust-lang.org/std/boxed/struct.ThinBox.html)

<!-- END AUTO ITEMS -->
