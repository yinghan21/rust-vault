---
title: "std::collections::VecDeque"
type: std-条目
kind: 结构体
module: collections
slug: collections.VecDeque
stable: "1.0.0"
tags:
  - std/集合
  - std/类型
aliases:
  - VecDeque
一句话: 用可增长的环形缓冲区实现的双端队列，两头进出都是 O(1)。
---

# `VecDeque<T>`

> [!abstract] 一句话
> `VecDeque<T>` 是可增长的**环形缓冲区**：`push_back` / `pop_front` 都是摊销 O(1)，既能当队列，也能当双端队列和栈。

## 简介

`VecDeque` 的典型用法就是队列：`push_back` 入队、`pop_front` 出队。因为它两头都能 O(1) 进出，做双端队列、滑动窗口、BFS 的待访问表、撤销栈都很合适；而 `Vec` 在头部插入或删除要搬移整个数组，是 O(n)。

内部是环形缓冲区，所以元素在内存里**不一定连续**。需要连续切片时（例如整体排序、传给只接受 `&[T]` 的函数），可以调 `make_contiguous()`：它会把环形内容旋转成一段连续内存并返回 `&mut [T]`。不关心顺序时，`as_slices()` 能直接拿到至多两段的只读视图。

和相邻类型的分工：需要随机访问、连续内存、缓存友好就用 [[vec.Vec|Vec]]；只需要按优先级取最值用 [[collections.BinaryHeap|BinaryHeap]]；需要键值查找用 [[collections.HashMap|HashMap]]。`VecDeque` 的强项是「两端增删」，随机访问虽然也支持（`get` / `get_mut`），但常数开销比 `Vec` 略高。

## 常用方法

### 构造与容量

| 方法 | 说明 |
| --- | --- |
| `new()` | 创建一个空的双端队列。 |
| `with_capacity(n)` | 创建空队列并预留 `n` 个元素的空间。 |
| `capacity()` | 返回不重新分配即可容纳的元素数。 |
| `reserve(n)` | 预留至少 `n` 个元素的容量。 |
| `reserve_exact(n)` | 预留刚好够 `n` 个元素的最小容量。 |
| `try_reserve(n)` | `reserve` 的可失败版本，失败返回 `Err`。 |
| `try_reserve_exact(n)` | `reserve_exact` 的可失败版本。 |
| `shrink_to_fit()` | 丢弃多余容量，尽量收缩到实际长度。 |
| `shrink_to(n)` | 收缩容量，但至少保留 `n` 个元素的空间。 |

### 长度与访问

| 方法 | 说明 |
| --- | --- |
| `len()` | 返回队列中的元素个数。 |
| `is_empty()` | 判断队列是否为空。 |
| `get(i)` | 返回下标 `i` 处元素的引用，越界为 `None`。 |
| `get_mut(i)` | 返回下标 `i` 处元素的可变引用。 |
| `front()` | 返回队首元素的引用，空队列为 `None`。 |
| `front_mut()` | 返回队首元素的可变引用。 |
| `back()` | 返回队尾元素的引用，空队列为 `None`。 |
| `back_mut()` | 返回队尾元素的可变引用。 |
| `contains(&x)` | 判断队列中是否存在等于 `x` 的元素。 |
| `swap(i, j)` | 交换下标 `i` 与 `j` 处的元素。 |

### 两端进出

| 方法 | 说明 |
| --- | --- |
| `push_front(v)` | 把元素压入队首。 |
| `push_back(v)` | 把元素压入队尾。 |
| `push_front_mut(v)` | 压入队首并返回该元素的可变引用。 |
| `push_back_mut(v)` | 压入队尾并返回该元素的可变引用。 |
| `pop_front()` | 移除并返回队首元素，空队列为 `None`。 |
| `pop_back()` | 移除并返回队尾元素，空队列为 `None`。 |
| `pop_front_if(p)` | 谓词通过时移除并返回队首元素。 |
| `pop_back_if(p)` | 谓词通过时移除并返回队尾元素。 |

### 插入、删除与裁剪

| 方法 | 说明 |
| --- | --- |
| `insert(i, v)` | 在下标 `i` 处插入元素，后续元素后移。 |
| `insert_mut(i, v)` | 在下标 `i` 处插入并返回其可变引用。 |
| `remove(i)` | 移除并返回下标 `i` 处元素，越界为 `None`。 |
| `swap_remove_front(i)` | 移除下标 `i` 处元素，用队首元素填补。 |
| `swap_remove_back(i)` | 移除下标 `i` 处元素，用队尾元素填补。 |
| `truncate(len)` | 截断到前 `len` 个元素，丢弃其余。 |
| `retain_back(len)` | 只保留最后 `len` 个元素，丢弃其余。 |
| `clear()` | 清空队列，移除所有元素。 |
| `retain(f)` | 只保留闭包返回 `true` 的元素。 |
| `retain_mut(f)` | 同 `retain`，闭包拿到可变引用。 |
| `resize(len, v)` | 调整长度，多删少补（补的是 `v` 的克隆）。 |
| `resize_with(len, f)` | 调整长度，缺失元素由闭包生成。 |
| `split_off(at)` | 在下标 `at` 处分裂，返回后半部分。 |
| `append(other)` | 把另一队列的元素全部移到本队列尾部。 |

### 遍历与区间

| 方法 | 说明 |
| --- | --- |
| `iter()` | 返回从队首到队尾的迭代器。 |
| `iter_mut()` | 返回可修改元素的从队首到队尾迭代器。 |
| `as_slices()` | 返回按顺序排列、至多两段的只读切片。 |
| `as_mut_slices()` | 返回按顺序排列、至多两段的可变切片。 |
| `range(r)` | 返回覆盖指定区间的迭代器。 |
| `range_mut(r)` | 返回覆盖指定区间的可变迭代器。 |
| `drain(r)` | 批量移除指定区间，返回被移除元素的迭代器。 |

### 旋转、连续化与查找

| 方法 | 说明 |
| --- | --- |
| `rotate_left(n)` | 把队列整体向左旋转 `n` 位。 |
| `rotate_right(n)` | 把队列整体向右旋转 `n` 位。 |
| `make_contiguous()` | 把环形内容转成一段连续切片并返回。 |
| `binary_search(&x)` | 在已排序队列中二分查找元素。 |
| `binary_search_by(f)` | 用比较函数二分查找。 |
| `binary_search_by_key(&b, f)` | 用键提取函数二分查找。 |
| `partition_point(p)` | 返回满足谓词的前缀长度，即分界下标。 |

## 示例

### 当队列和双端队列用

```rust
use std::collections::VecDeque;

fn main() {
    let mut q: VecDeque<i32> = VecDeque::new();
    q.push_back(1);
    q.push_back(2);
    q.push_front(0);

    assert_eq!(q.len(), 3);
    assert_eq!(q.front(), Some(&0));
    assert_eq!(q.back(), Some(&2));

    assert_eq!(q.pop_front(), Some(0));
    assert_eq!(q.pop_back(), Some(2));
    assert_eq!(q.pop_front(), Some(1));
    assert_eq!(q.pop_front(), None);

    // 从数组直接构造，用 for 循环按顺序遍历
    let d = VecDeque::from([-1, 0, 1]);
    let mut sum = 0;
    for x in &d {
        sum += *x;
    }
    assert_eq!(sum, 0);
}
```

### 环形缓冲区的两段切片与连续化

```rust
use std::collections::VecDeque;

fn main() {
    // 队首出队再入队，底层环形指向会绕到开头
    let mut d: VecDeque<i32> = (1..=4).collect();
    for _ in 0..2 {
        if let Some(x) = d.pop_front() {
            d.push_back(x);
        }
    }

    // as_slices 可能返回两段，合起来仍是完整顺序
    let (a, b) = d.as_slices();
    let mut joined: Vec<i32> = a.to_vec();
    joined.extend(b);
    assert_eq!(joined, vec![3, 4, 1, 2]);

    // make_contiguous 把它旋转成一段，可直接当切片用
    let s = d.make_contiguous();
    assert_eq!(s.to_vec(), vec![3, 4, 1, 2]);

    // 区间查找与旋转
    assert_eq!(d.get(0), Some(&3));
    d.rotate_left(1);
    assert_eq!(d.iter().copied().collect::<Vec<_>>(), vec![4, 1, 2, 3]);

    let removed: Vec<i32> = d.drain(1..3).collect();
    assert_eq!(removed, vec![1, 2]);
    assert_eq!(d.len(), 2);
}
```

## 常见陷阱

1. **元素不保证连续**：不要假设 `&d[..]` 能拿到整段切片，`VecDeque` 不实现 `Deref<Target = [T]>`；需要连续内存请先 `make_contiguous()`。
2. **`remove` / `insert` 是 O(n)**：它们要搬移受影响的元素，只有头尾的 `push_*` / `pop_*` 才是 O(1)；按索引频繁增删应改用别的结构。
3. **下标访问会 panic**：`d[0]` 走 `Index`，越界直接 panic；不确定时用 `get` 拿 `Option`。
4. **`binary_search` 要求已排序**：队列没排序时结果未定义且无意义，先排序或用线性 `contains`。
5. **`retain` 的闭包只能看 `&T`**：需要在遍历中修改元素请用 `retain_mut`，否则编译不过。

## 相关

- [[collections|std::collections 模块]]：本模块全部集合类型。
- [[vec.Vec|Vec]]：连续内存的主力容器，头部增删是 O(n)。
- [[collections.BinaryHeap|BinaryHeap]]：只需要取最值时的优先队列。
- [[iter.DoubleEndedIterator|DoubleEndedIterator]]：`VecDeque` 的迭代器天然双端。
- [[12-集合类型|集合类型]]：各集合的选型与常见操作。
