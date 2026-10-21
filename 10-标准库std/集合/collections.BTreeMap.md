---
title: "std::collections::BTreeMap"
type: std-条目
kind: 结构体
module: collections
slug: collections.BTreeMap
stable: "1.0.0"
tags:
  - std/集合
  - std/类型
aliases:
  - BTreeMap
一句话: 基于 B 树实现的有序映射，键始终按 Ord 升序排列，支持区间查询。
---

# `BTreeMap<K, V>`

> [!abstract] 一句话
> `BTreeMap<K, V>` 是按键有序的映射：所有遍历都按键的 `Ord` 升序进行，并支持用 `range` 做区间查询，单次操作 O(log n)。

## 简介

`BTreeMap` 和 [[collections.HashMap|HashMap]] 都是键值映射，区别在于它**维护键的顺序**。因此 `iter`、`keys`、`values`、`into_iter` 全都按键升序返回，`first_key_value` / `last_key_value` 能直接拿到最小与最大的键，`range` 能按区间切片。

代价是每次操作要 O(log n) 而不是平均 O(1)，常数也比哈希表大。选型规则：只要需要顺序输出、范围查询、或者要按顺序找「前一个/后一个」键，就用 `BTreeMap`；纯粹高频乱序查找用 `HashMap`。

键必须实现 `Ord`（全序），字符串按字典序、数字按自然序。和 `HashSet` 不同，这里不需要 `Hash`。键一旦插入就不能再修改其排序相关字段，否则属于逻辑错误——行为未定义到该映射内部，可能 panic 或产生错误结果。

## 常用方法

### 构造与整体操作

| 方法 | 说明 |
| --- | --- |
| `new()` | 创建空的有序映射。 |
| `clear()` | 清空全部键值对。 |
| `append(other)` | 把另一映射的元素全部移入，并清空它。 |
| `split_off(k)` | 在键处拆分，返回键及其后的部分。 |

### 按键查询

| 方法 | 说明 |
| --- | --- |
| `get(k)` | 返回键对应值的引用，缺键返回 `None`。 |
| `get_mut(k)` | 返回键对应值的可变引用。 |
| `get_key_value(k)` | 返回键值对的引用，键可按借用类型查询。 |
| `contains_key(k)` | 判断映射中是否存在该键。 |
| `len()` | 返回键值对数量。 |
| `is_empty()` | 判断映射是否为空。 |

### 首尾元素

| 方法 | 说明 |
| --- | --- |
| `first_key_value()` | 返回最小键的键值对。 |
| `first_entry()` | 返回最小键的 `Entry`，可就地改写。 |
| `pop_first()` | 移除并返回最小键的键值对。 |
| `last_key_value()` | 返回最大键的键值对。 |
| `last_entry()` | 返回最大键的 `Entry`，可就地改写。 |
| `pop_last()` | 移除并返回最大键的键值对。 |

### 插入、删除与改写

| 方法 | 说明 |
| --- | --- |
| `insert(k, v)` | 插入键值对，返回被覆盖的旧值。 |
| `entry(k)` | 取得键对应的 `Entry`，用于就地增删改。 |
| `remove(k)` | 删除键，返回它原来的值。 |
| `remove_entry(k)` | 删除键，返回键与值两者。 |
| `retain(f)` | 只保留谓词返回 `true` 的键值对。 |
| `extract_if(range, pred)` | 在区间内移出满足谓词的元素并迭代。 |

### 区间与遍历

| 方法 | 说明 |
| --- | --- |
| `range(r)` | 迭代区间内的键值对，按键升序。 |
| `range_mut(r)` | 迭代区间内的键值对，值可修改。 |
| `iter()` | 按键升序迭代 `(&K, &V)`。 |
| `iter_mut()` | 按键升序迭代 `(&K, &mut V)`。 |
| `keys()` | 按键升序迭代所有键的引用。 |
| `into_keys()` | 消耗映射，按键升序迭代所有键。 |
| `values()` | 按键顺序迭代所有值的引用。 |
| `values_mut()` | 按键顺序可变迭代所有值。 |
| `into_values()` | 消耗映射，按键顺序迭代所有值。 |

## 示例

```rust
use std::collections::BTreeMap;

fn main() {
    // 从数组构造
    let mut scores: BTreeMap<&str, i32> = BTreeMap::from([
        ("carol", 78),
        ("alice", 92),
        ("bob", 85),
    ]);

    // 迭代顺序就是键的升序，与插入顺序无关
    let names: Vec<&&str> = scores.keys().collect();
    assert_eq!(names, vec![&"alice", &"bob", &"carol"]);

    // 首尾元素是键的最小值与最大值
    assert_eq!(scores.first_key_value(), Some((&"alice", &92)));
    assert_eq!(scores.last_key_value(), Some((&"carol", &78)));

    // range 是左闭右开区间
    let mid: Vec<i32> = scores.range("alice".."carol").map(|(_, v)| *v).collect();
    assert_eq!(mid, vec![92, 85]);

    // entry 就地插入，split_off 把大键那一半拆出去
    *scores.entry("dave").or_insert(0) = 60;
    let high = scores.split_off("carol");
    assert_eq!(high.len(), 2);
    assert_eq!(scores.len(), 2);

    // 按顺序拿走两端
    assert_eq!(scores.pop_first(), Some(("alice", 92)));
    assert_eq!(scores.pop_last(), Some(("bob", 85)));
    assert!(scores.is_empty());
}
```

## 常见陷阱

1. **键必须实现 `Ord`**：`f64` 只有 `PartialOrd`，不能直接做键。对策：换成定点整数或字符串键，或自己包装并实现 `Ord`。
2. **`range` 默认左闭右开**：`range("a".."c")` 不含 `"c"`，想包含上界要写 `"a"..="c"`。对策：先用小数据验证边界，再放开。
3. **比 `HashMap` 慢常数倍**：每次操作 O(log n) 且要比较键。对策：只要无序的键值查找就换 `HashMap`，需要顺序时才用 `BTreeMap`。
4. **键插入后不能再改**：没有 `key_mut` 之类的接口。对策：`remove_entry` 取出键值、改完再 `insert` 回去。
5. **`split_off` 会重新分配整棵树**：它返回一个新的 `BTreeMap`，不是视图。对策：只想切片遍历时用 `range`，不要 `split_off`。

## 相关

- [[collections|std::collections 模块]]：本模块全部条目。
- [[collections.HashMap|HashMap]]：无需顺序时的更快的选择。
- [[collections.BTreeSet|BTreeSet]]：只存键的有序集合。
- [[cmp.Ord|Ord]]：`BTreeMap` 键必须实现的全序特质。
- [[ops.Range|Range]]：`range` 方法接受的区间类型。
