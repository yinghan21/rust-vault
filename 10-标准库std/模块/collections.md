---
title: "std::collections"
type: std-模块
module: collections
stable: "1.0.0"
unstable: false
tags:
  - std/模块
  - std/集合
aliases:
  - collections
  - 集合容器
一句话: 标准库的通用集合类型：哈希与有序的映射/集合、双端队列、优先队列和链表。
---

# std::collections

> [!abstract] 一句话
> `std::collections` 汇集 `HashMap`、`BTreeMap`、`HashSet`、`BTreeSet`、`VecDeque`、`BinaryHeap` 等通用容器，覆盖绝大多数数据组织需求。

## 模块简介

官方给的第一条建议是：**默认就用 `Vec` 和 `HashMap`**。这两个容器覆盖了通用数据存储与处理的大部分场景，其他集合只在特定需求下才是最优解。`Vec` 属于 `std::vec` 模块且已经通过 prelude 自动导入，本模块负责的是映射、集合、队列与堆这类结构。

按用途可以分成四组：

- 序列：`VecDeque`（双端队列，两端进出都是 O(1)）、`LinkedList`（双向链表，标准库中很少是最佳选择）。
- 映射：`HashMap`（哈希表，平均 O(1)，无序）、`BTreeMap`（B 树，按键有序，范围查询方便）。
- 集合：`HashSet`、`BTreeSet`，分别是上面两种映射的「键集」版本。
- 优先队列：`BinaryHeap`，二叉堆实现的最大堆，适合任务调度与 Top-K。

选择的依据通常是三条：需不需要有序遍历、需不需要在两端操作、需不需要按优先级取元素。都不需要时，`Vec` 或 `HashMap` 就是答案。

`HashMap` 默认使用 SipHash 抵御哈希洪水攻击，安全但不追求极致速度；对性能敏感的场景可以用 `HashMap::with_hasher` 换成自己的 `Hasher`。所有集合都提供 `with_capacity` 预分配，`try_reserve` 则能在分配失败时返回错误而不是直接失败。

## 快速上手

```rust
use std::collections::{BTreeMap, HashMap, VecDeque};

fn main() {
    // HashMap：键值对，查找平均 O(1)，迭代顺序不保证
    let mut scores = HashMap::new();
    scores.insert("Alice", 90);
    scores.insert("Bob", 75);

    // entry 占位：存在则修改，不存在则插入
    scores.entry("Alice").and_modify(|s| *s += 5).or_insert(0);
    assert_eq!(scores["Alice"], 95);
    assert_eq!(scores.get("Bob"), Some(&75));

    // BTreeMap：按键有序，遍历顺序稳定
    let mut sorted = BTreeMap::new();
    sorted.insert(3, "三");
    sorted.insert(1, "一");
    sorted.insert(2, "二");
    let keys: Vec<i32> = sorted.keys().copied().collect();
    assert_eq!(keys, vec![1, 2, 3]);

    // VecDeque：双端队列，两端插入与弹出都是 O(1)
    let mut queue = VecDeque::new();
    queue.push_back(1);
    queue.push_back(2);
    queue.push_front(0);
    assert_eq!(queue.pop_front(), Some(0));
    assert_eq!(queue.pop_back(), Some(2));
    assert_eq!(queue.len(), 1);
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[collections.HashMap|HashMap]] | 哈希表，平均 O(1) 查找，迭代无序。 |
| [[collections.HashSet|HashSet]] | 哈希集合，元素唯一，迭代无序。 |
| [[collections.BTreeMap|BTreeMap]] | 基于 B 树的有序映射，按键升序遍历。 |
| [[collections.BTreeSet|BTreeSet]] | 基于 B 树的有序集合。 |
| [[collections.VecDeque|VecDeque]] | 环形缓冲实现的双端队列。 |
| [[collections.BinaryHeap|BinaryHeap]] | 二叉堆实现的最大堆 / 优先队列。 |
| `collections::LinkedList` | 双向链表，实际项目中很少是最佳选择。 |
| `collections::TryReserveError` | `try_reserve` 分配失败时返回的错误。 |
| `collections::TryReserveErrorKind` | 描述分配失败原因的枚举。 |
| [[vec.Vec|Vec]] | 可增长数组，默认首选的序列容器（位于 `std::vec`）。 |
| `HashMap::entry` | 占位式插入或修改，避免重复查找。 |
| `BTreeMap::range` | 按键范围查询一段有序条目。 |
| `VecDeque::make_contiguous` | 把环形缓冲整理成连续切片。 |

## 注意事项

> [!tip] 先选 `Vec` / `HashMap`
> 除非明确需要有序遍历、双端操作或优先级，否则这两个就够了；它们实现最成熟、文档最多。

> [!danger] `HashMap` 的迭代顺序不确定
> 每次运行顺序可能不同，不能依赖它输出稳定结果。需要稳定顺序时改用 `BTreeMap`，或先收集再 `sort`。

> [!warning] 预分配能省掉大量扩容
> 已知规模时用 `with_capacity`；`try_reserve` 把「分配失败」变成可处理的 `Result`，适合内存受限的场景。

## 相关

- [[collections.HashMap|HashMap]] 与 [[collections.BTreeMap|BTreeMap]]：两种最常用的映射。
- [[12-集合类型|集合类型]]：集合的选择与常见操作。
- [[vec|std::vec 模块]]：`Vec` 的完整方法。
- [[iter|std::iter 模块]]：在集合上使用迭代器与适配器。
- [[hash|std::hash 模块]]：自定义 `Hash` 实现与哈希器。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 9 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [[collections.BTreeMap|`BTreeMap`]]
- [[collections.BTreeSet|`BTreeSet`]]
- [[collections.BinaryHeap|`BinaryHeap`]]
- [[collections.HashMap|`HashMap`]]
- [[collections.HashSet|`HashSet`]]
- [`LinkedList`](https://doc.rust-lang.org/std/collections/struct.LinkedList.html)
- [`TryReserveError`](https://doc.rust-lang.org/std/collections/struct.TryReserveError.html)
- [[collections.VecDeque|`VecDeque`]]

### 枚举

- [`TryReserveErrorKind`](https://doc.rust-lang.org/std/collections/enum.TryReserveErrorKind.html)

<!-- END AUTO ITEMS -->
