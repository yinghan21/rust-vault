---
title: "std::ops::Range"
type: std-条目
kind: 结构体
module: ops
slug: ops.Range
stable: "1.0.0"
tags:
  - std/类型
aliases:
  - Range
一句话: 左闭右开区间 `start..end`，既是最常见的用于循环与切片的迭代器，也是切片下标的类型。
---

# `Range<Idx>`

> [!abstract] 一句话
> `Range<Idx>` 就是 `start..end` 这个**左闭右开**区间：包含 `start`，不包含 `end`；它既可以用作 `for` 循环的迭代器，也可以用作切片下标。

## 简介

`Range` 的结构非常直白：

```text
pub struct Range<Idx> {
    pub start: Idx,
    pub end: Idx,
}
```

两个字段都是公开的，可以直接读写成 `r.start` / `r.end`。因为它实现了 `Iterator`（产出从 `start` 开始、到 `end - 1` 结束的值），所以 `for i in 0..n` 里的 `0..n` 就是一个 `Range<usize>`；又因为 `[T]`、`Vec<T>`、`String` 等都实现了 `Index<Range<usize>>`，所以 `&v[1..3]` 里传的也是它。

边界语义是**左闭右开**，这样一来「长度」就等于 `end - start`，相邻区间拼接时不会重叠，`0..n` 恰好覆盖 `n` 个元素。需要包含右端点时用 `a..=b`，那是另一个类型 `RangeInclusive`，不要和 `Range` 混用。

它属于 [[ops|std::ops 模块]] 中的区间家族，同一家族还有 `RangeFrom`（`a..`）、`RangeTo`（`..b`）、`RangeToInclusive`（`..=b`）和 `RangeFull`（`..`）；`RangeBounds` trait 把这些类型统一起来，`slice::get`、`drain`、`splice` 等接受 `R: RangeBounds<usize>` 的方法可以接受任意一种。

## 常用方法

| 方法 | 说明 |
| --- | --- |
| `contains(item)` | 判断 `item` 是否落在区间内（左闭右开）。 |
| `is_empty()` | 判断区间是否不含任何元素，即 `!(start < end)`。 |

> [!tip] 签名
> `pub fn contains<U>(&self, item: &U) -> bool where Idx: PartialOrd<U>, U: PartialOrd<Idx> + ?Sized`
> `pub fn is_empty(&self) -> bool where Idx: PartialOrd`

## 示例

```rust
use std::ops::Range;

fn main() {
    let r: Range<i32> = 1..5;
    assert_eq!(r.start, 1);
    assert_eq!(r.end, 5);

    // 左闭右开：1、2、3、4 在区间内，5 不在
    assert!(r.contains(&1));
    assert!(r.contains(&4));
    assert!(!r.contains(&0));
    assert!(!r.contains(&5));

    // start == end 时区间为空
    assert!((5..5).is_empty());
    assert!(!r.is_empty());
    // start > end 也是空区间，用 for 循环不会产出任何值
    assert!((3..1).is_empty());
}
```

用作迭代器与切片下标：

```rust
fn main() {
    // 1) 当迭代器：产出 1, 2, 3
    let mut sum = 0;
    for i in 1..4 {
        sum += i;
    }
    assert_eq!(sum, 6);

    // 2) 当下标：&v[1..3] 取下标 1、2 两个元素
    let v = [10, 20, 30, 40, 50];
    assert_eq!(&v[1..3], &[20, 30]);
    assert_eq!(v[1..3].len(), 2);

    // 3) 直接当迭代器用，配合 Iterator 的适配器
    let doubled: Vec<i32> = (0..3).map(|x| x * 2).collect();
    assert_eq!(doubled, [0, 2, 4]);
}
```

## 常见陷阱

1. **忘记右端是开区间**：`v[0..len]` 才覆盖全部元素，`v[0..len - 1]` 会漏掉最后一个；要包含右端点请写 `0..=len - 1`（类型是 `RangeInclusive`）。
2. **`Range` 只能迭代一次**：`Range` 不可 `Copy`，作为迭代器被 `for` 消耗后不能再用，需要重复使用就先 `clone()`。
3. **下标用错整数类型**：切片下标要求 `Range<usize>`，`0..n` 中的 `n` 若是 `i32` 需要显式转换，否则编译报错。
4. **空区间不报错**：`start >= end` 时迭代不产出任何元素、`is_empty()` 为 `true`，循环体不执行很容易被误判成逻辑没生效。
5. **`Range<f64>` 的 `contains` 对 `NaN` 恒为假**：因为比较基于 `PartialOrd`，`NaN` 与任何值都不可比，判断浮点区间时要注意。

## 相关

- [[ops|std::ops 模块]]：`Range`、`RangeInclusive`、`RangeBounds` 等区间与运算符 trait 都在这里。
- [[primitive.slice|Type slice]]：切片的下标与 `get` 都接受 `Range<usize>`。
- [[iter.Iterator|Iterator]]：`Range` 实现了它，可以接 `map`、`filter`、`sum` 等适配器。
- [[18-迭代器|迭代器]]：`for` 循环与区间迭代的展开过程。
