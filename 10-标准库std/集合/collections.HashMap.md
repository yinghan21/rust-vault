---
title: "std::collections::HashMap"
type: std-条目
kind: 结构体
module: collections
slug: collections.HashMap
stable: "1.0.0"
tags:
  - std/集合
  - std/类型
aliases:
  - HashMap
一句话: 以键值对存储数据的哈希表，平均 O(1) 查找，迭代顺序不固定。
---

# `HashMap<K, V>`

> [!abstract] 一句话
> `HashMap<K, V>` 是哈希表实现的键值映射：按键查找、插入、删除的平均时间复杂度都是 O(1)，代价是**不保证任何遍历顺序**。

## 简介

`HashMap` 是「知道键，想快速拿到值」时的首选容器。它要求键类型实现 `Eq + Hash`——通常写 `#[derive(PartialEq, Eq, Hash)]` 就够了。内部用平方探测加 SIMD 查找，默认哈希算法是随机种子的 SipHash 1-3，专门用来抵御 HashDoS 攻击。

代价有两条：一是**内存开销比 [[vec.Vec|Vec]] 大**（要留空槽位维持低负载因子）；二是**迭代顺序不确定**，而且每次运行都可能不同。需要按顺序遍历时，应该换成 [[collections.BTreeMap|BTreeMap]]，或者把键收集起来排序。

哈希算法可以按实例替换：`default`、`with_hasher`、`with_capacity_and_hasher` 三个构造入口都接受自定义 `BuildHasher`——用小整数或长字符串做键时，换一种更快的哈希器能明显提速，前提是数据不来自不可信输入。

## 常用方法

### 构造

| 方法 | 说明 |
| --- | --- |
| `new()` | 创建空表，使用默认哈希构建器。 |
| `with_capacity(n)` | 创建空表并预留至少 `n` 个元素的空间。 |
| `with_hasher(s)` | 用给定的哈希构建器创建空表。 |
| `with_capacity_and_hasher(n, s)` | 同时指定容量与哈希构建器创建空表。 |

### 查询与访问

| 方法 | 说明 |
| --- | --- |
| `get(k)` | 返回键对应值的引用，缺键返回 `None`。 |
| `get_mut(k)` | 返回键对应值的可变引用。 |
| `get_key_value(k)` | 返回键值对的引用，键可按借用类型查询。 |
| `get_disjoint_mut(ks)` | 一次取多个键的可变引用，含重复键则为 `None`。 |
| `get_disjoint_unchecked_mut(ks)` | 同上，但不检查重复键（`unsafe`）。 |
| `contains_key(k)` | 判断表中是否存在该键。 |
| `hasher()` | 返回表所用 `BuildHasher` 的引用。 |
| `capacity()` | 返回不再重新分配即可容纳的元素数。 |
| `len()` | 返回键值对数量。 |
| `is_empty()` | 判断表是否为空。 |

### 插入与删除

| 方法 | 说明 |
| --- | --- |
| `insert(k, v)` | 插入键值对，返回被覆盖的旧值。 |
| `entry(k)` | 取得键对应的 `Entry`，用于就地增删改。 |
| `remove(k)` | 删除键，返回它原来的值。 |
| `remove_entry(k)` | 删除键，返回键与值两者。 |
| `clear()` | 清空全部键值对，保留已分配内存。 |
| `retain(f)` | 只保留谓词返回 `true` 的键值对。 |
| `extract_if(pred)` | 迭代并移出满足谓词的元素。 |
| `drain()` | 清空并迭代移出的键值对，保留内存。 |

### 迭代

| 方法 | 说明 |
| --- | --- |
| `iter()` | 以任意顺序迭代 `(&K, &V)`。 |
| `iter_mut()` | 以任意顺序迭代 `(&K, &mut V)`。 |
| `keys()` | 以任意顺序迭代所有键的引用。 |
| `into_keys()` | 消耗表，按所有权迭代所有键。 |
| `values()` | 以任意顺序迭代所有值的引用。 |
| `values_mut()` | 以任意顺序可变迭代所有值。 |
| `into_values()` | 消耗表，按所有权迭代所有值。 |

### 容量管理

| 方法 | 说明 |
| --- | --- |
| `reserve(n)` | 预留至少 `n` 个元素的容量。 |
| `try_reserve(n)` | 可失败版本，分配失败返回 `Err`。 |
| `shrink_to_fit()` | 尽量把容量收缩到最小。 |
| `shrink_to(n)` | 收缩容量，但保留至少 `n` 个。 |

## 示例

```rust
use std::collections::HashMap;

fn main() {
    let text = "the quick brown fox jumps over the lazy dog the end";
    let mut counts: HashMap<&str, usize> = HashMap::new();

    // entry + or_insert：键不存在时插入 0，再就地加一
    for word in text.split_whitespace() {
        *counts.entry(word).or_insert(0) += 1;
    }
    assert_eq!(counts["the"], 3);
    assert_eq!(counts.len(), 9);
    assert_eq!(counts.get("fox"), Some(&1));
    assert_eq!(counts.get("cat"), None);
    assert!(counts.contains_key("jumps"));

    // retain 就地过滤：只留下出现两次以上的词
    counts.retain(|_, n| *n > 1);
    assert_eq!(counts.len(), 1);

    // 需要固定顺序时，收集到 Vec 再排序
    let mut pairs: Vec<_> = counts.iter().collect();
    pairs.sort();
    for (word, n) in pairs {
        println!("{word}: {n}");
    }

    // remove 返回被删掉的值
    assert_eq!(counts.remove("the"), Some(3));
    assert!(counts.is_empty());
}
```

## 常见陷阱

1. **遍历顺序不可依赖**：`iter()` 的顺序随机且随运行变化，测试里断言顺序必然偶发失败。对策：断言前先 `sort`，或改用 `BTreeMap`。
2. **`map[k]` 缺键会 panic**：索引语法在键不存在时直接 panic。对策：用 `get` + `Option` 处理，或先 `contains_key` 确认。
3. **浮点数不能当键**：`f64` 没实现 `Eq` 和 `Hash`，无法作为键。对策：用定点整数、字符串，或自行包装并实现所需特质。
4. **`insert` 会丢弃旧值**：返回值被忽略时，覆盖前的数据就悄悄没了。对策：需要保留时接收返回值，或改用 `entry`。
5. **迭代中修改表编译不过**：`iter()` 持有不可变借用，`insert` / `remove` 需要可变借用。对策：先把要改的键收集到 `Vec`，循环结束后再改。

## 相关

- [[collections|std::collections 模块]]：本模块全部条目。
- [[collections.HashSet|HashSet]]：只存键、不存值的版本。
- [[collections.BTreeMap|BTreeMap]]：按键有序的映射，适合范围查询。
- [[hash.Hash|Hash]]：作为键的类型必须实现的特质。
- [[12-集合类型|集合类型]]：`Vec`、`HashMap`、`HashSet` 的选型对比。
