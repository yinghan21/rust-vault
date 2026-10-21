---
title: "std::iter::Extend"
type: std-条目
kind: 特质
module: iter
slug: iter.Extend
stable: "1.0.0"
tags:
  - std/特质
  - std/类型
aliases:
  - Extend
一句话: 用迭代器的内容扩展现有集合，是 extend 方法背后的特质。
---

# `Extend`

> [!abstract] 一句话
> `Extend` 定义「把迭代器里的元素追加进已有集合」的规则，`Vec::extend`、`String::extend`、`HashMap::extend` 都由它提供。

## 简介

迭代器能产出一串值，集合本身也是一串值，`Extend` 就是两者之间的桥：`collection.extend(iter)` 把 `iter` 的元素逐个塞进集合末尾。它和 `FromIterator` 的区别在于**目标已存在**——`collect` 新建容器，`extend` 往旧容器里续。

对映射类集合，`extend` 的语义是「插入或更新」：键已存在就覆盖值，允许重复键的集合则直接再插一条。因为接受 `IntoIterator`，`extend` 能吃数组、区间、`Vec`、其它迭代器，写法比循环 `push` 更短，也更容易被编译器优化。

`Extend` 也是 `Iterator::unzip` 和 `Iterator::partition` 的约束之一（`B: Default + Extend<Self::Item>`），理解它就理解了这些方法的返回类型要求。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `extend(iter)` | 把 `iter` 的全部元素追加进 `self`。 |

## 提供的方法

本特质没有提供默认实现的方法；需要一次性插入大量元素时，实现里通常配合 `reserve` 预留容量。

## 关联类型

本特质没有关联类型：元素类型由特质参数 `A` 指定，例如 `impl Extend<i32> for MyBag`。

## 示例

### 标准库集合的 `extend`

```rust
use std::collections::{BTreeMap, BTreeSet};

fn main() {
    // Vec 追加区间
    let mut v = vec![1, 2, 3];
    v.extend(4..=5);
    assert_eq!(v, vec![1, 2, 3, 4, 5]);

    // String 追加字符
    let mut s = String::from("ab");
    s.extend(['c', 'd']);
    assert_eq!(s, "abcd");

    // BTreeSet 去重
    let mut set = BTreeSet::from([3]);
    set.extend([1, 2, 3]);
    assert_eq!(set.len(), 3);

    // BTreeMap 同键覆盖
    let mut m = BTreeMap::new();
    m.extend([("a", 1), ("b", 2)]);
    m.extend([("a", 3)]);
    assert_eq!(m.get("a"), Some(&3));
    assert_eq!(m.len(), 2);
}
```

### 给自定义类型实现 `Extend`

```rust
#[derive(Debug)]
struct Bag(Vec<i32>);

impl Bag {
    fn new() -> Bag {
        Bag(Vec::new())
    }
}

impl Extend<i32> for Bag {
    fn extend<T: IntoIterator<Item = i32>>(&mut self, iter: T) {
        for x in iter {
            self.0.push(x);
        }
    }
}

fn main() {
    let mut bag = Bag::new();
    bag.extend([1, 2]);
    bag.extend(3..=4);
    assert_eq!(format!("{:?}", bag), "Bag([1, 2, 3, 4])");
}
```

## 常见陷阱

1. **`extend` 不清空原集合**：它是在末尾追加；想要覆盖请先 `clear()`，或直接用 `collect` 造新容器。
2. **`extend` 会消耗参数**：传入 `Vec` 会移走所有权，之后再想用原 `Vec` 需要改传 `&v`（此时元素需 `Copy` 或集合接受引用）。
3. **映射类型是覆盖语义**：`HashMap::extend` 遇到重复键会覆盖旧值，不会报错，容易丢掉先前数据。
4. **频繁 `extend` 会反复扩容**：已知总量时先 `reserve`，比多次小批量追加更省。
5. **`String::extend` 只接受 `char`、`&str`、`String` 等少数元素类型**：传 `Vec<u8>` 会因 `IntoIterator<Item = u8>` 不匹配而编译失败。

## 相关

- [[iter|std::iter 模块]]：迭代器相关条目总览。
- [[iter.FromIterator|FromIterator]]：从迭代器新建容器，与 `Extend` 互为补充。
- [[iter.IntoIterator|IntoIterator]]：`extend` 参数要求的特质。
- [[iter.Iterator|Iterator]]：`unzip`、`partition` 依赖 `Extend` 作为约束。
- [[12-集合类型|集合类型]]：各集合追加元素的实际用法。
