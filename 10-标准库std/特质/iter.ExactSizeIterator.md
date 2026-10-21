---
title: "std::iter::ExactSizeIterator"
type: std-条目
kind: 特质
module: iter
slug: iter.ExactSizeIterator
stable: "1.0.0"
tags:
  - std/特质
  - std/类型
aliases:
  - ExactSizeIterator
一句话: 明确知道自己还剩多少个元素的迭代器，提供精确的 len。
---

# `ExactSizeIterator`

> [!abstract] 一句话
> `ExactSizeIterator` 表示迭代器**确切知道**自己还能迭代多少次，于是 `len()` 可以给出精确剩余长度，而不是模糊的区间提示。

## 简介

大多数迭代器只能用 `size_hint()` 给出 `(下界, 可选上界)`，因为 `filter`、`take_while` 之类的适配器无法预知会命中几个元素。`ExactSizeIterator` 是更强的承诺：剩余长度就是确定的数字，`len()` 直接返回它。

它永远和 `Iterator` 一起出现；实现时还要求 `size_hint()` 返回精确值（上下界都等于真实剩余长度），否则 `len()` 的默认实现会算出错误结果。`len()` 虽在必需方法里，但**有默认实现**，通常不必手写，只在能算得更快时才覆盖。

由于长度精确，标准库能据此预分配：`collect` 到 `Vec` 时会按长度提示预留容量，而精确的长度提示最可靠。`Vec`、`VecDeque`、数组、切片、区间都实现了它；`filter`、`flat_map` 这类改变元素数量的适配器则不会实现。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `len(&self)` | 返回剩余元素个数，有默认实现可覆盖。 |

> [!note] 还要顺便检查 `size_hint`
> 默认实现的 `len()` 直接从 `size_hint()` 取上界并断言其存在，所以真正决定正确性的是 `size_hint()` 是否精确。

## 提供的方法

本特质没有额外提供默认实现的方法；`len()` 本身就是带默认实现的那一个。

## 关联类型

| 关联类型 | 说明 |
| --- | --- |
| `type Item;` | 继承自 `Iterator`，本特质不再引入新的关联类型。 |

## 示例

### 精确长度随处可见

```rust
fn main() {
    // 区间知道自己的长度
    let five = 0..5;
    assert_eq!(five.len(), 5);

    // Vec 的迭代器也知道
    let v = vec!['a', 'b', 'c'];
    let mut it = v.iter();
    assert_eq!(it.len(), 3);
    it.next();
    assert_eq!(it.len(), 2);

    // 数组同理
    let arr = [1, 2, 3, 4];
    assert_eq!(arr.iter().len(), 4);

    // 双端迭代器还能配合 rposition，从右往左找
    assert_eq!(v.iter().rposition(|&c| c == 'b'), Some(1));
}
```

### 自己实现 `ExactSizeIterator`

```rust
struct Countdown {
    remaining: usize,
}

impl Iterator for Countdown {
    type Item = usize;

    fn next(&mut self) -> Option<usize> {
        if self.remaining == 0 {
            None
        } else {
            self.remaining -= 1;
            Some(self.remaining)
        }
    }

    // 承诺长度精确：上下界相等
    fn size_hint(&self) -> (usize, Option<usize>) {
        (self.remaining, Some(self.remaining))
    }
}

impl ExactSizeIterator for Countdown {}

fn main() {
    let mut c = Countdown { remaining: 3 };
    assert_eq!(c.len(), 3);

    // len 就是剩余次数，取一个就少一个
    assert_eq!(c.next(), Some(2));
    assert_eq!(c.len(), 2);
    assert_eq!(c.count(), 2);
}
```

## 常见陷阱

1. **`filter` 之后就没有 `len()` 了**：过滤会改变元素数量，`Filter` 只实现 `Iterator`，想要长度请先 `collect` 再取 `Vec::len()`。
2. **`size_hint` 写错会让 `len()` 撒谎**：默认实现直接用上界，实现者必须保证 `(n, Some(n))` 里的 `n` 真的等于剩余个数。
3. **`len()` 是剩余数量，不是总数**：迭代到一半时它只算还没产出的部分，别拿它当集合容量。
4. **`ExactSizeIterator` 不保证元素连续或可随机访问**：它只承诺数量精确，要按下标取元素仍需 `get` 之类的接口。
5. **别在循环里边迭代边改集合**：借用规则会拦住它，强行用 `RefCell` 之类绕过又可能让长度承诺失效。

## 相关

- [[iter|std::iter 模块]]：迭代器相关条目总览。
- [[iter.Iterator|Iterator]]：本特质的父特质，`size_hint` 就在这里。
- [[iter.DoubleEndedIterator|DoubleEndedIterator]]：常与精确长度一起出现，`rposition` 同时要求两者。
- [[vec.Vec|Vec]]：最常见的精确长度来源。
- [[18-迭代器|迭代器]]：学习笔记中的迭代器章节。
