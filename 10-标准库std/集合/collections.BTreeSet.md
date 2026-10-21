---
title: "std::collections::BTreeSet"
type: std-条目
kind: 结构体
module: collections
slug: collections.BTreeSet
stable: "1.0.0"
tags:
  - std/集合
  - std/类型
aliases:
  - BTreeSet
一句话: 基于 B 树实现的有序集合，元素按 Ord 升序排列，支持区间查询与范围切分。
---

# `BTreeSet<T>`

> [!abstract] 一句话
> `BTreeSet<T>` 是元素唯一且**始终有序**的集合，底层是 [[collections.BTreeMap|BTreeMap]]，单次操作 O(log n)，遍历按升序。

## 简介

`BTreeSet` 就是「只存键」的 `BTreeMap<T, ()>`。它和 [[collections.HashSet|HashSet]] 的关系，正如 `BTreeMap` 和 `HashMap`：功能相同，取舍不同——`BTreeSet` 慢一个常数级，但保证顺序，并且能 `range` 取区间、`first` / `last` 取两端。

元素类型必须实现 `Ord`（全序），不要求 `Hash`。字符串按字典序、元组按字典序逐项比较，所以 `BTreeSet` 也是「自动排序 + 去重」的顺手工具：把一批数据塞进去再 `iter()` 出来，就已经排好序了。

常见用途：维护有序的去重列表、做区间内的成员查询、实现「最近邻」式的上下界查找（用 `range` 配合 `next()` / `next_back()`）、统计不同元素数量。元素进入集合后不能再修改，需要改就先 `take` 出来、改完再 `insert` 回去。

## 常用方法

### 构造与整体操作

| 方法 | 说明 |
| --- | --- |
| `new()` | 创建空的有序集合。 |
| `clear()` | 清空集合，移除所有元素。 |
| `append(other)` | 把另一集合的元素全部移入，并清空它。 |
| `split_off(v)` | 返回大于等于该值的元素组成的新集合。 |

### 查询

| 方法 | 说明 |
| --- | --- |
| `contains(v)` | 判断集合中是否存在该值。 |
| `get(v)` | 返回集合中与该值相等的元素引用。 |
| `len()` | 返回元素个数。 |
| `is_empty()` | 判断集合是否为空。 |
| `is_disjoint(other)` | 判断两边是否没有公共元素。 |
| `is_subset(other)` | 判断 `self` 是否为 `other` 的子集。 |
| `is_superset(other)` | 判断 `self` 是否为 `other` 的超集。 |

### 首尾元素

| 方法 | 说明 |
| --- | --- |
| `first()` | 返回最小元素的引用。 |
| `last()` | 返回最大元素的引用。 |
| `pop_first()` | 移除并返回最小元素。 |
| `pop_last()` | 移除并返回最大元素。 |

### 插入与删除

| 方法 | 说明 |
| --- | --- |
| `insert(v)` | 插入值，返回它是否为新元素。 |
| `replace(v)` | 插入并替换相等的旧元素，返回旧值。 |
| `remove(v)` | 删除值，返回它原来是否存在。 |
| `take(v)` | 删除并返回与该值相等的元素。 |
| `retain(f)` | 只保留谓词返回 `true` 的元素。 |
| `extract_if(range, pred)` | 在区间内移出满足谓词的元素并迭代。 |

### 集合运算与遍历

| 方法 | 说明 |
| --- | --- |
| `difference(other)` | 迭代只在 `self` 中的元素，升序。 |
| `symmetric_difference(other)` | 迭代只在一侧出现的元素，升序。 |
| `intersection(other)` | 迭代两边共有的元素，升序。 |
| `union(other)` | 迭代两边全部元素并去重，升序。 |
| `range(r)` | 迭代指定区间内的元素，升序。 |
| `iter()` | 按升序迭代所有元素的引用。 |

## 示例

```rust
use std::collections::BTreeSet;

fn main() {
    // 构造时自动去重并按升序排列
    let set: BTreeSet<i32> = BTreeSet::from([5, 1, 3, 3, 9]);
    let ordered: Vec<i32> = set.iter().copied().collect();
    assert_eq!(ordered, vec![1, 3, 5, 9]);

    // 两端元素是集合中的最小值和最大值
    assert_eq!(set.first(), Some(&1));
    assert_eq!(set.last(), Some(&9));

    // range 是左闭右开区间
    let middle: Vec<i32> = set.range(3..9).copied().collect();
    assert_eq!(middle, vec![3, 5]);

    // 集合运算同样保持升序
    let a: BTreeSet<i32> = BTreeSet::from([1, 2, 3]);
    let b: BTreeSet<i32> = BTreeSet::from([3, 4]);
    assert!(a.is_subset(&BTreeSet::from([1, 2, 3, 4])));
    assert!(!a.is_disjoint(&b));
    let union: Vec<i32> = a.union(&b).copied().collect();
    assert_eq!(union, vec![1, 2, 3, 4]);

    // insert 返回是否新元素，take 连所有权一起取回
    let mut langs: BTreeSet<String> = BTreeSet::new();
    assert!(langs.insert("rust".to_string()));
    assert!(!langs.insert("rust".to_string()));
    assert_eq!(langs.take("rust"), Some("rust".to_string()));
    assert!(langs.is_empty());

    // split_off 把大于等于给定值的部分拆到新集合
    let mut nums: BTreeSet<i32> = BTreeSet::from([1, 2, 3, 4, 5]);
    let tail = nums.split_off(&3);
    assert_eq!(nums.len(), 2);
    assert_eq!(tail.len(), 3);
}
```

## 常见陷阱

1. **元素必须实现 `Ord`**：不能像 `HashSet` 那样只实现 `Eq + Hash`，`f64` 依然不能用。对策：需要浮点排序时先转成定点整数，或自己实现 `Ord`。
2. **比 `HashSet` 慢一个常数级**：每次操作 O(log n) 且要比较元素。对策：只要「在不在」且顺序无所谓，就换 `HashSet`。
3. **`range` 默认左闭右开**：`range(3..9)` 不含 `9`，要包含上界写 `3..=9`。对策：边界写完后用 `first()` / `last()` 核对。
4. **元素进入后不能再改**：只能得到 `&T`，没有可变迭代器。对策：`take` 取出后修改，再 `insert` 回去。
5. **`split_off` 会重建一棵树**：返回的是新集合而不是视图。对策：只要切片遍历就用 `range`。

## 相关

- [[collections|std::collections 模块]]：本模块全部条目。
- [[collections.BTreeMap|BTreeMap]]：`BTreeSet` 的底层实现，需要给元素附带数据时用它。
- [[collections.HashSet|HashSet]]：无序但更快的集合。
- [[cmp.Ord|Ord]]：集合元素必须实现的全序特质。
- [[12-集合类型|集合类型]]：去重、求交集、排序等场景的选型对比。
