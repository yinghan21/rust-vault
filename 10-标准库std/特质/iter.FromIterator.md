---
title: "std::iter::FromIterator"
type: std-条目
kind: 特质
module: iter
slug: iter.FromIterator
stable: "1.0.0"
tags:
  - std/特质
  - std/类型
aliases:
  - FromIterator
一句话: 定义类型如何从迭代器构造出来，是 collect 能工作的底层契约。
---

# `FromIterator`

> [!abstract] 一句话
> `FromIterator` 定义「怎么用一堆元素造出一个值」；`Iterator::collect` 的目标类型必须实现它，`Vec`、`String`、`HashMap` 都实现了。

## 简介

`collect` 只是语法糖：`iter.collect::<Vec<_>>()` 实际调用的是 `<Vec<_> as FromIterator<_>>::from_iter(iter)`。所以自定义集合想支持 `collect`，只要为它实现 `FromIterator`。

这个特质带一个泛型参数 `A`（元素类型），而不是关联类型，因此**同一个类型可以对多种元素类型分别实现它**。标准库正是用它一次性覆盖了「容器 + 元素」的所有组合。

与相邻概念区别：`IntoIterator` 负责「值 → 迭代器」，`FromIterator` 负责「迭代器 → 值」，两者合起来才是 `collect`。直接写 `Vec::from_iter(it)` 有时比 `it.collect::<Vec<_>>()` 更好读，尤其是嵌套泛型需要写 turbofish 的时候。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `from_iter(iter)` | 消耗迭代器，构造并返回 `Self`。 |

## 提供的方法

本特质没有提供默认实现的方法，全部构造逻辑都写在 `from_iter` 里。

## 关联类型

本特质没有关联类型：元素类型由特质参数 `A` 指定，例如 `impl FromIterator<i32> for MyBag`。

## 示例

### 标准库里的常见用法

```rust
use std::collections::{BTreeMap, BTreeSet};
use std::iter::FromIterator;

fn main() {
    // Vec 从区间构造
    let v = Vec::from_iter(1..=5);
    assert_eq!(v, vec![1, 2, 3, 4, 5]);

    // String 从字符迭代器构造
    let s = String::from_iter(['中', '文']);
    assert_eq!(s, "中文");

    // BTreeSet 自动去重
    let set: BTreeSet<i32> = (1..=3).chain(2..=4).collect();
    assert_eq!(set.len(), 4);

    // BTreeMap 从键值对构造，后面的覆盖前面的
    let map = BTreeMap::from_iter([("a", 1), ("b", 2), ("a", 3)]);
    assert_eq!(map.get("a"), Some(&3));
    assert_eq!(map.len(), 2);
}
```

### 给自定义类型实现 `FromIterator`

```rust
use std::iter::FromIterator;

#[derive(Debug, PartialEq)]
struct Stats {
    count: usize,
    sum: i32,
}

impl FromIterator<i32> for Stats {
    fn from_iter<T: IntoIterator<Item = i32>>(iter: T) -> Self {
        let mut count = 0;
        let mut sum = 0;
        for x in iter {
            count += 1;
            sum += x;
        }
        Stats { count, sum }
    }
}

fn main() {
    let stats = Stats::from_iter([1, 2, 3, 4]);
    assert_eq!(stats, Stats { count: 4, sum: 10 });

    // collect 走的就是同一条路
    let stats: Stats = (1..=4).collect();
    assert_eq!(stats, Stats { count: 4, sum: 10 });
}
```

## 常见陷阱

1. **`collect` 必须能推断目标类型**：`let v = it.collect();` 会因类型不明而报错，要写 `let v: Vec<_> = it.collect();` 或 `it.collect::<Vec<_>>()`。
2. **`collect` 会消耗迭代器**：同一迭代器只能收集一次，需要多次使用就先 `clone` 或重新构造。
3. **混用 `HashMap` 时后写的键覆盖前面的**：`from_iter` 按顺序插入，重复键以最后一次为准，这一点和 `Vec` 不同。
4. **`String` 只实现了 `FromIterator<char>` 和 `FromIterator<&str>` 等少数组合**：`Vec<String>` 不能直接 `collect` 成 `String`，需要先 `flatten` 或 `join`。
5. **自己实现时别丢元素**：`from_iter` 的契约是吃掉整个迭代器，提前 `return` 会静默丢弃剩余项。

## 相关

- [[iter|std::iter 模块]]：迭代器相关条目总览。
- [[iter.Iterator|Iterator]]：`collect` 方法所在的迭代器主特质。
- [[iter.IntoIterator|IntoIterator]]：反方向的「值 → 迭代器」。
- [[vec.Vec|Vec]]：最常见的 `FromIterator` 实现者。
- [[12-集合类型|集合类型]]：集合构造与 `collect` 的常见组合。
