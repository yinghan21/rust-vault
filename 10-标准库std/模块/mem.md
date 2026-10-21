---
title: "std::mem"
type: std-模块
module: mem
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - mem
一句话: "值与内存的底层操作：swap/take/replace/drop、尺寸与对齐查询，以及 unsafe 内存原语。"
---

# std::mem

> [!abstract] 一句话
> `std::mem` 处理「值和内存本身」：交换、取出、替换、提前析构，以及类型大小、对齐、是否需要在 drop 时做事。

## 模块简介

日常 Rust 代码里，`std::mem` 最常被用到的就是四个函数：`swap`、`take`、`replace`、`drop`。它们解决的共同问题是「如何在只有 `&mut T` 的情况下改掉里面的值」。`mem::swap(&mut a, &mut b)` 交换两个位置的值，不需要临时变量；`mem::take(&mut x)` 把值取走、原地留下 `T::default()`；`mem::replace(&mut x, new)` 放入新值并返回旧值，不要求 `Default`；`mem::drop(v)` 显式结束一个值的生命周期、立刻触发析构。链表、树、状态机里那些「把字段拿出来用，再填回去」的写法，底层都是这三个函数。

第二族是布局查询：`size_of` / `size_of_val` / `align_of` / `align_of_val` / `needs_drop`。做内存估算、检查 FFI 结构体对齐、判断某类型 drop 是否有副作用时用它们。它们是编译期常量或廉价的运行时查询，不会产生实际分配。

第三族是 `unsafe` 的内存原语，只在极底层代码里出现：`MaybeUninit<T>` 表示「可能尚未初始化」的内存，`ManuallyDrop<T>` 抑制自动析构（用于自己管理释放时机），`forget` 泄漏一个值、`transmute` 把位模式重新解释成另一种类型、`zeroed` 生成全零值。这些函数如果误用会直接造成未定义行为，业务代码基本用不到。

## 快速上手

```rust
use std::mem;

#[derive(Default, Debug, PartialEq)]
struct Buffer {
    data: Vec<u8>,
    pos: usize,
}

fn main() {
    // swap：交换两个变量的值，不要求 T: Default
    let mut a = String::from("左");
    let mut b = String::from("右");
    mem::swap(&mut a, &mut b);
    assert_eq!((a.as_str(), b.as_str()), ("右", "左"));

    // take：取出值，原地留下 T::default()
    let mut buf = Buffer { data: vec![1, 2, 3], pos: 2 };
    let taken = mem::take(&mut buf);
    assert_eq!(taken.data, vec![1, 2, 3]);
    assert_eq!(buf, Buffer::default());

    // replace：放入新值并返回旧值，不要求 Default
    let mut buf = Buffer { data: vec![9], pos: 1 };
    let old = mem::replace(&mut buf, Buffer::default());
    assert_eq!(old.data, vec![9]);
    assert!(buf.data.is_empty());

    // drop：提前析构，之后该值不可再用
    let s = String::from("再见");
    mem::drop(s);
    // println!("{s}"); // 编译错误：s 已被移动

    // 尺寸、对齐与析构需求
    assert_eq!(mem::size_of::<u32>(), 4);
    assert_eq!(mem::size_of::<[u16; 4]>(), 8);
    assert_eq!(mem::align_of::<u64>(), 8);
    // Option<Box<T>> 利用空指针优化，与 Box<T> 同样大
    assert_eq!(mem::size_of::<Option<Box<u8>>>(), mem::size_of::<Box<u8>>());
    assert!(mem::needs_drop::<String>());
    assert!(!mem::needs_drop::<u32>());
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[mem.swap\|swap]] | 交换两个可变位置的值，不要求 `Default`。 |
| [[mem.take\|take]] | 取出值并用 `Default` 填回原位。 |
| [[mem.replace\|replace]] | 放入新值，返回被替换的旧值。 |
| [[mem.drop\|drop]] | 立即析构一个值，结束其生命周期。 |
| `mem::size_of` / `mem::align_of` | 类型的字节大小 / 对齐要求。 |
| `mem::size_of_val` / `mem::align_of_val` | 按值（可为切片）查询大小 / 对齐。 |
| `mem::needs_drop` | 判断类型在 drop 时是否有工作要做。 |
| `mem::forget` | 取走值但不运行析构，造成泄漏。 |
| `mem::ManuallyDrop` | 零成本地抑制自动析构。 |
| `mem::MaybeUninit` | 安全地持有可能未初始化的内存。 |
| `mem::discriminant` | 取枚举变体的判别值用于比较。 |
| `mem::transmute` | 把一种类型重解释为另一种（unsafe）。 |
| `mem::zeroed` | 生成全零字节模式的值（unsafe）。 |

## 注意事项

> [!tip] 没有 `Default` 就用 `replace`
> `take` 依赖 `T: Default`。如果类型没有合理默认值，别硬造一个，改用 `mem::replace(&mut x, placeholder)`，或用 `Option` 把字段包起来再 `take`——后者是「暂时无效」状态的标准写法。

> [!warning] `forget` 是安全的泄漏，不是错误
> `mem::forget(v)` 不会运行析构：`String` 的内存、`Rc` 的引用计数都会永久留下。这在需要 `'static` 生命周期或跳过 `Drop` 时有用，但会让资源泄漏，不要用它来「避免析构副作用」。

> [!danger] `transmute` 与 `zeroed` 极易写出 UB
> `transmute` 要求源与目标大小完全相同，并且目标类型必须对所有位模式都合法——`&T`、`Box<T>`、`NonZeroU32`、`bool` 都做不到。`zeroed` 同理。能用 `From`/`TryFrom`、`to_bits`/`from_bits` 就不要用它们。

## 相关

- [[05-所有权|所有权]]：移动语义与 `drop` 的时机。
- [[20-智能指针|智能指针]]：`Box`/`Rc` 的析构与计数。
- [[ptr|std::ptr]]：更底层的裸指针读写。
- [[alloc|std::alloc]]：手动分配器 API。
- [[24-unsafe 与 FFI|unsafe 与 FFI]]：`MaybeUninit`、`transmute` 的正确用法。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 34 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`Discriminant`](https://doc.rust-lang.org/std/mem/struct.Discriminant.html)
- [`ManuallyDrop`](https://doc.rust-lang.org/std/mem/struct.ManuallyDrop.html)
- [`Alignment`](https://doc.rust-lang.org/std/mem/struct.Alignment.html)
- [`Assume`](https://doc.rust-lang.org/std/mem/struct.Assume.html)
- [`DropGuard`](https://doc.rust-lang.org/std/mem/struct.DropGuard.html)
- [`MaybeDangling`](https://doc.rust-lang.org/std/mem/struct.MaybeDangling.html)

### 特质

- [`TransmuteFrom`](https://doc.rust-lang.org/std/mem/trait.TransmuteFrom.html)

### 函数

- [`align_of`](https://doc.rust-lang.org/std/mem/fn.align_of.html)
- [`align_of_val`](https://doc.rust-lang.org/std/mem/fn.align_of_val.html)
- [`align_of_val_raw`](https://doc.rust-lang.org/std/mem/fn.align_of_val_raw.html)
- [`discriminant`](https://doc.rust-lang.org/std/mem/fn.discriminant.html)
- [[mem.drop|`drop`]]
- [`forget`](https://doc.rust-lang.org/std/mem/fn.forget.html)
- [`min_align_of`](https://doc.rust-lang.org/std/mem/fn.min_align_of.html)
- [`min_align_of_val`](https://doc.rust-lang.org/std/mem/fn.min_align_of_val.html)
- [`needs_drop`](https://doc.rust-lang.org/std/mem/fn.needs_drop.html)
- [[mem.replace|`replace`]]
- [`size_of`](https://doc.rust-lang.org/std/mem/fn.size_of.html)
- [`size_of_val`](https://doc.rust-lang.org/std/mem/fn.size_of_val.html)
- [`size_of_val_raw`](https://doc.rust-lang.org/std/mem/fn.size_of_val_raw.html)
- [[mem.swap|`swap`]]
- [[mem.take|`take`]]
- [`transmute`](https://doc.rust-lang.org/std/mem/fn.transmute.html)
- [`transmute_copy`](https://doc.rust-lang.org/std/mem/fn.transmute_copy.html)
- [`uninitialized`](https://doc.rust-lang.org/std/mem/fn.uninitialized.html)
- [`zeroed`](https://doc.rust-lang.org/std/mem/fn.zeroed.html)
- [`conjure_zst`](https://doc.rust-lang.org/std/mem/fn.conjure_zst.html)
- [`copy`](https://doc.rust-lang.org/std/mem/fn.copy.html)
- [`forget_unsized`](https://doc.rust-lang.org/std/mem/fn.forget_unsized.html)
- [`transmute_neo`](https://doc.rust-lang.org/std/mem/fn.transmute_neo.html)
- [`transmute_prefix`](https://doc.rust-lang.org/std/mem/fn.transmute_prefix.html)
- [`variant_count`](https://doc.rust-lang.org/std/mem/fn.variant_count.html)

### 宏

- [`offset_of`](https://doc.rust-lang.org/std/mem/macro.offset_of.html)

### 联合体

- [`MaybeUninit`](https://doc.rust-lang.org/std/mem/union.MaybeUninit.html)

<!-- END AUTO ITEMS -->
