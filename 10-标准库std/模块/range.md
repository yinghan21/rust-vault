---
title: "std::range"
type: std-模块
module: range
stable: "1.96.0"
unstable: false
tags:
  - std/模块
  - std/类型
aliases:
  - range
一句话: "区间类型的新家：Range、RangeFrom、RangeInclusive 等结构体连同它们的 by-value 迭代器，未来将取代 std::ops 里的旧类型。"
---

# std::range

> [!abstract] 一句话
> `std::range` 收拢了 `a..b`、`a..=b`、`..b`、`a..`、`..` 这些区间类型，并给可迭代的几种配了专用迭代器；它的目标是取代 [[ops|std::ops]] 里的旧版本。

## 模块简介

区间在语法上一直存在（`a..b`、`a..=b`、`a..`、`..b`、`..`），但类型一直住在 [[ops|std::ops]]。`std::range` 把它们搬了出来：`Range`、`RangeFrom`、`RangeTo`、`RangeInclusive`、`RangeToInclusive`、`RangeFull` 六个名字在这里重新定义，另外补了三个 by-value 迭代器 `RangeIter`、`RangeFromIter`、`RangeInclusiveIter`。

搬迁的理由是模块职责：`std::ops` 是运算符重载的地盘（`Add`、`Index`、`Fn`），区间只是一族实现了 `RangeBounds` 的普通结构体，却和运算符 trait 挤在一起。独立成模块之后，区间语义、边界规则、迭代器可以放在一处讲清楚；官方也明确说这是为了在未来的 edition 里替换掉 `std::ops` 的旧类型。

需要分清「语法」和「类型」两件事。语法在所有 edition 里都一样；但当前的 edition 下，`1..5` 构造出来的仍然是 `std::ops::Range`，`std::range::Range` 是另一个结构体，两者不能直接互相传递，只能靠 `From` / `Into` 转换（`let r: std::range::Range<usize> = (1..5).into();`）。判断手上到底是哪一个，打印 `std::any::type_name_of_val` 或看函数签名要求就行。

用途没有变化：`for` 循环、切片下标（`Index<Range<usize>>`）、`contains` 判断、接受 `RangeBounds` 的泛型参数，以及 `..` 这种「整段」写法。

## 快速上手

```rust
use std::range::{Range, RangeFull, RangeInclusive, RangeIter};

fn main() {
    let nums = [10, 20, 30, 40, 50];

    // 1. 左闭右开：0..3 取前三个。语法构造的是 ops 的区间，用 into 转成新类型
    let head: Range<usize> = (0..3).into();
    assert_eq!(&nums[head], &[10, 20, 30][..]);

    // 2. 闭区间，同时支持 contains 判断
    let first_four: RangeInclusive<usize> = (0..=3).into();
    assert_eq!(&nums[first_four.clone()], &[10, 20, 30, 40][..]);
    assert!(first_four.contains(&3));
    assert!(!first_four.contains(&4));

    // 3. 无界区间表示整段
    let all: RangeFull = (..).into();
    assert_eq!(&nums[all], &nums[..]);

    // 4. 区间自己就是迭代器，RangeIter 是它的 by-value 迭代器
    let mut it: RangeIter<i32> = Range::from(1..3).into_iter();
    assert_eq!(it.next(), Some(1));
    assert_eq!(it.next(), Some(2));
    assert_eq!(it.next(), None);

    // 5. 当前 edition 下区间语法照旧可用
    let total: i32 = (1..=5).sum();
    assert_eq!(total, 15);

    println!("全部通过");
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| `Range<Idx>` | `start..end`，左闭右开，可迭代。 |
| `RangeFrom<Idx>` | `start..`，只有下界，可迭代。 |
| `RangeInclusive<Idx>` | `start..=end`，两端都含，可迭代。 |
| `RangeTo<Idx>` | `..end`，只有上界，不能迭代。 |
| `RangeToInclusive<Idx>` | `..=end`，只有上界且包含，不能迭代。 |
| `RangeFull` | `..`，无界区间，常用于整段切片。 |
| `RangeIter<Idx>` | `Range` 的 by-value 迭代器。 |
| `RangeFromIter<Idx>` | `RangeFrom` 的 by-value 迭代器。 |
| `RangeInclusiveIter<Idx>` | `RangeInclusive` 的 by-value 迭代器。 |

## 注意事项

> [!warning] `std::range` 与 `std::ops` 目前是两套类型
> 当前 edition 里 `1..5` 仍然产生 `std::ops::Range`，不能直接赋给 `std::range::Range`，要显式 `.into()`；反过来也一样。这是为未来 edition 迁移铺的路，过渡期两套类型会共存，看函数签名 / 用 `type_name_of_val` 确认自己拿到的是哪一套。较旧的工具链上这个模块可能还不存在。

> [!tip] 哪些区间能迭代
> `Range`、`RangeFrom`、`RangeInclusive` 实现了 `Iterator`，可以直接 `for`、`.sum()`、`.map()`；`RangeTo`、`RangeToInclusive`、`RangeFull` 缺少起点或两端，不是迭代器，只用于切片下标和 `RangeBounds` 参数。新模块额外为前三种提供了 `RangeIter` / `RangeFromIter` / `RangeInclusiveIter` 作为显式的 by-value 迭代器类型。

> [!danger] 边界写错不是 panic 就是空区间
> 拿 `&v[a..b]` 做下标时要求 `a <= b <= v.len()`，否则 panic；`a..=b` 在 `a > b` 时迭代为空，但作为切片下标**仍然**会 panic（要求 `a <= b`）。可能越界时用 `.get(a..b)` 拿到 `Option`，不要靠 `catch_unwind` 兜。

## 相关

- [[ops|std::ops]]：运算符重载，旧的区间类型仍在 `std::ops::Range`。
- [[ops.Range|Range]]：旧版区间类型的完整笔记，可与本页对照。
- [[18-迭代器|迭代器]]：区间是最简单的迭代器之一。
- [[slice|std::slice]]：切片下标全部由区间类型驱动。
- [[iter.Iterator|Iterator]]：`Range` 系列实现的那套接口。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 9 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`Range`](https://doc.rust-lang.org/std/range/struct.Range.html)
- [`RangeFrom`](https://doc.rust-lang.org/std/range/struct.RangeFrom.html)
- [`RangeFromIter`](https://doc.rust-lang.org/std/range/struct.RangeFromIter.html)
- [`RangeFull`](https://doc.rust-lang.org/std/range/struct.RangeFull.html)
- [`RangeInclusive`](https://doc.rust-lang.org/std/range/struct.RangeInclusive.html)
- [`RangeInclusiveIter`](https://doc.rust-lang.org/std/range/struct.RangeInclusiveIter.html)
- [`RangeIter`](https://doc.rust-lang.org/std/range/struct.RangeIter.html)
- [`RangeTo`](https://doc.rust-lang.org/std/range/struct.RangeTo.html)
- [`RangeToInclusive`](https://doc.rust-lang.org/std/range/struct.RangeToInclusive.html)

<!-- END AUTO ITEMS -->
