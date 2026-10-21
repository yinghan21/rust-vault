---
title: "std::collections::BinaryHeap"
type: std-条目
kind: 结构体
module: collections
slug: collections.BinaryHeap
stable: "1.0.0"
tags:
  - std/集合
  - std/类型
aliases:
  - BinaryHeap
一句话: 二叉堆实现的最大堆，也是标准库自带的优先队列，取最大值 O(1)、进出 O(log n)。
---

# `BinaryHeap<T>`

> [!abstract] 一句话
> `BinaryHeap<T>` 是二叉堆实现的**最大堆**：`peek` 看最大值 O(1)，`push` / `pop` 都是 O(log n)，可以当作优先队列用。

## 简介

`BinaryHeap` 只承诺一件事：随时能以 O(1) 取到最大元素。因此它天然就是优先队列——任务调度、Dijkstra、合并 K 个有序序列、取 Top-N 都用它。元素类型必须实现 `Ord`。

它**默认是最大堆**。需要最小堆时，标准库的惯用做法是把元素包进 `std::cmp::Reverse`，这样「最小」就变成了包装类型的「最大」，不用自定义比较函数。

注意堆内部用 `Vec` 存储，只有堆顶有顺序保证：`iter()`、`as_slice()`、`into_vec()`、`drain()` 都是**任意顺序**（实际是底层数组顺序）。要顺序结果必须用 `into_sorted_vec()`，它消耗堆并返回升序 `Vec`。元素进入堆后不能改变其排序，`peek_mut` 修改后由 `PeekMut` 在丢弃时自动修复堆序。

## 常用方法

### 构造

| 方法 | 说明 |
| --- | --- |
| `new()` | 创建一个空的最大堆。 |
| `with_capacity(n)` | 创建最大堆并预留至少 `n` 个元素的空间。 |

### 进出元素

| 方法 | 说明 |
| --- | --- |
| `push(item)` | 把元素压入堆。 |
| `pop()` | 移除并返回堆中最大元素。 |
| `peek()` | 返回最大元素的引用，不取出。 |
| `peek_mut()` | 返回最大元素的可变引用，便于就地修改。 |

### 容量管理

| 方法 | 说明 |
| --- | --- |
| `capacity()` | 返回不再重新分配即可容纳的元素数。 |
| `reserve(n)` | 预留至少 `n` 个元素的容量。 |
| `reserve_exact(n)` | 预留刚好够 `n` 个元素的最小容量。 |
| `try_reserve(n)` | 可失败版本，分配失败返回 `Err`。 |
| `try_reserve_exact(n)` | `reserve_exact` 的可失败版本。 |
| `shrink_to_fit()` | 丢弃多余容量，尽量收缩。 |
| `shrink_to(n)` | 收缩容量，但保留至少 `n` 个。 |

### 遍历与转换

| 方法 | 说明 |
| --- | --- |
| `iter()` | 按底层数组顺序迭代元素，无序。 |
| `as_slice()` | 返回底层数组的切片，无序。 |
| `into_vec()` | 消耗堆，返回底层 `Vec`，无序。 |
| `into_sorted_vec()` | 消耗堆，返回升序排列的 `Vec`。 |
| `drain()` | 清空堆并迭代移出的元素，无序。 |

### 批量与整体操作

| 方法 | 说明 |
| --- | --- |
| `append(other)` | 把另一堆的元素全部移入，并清空它。 |
| `retain(f)` | 只保留谓词返回 `true` 的元素。 |
| `clear()` | 清空堆中所有元素。 |
| `len()` | 返回堆中元素个数。 |
| `is_empty()` | 判断堆是否为空。 |

## 示例

```rust
use std::cmp::Reverse;
use std::collections::BinaryHeap;

fn main() {
    // 默认是最大堆：peek 与 pop 都先给最大值
    let mut heap = BinaryHeap::new();
    assert_eq!(heap.peek(), None);
    for x in [3, 1, 4, 1, 5, 9, 2] {
        heap.push(x);
    }
    assert_eq!(heap.len(), 7);
    assert_eq!(heap.peek(), Some(&9));
    assert_eq!(heap.pop(), Some(9));

    // iter 是底层数组顺序，不能当有序结果用
    assert_eq!(heap.iter().copied().max(), Some(5));

    // 要升序数据就消耗堆，用 into_sorted_vec
    let sorted = heap.into_sorted_vec();
    assert_eq!(sorted, vec![1, 1, 2, 3, 4, 5]);

    // 最小堆：把元素包进 Reverse，取反后最大的就是最小的
    let mut min_heap: BinaryHeap<Reverse<i32>> = BinaryHeap::new();
    for x in [3, 1, 4] {
        min_heap.push(Reverse(x));
    }
    assert_eq!(min_heap.pop(), Some(Reverse(1)));

    // retain 就地过滤，再按升序取出
    let mut evens = BinaryHeap::from([1, 2, 3, 4, 5, 6]);
    evens.retain(|x| x % 2 == 0);
    assert_eq!(evens.into_sorted_vec(), vec![2, 4, 6]);
}
```

## 常见陷阱

1. **默认是最大堆**：想要最小堆却直接 `push`，取出的永远是最小值。对策：元素包一层 `Reverse`，或用 `BinaryHeap<(Reverse<Key>, T)>` 保留附加值。
2. **`iter()` / `into_vec()` 无序**：它们返回底层数组顺序，既非升序也非降序。对策：需要顺序就用 `into_sorted_vec()`，或自己 `sort`。
3. **元素必须实现 `Ord`**：`f64` 不能直接进堆。对策：用定点整数，或包装类型自己实现 `Ord`（并处理 NaN）。
4. **`peek_mut` 改完不能泄漏**：`PeekMut` 在被丢弃时负责恢复堆序，`mem::forget` 掉它会让堆内部失序。对策：让 `PeekMut` 自然离开作用域。
5. **只看堆顶不等于全序**：`peek` 只保证最大，其余元素无序。对策：需要反复取最值的场景就用 `pop`，别遍历堆去找第二个最大值。

## 相关

- [[collections|std::collections 模块]]：本模块全部条目。
- [[vec.Vec|Vec]]：`BinaryHeap` 的底层存储，`into_vec` 返回它。
- [[collections.VecDeque|VecDeque]]：双端队列，适合先进先出而不是按优先级。
- [[cmp.Ord|Ord]]：堆元素必须实现的全序特质。
- [[12-集合类型|集合类型]]：`Vec`、`HashMap`、`BinaryHeap` 的选型对比。
