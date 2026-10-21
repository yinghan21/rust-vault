---
title: "std::cmp"
type: std-模块
module: cmp
stable: "1.0.0"
unstable: false
tags:
  - std/模块
  - std/特质
aliases:
  - cmp
  - 比较与排序
一句话: 比较与排序的基础设施：`PartialEq`/`Eq`/`PartialOrd`/`Ord` 四个特质、三值比较结果 `Ordering`，以及 `min`/`max` 家族。
---

# std::cmp

> [!abstract] 一句话
> `std::cmp` 定义相等与顺序的比较特质，返回 `Ordering`，并提供 `min`、`max`、`Reverse` 等排序工具。

## 模块简介

比较在 Rust 里是特质化的：`==` 走 `PartialEq`，`<`、`>` 走 `PartialOrd` 并返回 `Ordering`（`Less` / `Equal` / `Greater` 三值，而不是布尔）。`Eq` 和 `Ord` 是更强的承诺——它们要求比较满足全序或等价关系，因此能用作 `BTreeMap` 的键或 `sort` 的依据。

为什么分成「Parti」和「全」两套？因为浮点数。`f64` 的 `NaN` 不等于任何值（包括自己），所以 `f64` 只实现 `PartialEq` / `PartialOrd`，`partial_cmp` 返回 `Option<Ordering>`。这避免了在类型系统里假装存在一个「无法比较」的全序。

日常写代码时，`#[derive(PartialEq, Eq, PartialOrd, Ord)]` 会按字段**声明顺序**生成逐字段比较；先比较第一个字段，相等再看第二个。这个顺序决定了结构体在 `BTreeMap` 和 `sort` 中的排序结果，调整字段顺序会静默改变排序。

模块顶层的 `min`、`max` 及其 `_by`、`_by_key` 变体是常用的小工具，`Reverse` 则是把任意 `Ord` 类型的顺序翻转的包装器，常配合 `sort_by_key`、`BinaryHeap` 做降序。

## 快速上手

```rust
use std::cmp::{max, min, Ordering, Reverse};

fn main() {
    // 自由函数：直接取最小值 / 最大值
    assert_eq!(min(3, 7), 3);
    assert_eq!(max('a', 'z'), 'z');

    // Ordering 是三值比较结果
    let ord = 2.cmp(&5);
    assert_eq!(ord, Ordering::Less);

    // 链式比较：先按第一个键，相等时再看第二个键
    let by_name = "alice".cmp("bob");
    let by_age = 30.cmp(&25);
    assert_eq!(by_name.then(by_age), Ordering::Less);

    // Reverse 反转顺序，配合排序得到降序
    let mut scores = vec![3, 1, 2];
    scores.sort_by_key(|&n| Reverse(n));
    assert_eq!(scores, vec![3, 2, 1]);

    // 自定义比较：按字符串长度排序
    let mut words = vec!["ccc", "a", "bb"];
    words.sort_by_key(|w| w.len());
    assert_eq!(words, vec!["a", "bb", "ccc"]);
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[cmp.Ordering|Ordering]] | 比较结果枚举：`Less`、`Equal`、`Greater`。 |
| [[cmp.PartialEq|PartialEq]] | `==` 与 `!=` 对应的相等比较特质。 |
| [[cmp.Eq|Eq]] | 等价关系标记特质，可作为 `HashMap` 键的约束。 |
| [[cmp.PartialOrd|PartialOrd]] | `<`、`>` 等运算符对应的偏序特质。 |
| [[cmp.Ord|Ord]] | 全序特质，`cmp` 返回 `Ordering`。 |
| [[cmp.min|min]] | 返回两个值中较小的一个。 |
| [[cmp.max|max]] | 返回两个值中较大的一个。 |
| `cmp::min_by` / `cmp::max_by` | 用自定义比较函数取最小 / 最大值。 |
| `cmp::min_by_key` / `cmp::max_by_key` | 按提取出的键取最小 / 最大值。 |
| `cmp::Reverse` | 包装类型，把 `Ord` 的顺序反过来。 |
| `#[derive(PartialEq, Eq, PartialOrd, Ord)]` | 按字段声明顺序生成逐字段比较。 |
| `f64::partial_cmp` | 浮点比较返回 `Option<Ordering>`，`NaN` 得到 `None`。 |
| `Ordering::then` | 前一个比较相等时，继续用后一个比较。 |

## 注意事项

> [!danger] `NaN` 破坏全序
> `f64` 只实现 `PartialOrd`，`partial_cmp` 返回 `Option<Ordering>`，遇到 `NaN` 得到 `None`；因此浮点数组不能直接用 `sort`（它要求 `Ord`）。需要确定顺序时用 `f64::total_cmp` 配合 `sort_by`。

> [!warning] 派生比较依赖字段顺序
> `#[derive(PartialOrd, Ord)]` 按字段声明顺序比较，字段顺序变了排序结果就变。需要自定义顺序时手写 `impl Ord`，或只在内部表示上派生、对外提供独立比较函数。

> [!tip] 别用 `==` 比较浮点
> 浮点相等判断容易受舍入误差影响，用 `(a - b).abs() < EPS` 做近似比较，或比较 `to_bits()` 得到的整数。

## 相关

- [[cmp.Ordering|Ordering]]：比较结果与 `then` 等方法。
- [[collections.BTreeMap|BTreeMap]]：依赖 `Ord` 保持按键有序。
- [[hash|std::hash 模块]]：`HashMap` 需要的 `Hash` 与 `Eq`。
- [[12-集合类型|集合类型]]：排序、去重与集合选择。
- [[15-trait 基础|trait 基础]]：实现与派生比较特质。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 21 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`Reverse`](https://doc.rust-lang.org/std/cmp/struct.Reverse.html)

### 枚举

- [[cmp.Ordering|`Ordering`]]

### 特质

- [[cmp.Eq|`Eq`]]
- [[cmp.Ord|`Ord`]]
- [[cmp.PartialEq|`PartialEq`]]
- [[cmp.PartialOrd|`PartialOrd`]]

### 函数

- [[cmp.max|`max`]]
- [`max_by`](https://doc.rust-lang.org/std/cmp/fn.max_by.html)
- [`max_by_key`](https://doc.rust-lang.org/std/cmp/fn.max_by_key.html)
- [[cmp.min|`min`]]
- [`min_by`](https://doc.rust-lang.org/std/cmp/fn.min_by.html)
- [`min_by_key`](https://doc.rust-lang.org/std/cmp/fn.min_by_key.html)
- [`largest`](https://doc.rust-lang.org/std/cmp/fn.largest.html)
- [`minmax`](https://doc.rust-lang.org/std/cmp/fn.minmax.html)
- [`minmax_by`](https://doc.rust-lang.org/std/cmp/fn.minmax_by.html)
- [`minmax_by_key`](https://doc.rust-lang.org/std/cmp/fn.minmax_by_key.html)
- [`smallest`](https://doc.rust-lang.org/std/cmp/fn.smallest.html)

### 其他

- [[cmp.Eq|`Eq`]]
- [[cmp.Ord|`Ord`]]
- [[cmp.PartialEq|`PartialEq`]]
- [[cmp.PartialOrd|`PartialOrd`]]

<!-- END AUTO ITEMS -->
