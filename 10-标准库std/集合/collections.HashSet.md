---
title: "std::collections::HashSet"
type: std-条目
kind: 结构体
module: collections
slug: collections.HashSet
stable: "1.0.0"
tags:
  - std/集合
  - std/类型
aliases:
  - HashSet
一句话: 用哈希表实现的无序集合，自动去重，判断「在不在」平均 O(1)。
---

# `HashSet<T>`

> [!abstract] 一句话
> `HashSet<T>` 是只存键不存值的 [[collections.HashMap|HashMap]]，元素唯一、顺序不定，平均值成员判断与插入都是 O(1)。

## 简介

`HashSet` 的语义就是数学上的「集合」：每个值最多出现一次，你只关心「在不在」。它内部就是一个 `HashMap<T, ()>`，所以容量、哈希、内存开销这些特征与 `HashMap` 完全一致，成员判断比 `Vec` 的线性扫描快得多。

元素类型必须实现 `Eq + Hash`，最常见的做法是 `#[derive(PartialEq, Eq, Hash)]`。注意**浮点数不能放进 `HashSet`**，因为 `f64` 没有实现 `Eq` 和 `Hash`。

需要顺序时用 [[collections.BTreeSet|BTreeSet]]；需要给每个元素附带数据时，用 `HashMap` 的 `keys()` 集合，或者反过来存成 `HashMap<T, 附加数据>`。由于元素一旦进入集合，它的哈希值就不能再变，所以「修改元素」只能先 `take` 出来、改完再 `insert` 回去。

## 常用方法

### 构造

| 方法 | 说明 |
| --- | --- |
| `new()` | 创建空集合，使用默认哈希构建器。 |
| `with_capacity(n)` | 创建空集合并预留至少 `n` 个元素的空间。 |
| `with_hasher(s)` | 用给定的哈希构建器创建空集合。 |
| `with_capacity_and_hasher(n, s)` | 同时指定容量与哈希构建器创建空集合。 |

### 查询与迭代

| 方法 | 说明 |
| --- | --- |
| `contains(v)` | 判断集合中是否存在该值。 |
| `get(v)` | 返回集合中与该值相等的元素引用。 |
| `hasher()` | 返回集合所用 `BuildHasher` 的引用。 |
| `capacity()` | 返回不再重新分配即可容纳的元素数。 |
| `len()` | 返回元素个数。 |
| `is_empty()` | 判断集合是否为空。 |
| `iter()` | 以任意顺序迭代所有元素的引用。 |

### 插入与删除

| 方法 | 说明 |
| --- | --- |
| `insert(v)` | 插入值，返回它是否为新元素。 |
| `replace(v)` | 插入并替换相等的旧元素，返回旧值。 |
| `remove(v)` | 删除值，返回它原来是否存在。 |
| `take(v)` | 删除并返回与该值相等的元素。 |
| `clear()` | 清空集合，保留已分配内存。 |
| `retain(f)` | 只保留谓词返回 `true` 的元素。 |
| `extract_if(pred)` | 迭代并移出满足谓词的元素。 |
| `drain()` | 清空并迭代移出的元素，保留内存。 |

### 集合运算

| 方法 | 说明 |
| --- | --- |
| `difference(other)` | 迭代只在 `self` 中的元素，即差集。 |
| `symmetric_difference(other)` | 迭代只在一侧出现的元素，即对称差。 |
| `intersection(other)` | 迭代两边共有的元素，即交集。 |
| `union(other)` | 迭代两边全部元素并去重，即并集。 |
| `is_disjoint(other)` | 判断两边是否没有公共元素。 |
| `is_subset(other)` | 判断 `self` 是否为 `other` 的子集。 |
| `is_superset(other)` | 判断 `self` 是否为 `other` 的超集。 |

### 容量管理

| 方法 | 说明 |
| --- | --- |
| `reserve(n)` | 预留至少 `n` 个元素的容量。 |
| `try_reserve(n)` | 可失败版本，分配失败返回 `Err`。 |
| `shrink_to_fit()` | 尽量把容量收缩到最小。 |
| `shrink_to(n)` | 收缩容量，但保留至少 `n` 个。 |

## 示例

```rust
use std::collections::HashSet;

fn main() {
    // 从数组构造：重复元素只保留一个
    let a: HashSet<i32> = HashSet::from([1, 2, 2, 3, 4]);
    let b: HashSet<i32> = [3, 4, 5, 6].into_iter().collect();
    assert_eq!(a.len(), 4);
    assert!(a.contains(&2));
    assert!(!a.contains(&9));

    // 四种集合运算的结果都要排序后才好断言（集合本身无序）
    let mut inter: Vec<i32> = a.intersection(&b).copied().collect();
    let mut uni: Vec<i32> = a.union(&b).copied().collect();
    let mut diff: Vec<i32> = a.difference(&b).copied().collect();
    let mut sym: Vec<i32> = a.symmetric_difference(&b).copied().collect();
    inter.sort();
    uni.sort();
    diff.sort();
    sym.sort();
    assert_eq!(inter, vec![3, 4]);
    assert_eq!(uni, vec![1, 2, 3, 4, 5, 6]);
    assert_eq!(diff, vec![1, 2]);
    assert_eq!(sym, vec![1, 2, 5, 6]);

    // 子集、超集、不相交判断
    let small: HashSet<i32> = HashSet::from([1, 2]);
    assert!(small.is_subset(&a));
    assert!(a.is_superset(&small));
    assert!(small.is_disjoint(&HashSet::from([7, 8])));

    // insert 返回是否新插入，remove 返回是否存在
    let mut langs = HashSet::new();
    assert!(langs.insert("rust"));
    assert!(!langs.insert("rust"));
    assert!(langs.remove("rust"));
    assert!(langs.is_empty());
}
```

## 常见陷阱

1. **遍历顺序不可依赖**：`iter()` 与 `into_iter()` 顺序随机且随运行变化。对策：断言前先 `sort`，或改用 `BTreeSet`。
2. **重复插入是静默的**：第二次 `insert` 只返回 `false`，不会报错也不会替换。对策：需要知道「是否已存在」时检查返回值，要保持旧值不变就什么都别做。
3. **元素进入集合后不能再改**：`HashSet` 只提供 `&T`，没有 `iter_mut`。对策：`take` 取出、改完再 `insert`，或改用 `HashMap` 存可变数据。
4. **`contains` 与元素类型不同也能查**：`HashSet<String>` 可以用 `&str` 查询，靠的是 `Borrow`。对策：查 `String` 集合时直接传字符串字面量，不必 `to_string`。
5. **浮点数不能作元素**：`f64` 未实现 `Eq + Hash`，`HashSet<f64>` 编译失败。对策：存`整数化`后的值或包裹类型，并自己实现 `Hash`/`Eq`。

## 相关

- [[collections|std::collections 模块]]：本模块全部条目。
- [[collections.HashMap|HashMap]]：`HashSet` 的底层实现，需要修值时用它。
- [[collections.BTreeSet|BTreeSet]]：有序集合，支持范围查询。
- [[cmp.Eq|Eq]]：集合元素必须实现的特质。
- [[12-集合类型|集合类型]]：去重、求交集等场景的选型对比。
