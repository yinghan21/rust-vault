---
title: "std::iter::DoubleEndedIterator"
type: std-条目
kind: 特质
module: iter
slug: iter.DoubleEndedIterator
stable: "1.0.0"
tags:
  - std/特质
  - std/类型
aliases:
  - DoubleEndedIterator
一句话: 可以从两端取元素的迭代器，多出 next_back 等五个稳定方法。
---

# `DoubleEndedIterator`

> [!abstract] 一句话
> `DoubleEndedIterator` 在 [[iter.Iterator|Iterator]] 之上加了一个能力：既能从头部 `next()`，也能从尾部 `next_back()` 取元素。

## 简介

普通迭代器只能一路往前，`DoubleEndedIterator` 允许两头一起走。两个方向共享同一个剩余区间，**不会交叉**：前后指针在中间相遇时迭代就结束了，之后两头都返回 `None`。

`next()` 和 `next_back()` 可以任意穿插调用，每次调用都让剩余区间缩短一个元素。也正因为共享区间，一旦某端返回过 `None`，再调用可能永远返回 `None`，也可能不返回——需要确定性行为时套一层 `fuse()`。

它同时是 `rev()`、`rposition()` 的前提：`Iterator::rev` 要求 `Self: Sized + DoubleEndedIterator`。`Vec`、`VecDeque`、数组、切片、区间都实现了它，而 `filter`、`map` 这类适配器只有在内层也实现时才跟着实现。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `next_back(&mut self)` | 从尾部取出一个元素，空时为 `None`。 |

## 提供的方法

| 方法 | 说明 |
| --- | --- |
| `nth_back(n)` | 从尾部返回倒数第 `n` 个元素。 |
| `try_rfold(init, f)` | 从尾部开始的可失败折叠，出错即停。 |
| `rfold(init, f)` | 从尾部开始把元素折叠成单个值。 |
| `rfind(p)` | 从尾部找到第一个满足条件的元素。 |

## 关联类型

| 关联类型 | 说明 |
| --- | --- |
| `type Item;` | 继承自 `Iterator`，两端取出的是同一种元素类型。 |

## 示例

### 两端穿插取值

```rust
fn main() {
    let v = vec![1, 2, 3, 4, 5, 6];
    let mut it = v.iter();

    assert_eq!(it.next(), Some(&1));
    assert_eq!(it.next_back(), Some(&6));
    assert_eq!(it.next_back(), Some(&5));
    assert_eq!(it.next(), Some(&2));
    assert_eq!(it.next(), Some(&3));
    assert_eq!(it.next(), Some(&4));

    // 两头相遇后都返回 None
    assert_eq!(it.next(), None);
    assert_eq!(it.next_back(), None);
}
```

### 反向方法 `rev`、`rfind`、`rfold`

```rust
fn main() {
    let v = [1, 2, 3, 4, 5];

    // rev 反转方向
    let reversed: Vec<i32> = v.iter().copied().rev().collect();
    assert_eq!(reversed, vec![5, 4, 3, 2, 1]);

    // rfind 从尾部找偶数
    assert_eq!(v.iter().rfind(|&&x| x % 2 == 0), Some(&4));

    // rfold 从尾部折叠：先 5，再 4……
    let n = v.iter().copied().rfold(0, |acc, x| acc * 10 + x);
    assert_eq!(n, 54321);

    // nth_back 取倒数第二个，注意下标从 0 开始
    assert_eq!(v.iter().nth_back(1), Some(&4));
}
```

## 常见陷阱

1. **两端共享同一区间**：`next()` 取走头元素后，`next_back()` 不会重复给出它；以为能分别遍历两遍是最常见的误解。
2. **返回 `None` 后行为不确定**：某些实现（如 `Chain` 之外的自定义迭代器）在耗尽后再调用可能仍给出元素，需要确定语义时用 `fuse()`。
3. **不是所有迭代器都是双端的**：`map`、`filter` 只在内层也双端时才双端，`std::iter::once` 这类一次性迭代器则不是，用 `rev()` 前先确认约束。
4. **`rev()` 不复制数据**：`Rev` 只是把取值方向调头，不会生成新集合，且要求底层支持 `next_back()`。
5. **`rposition` 的下标仍从头算**：它返回的是正向下标，不是「倒数第几个」。

## 相关

- [[iter|std::iter 模块]]：迭代器相关条目总览。
- [[iter.Iterator|Iterator]]：本特质的父特质，提供 `next` 与多数适配器。
- [[iter.ExactSizeIterator|ExactSizeIterator]]：常与双端迭代器配合，`rposition` 同时要求两者。
- [[collections.VecDeque|VecDeque]]：天然支持两端进出的集合。
- [[18-迭代器|迭代器]]：学习笔记中的迭代器章节。
