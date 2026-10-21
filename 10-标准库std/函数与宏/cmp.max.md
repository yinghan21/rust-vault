---
title: "std::cmp::max"
type: std-条目
kind: 函数
module: cmp
slug: cmp.max
stable: "1.0.0"
tags:
  - std/类型
aliases:
  - "max"
  - "cmp::max"
一句话: "按 Ord 比较并返回两个值中较大的那个；两者相等时返回第二个参数，与 min 的取舍方向相反。"
---

# `max`

> [!abstract] 一句话
> `std::cmp::max(a, b)` 比较两个同类型的值，返回较大的那个。两个值相等时**返回第二个参数**——这是它与 [[cmp.min|min]] 唯一的方向性差别。要求 `T: Ord`，按值传入、按值返回。

## 简介

`cmp::max` 是「取两者较大」的通用函数，适用于所有实现 `Ord` 的类型：整数、`char`、`&str`、`String`、元组、`Vec`（字典序）、以及 `derive(Ord)` 的结构体。它在求上界、夹取范围、取最新时间戳这类场景里最常用。

和浮点要区分开：`f64` 有 `NaN`，做不到全序，只实现 `PartialOrd`，所以 `cmp::max(1.0, 2.0)` 编译不过；浮点要用 `a.max(b)` 方法，并注意它遇到 `NaN` 时的返回规则（`f64::max` 会返回另一个非 `NaN` 的操作数）。

相等时的取舍是 `max` 经常被问的细节：`cmp::max` 在 `b >= a` 时返回 `b`，也就是相等时返回**第二个**参数；而 `cmp::min` 相等时返回**第一个**参数。所以对「比较结果相同但载荷不同」的类型，`min` 偏左、`max` 偏右，这个对称设计让 `min(a, b)` 与 `max(a, b)` 不会同时返回同一个对象。

参数按值传入，非 `Copy` 类型会被消耗：另一个值在函数内部被丢弃。想保留所有权就传引用，`&T` 也实现 `Ord`，此时返回的是 `&T`。

## 签名与参数

```text
pub fn max<T: Ord>(v1: T, v2: T) -> T
```

| 参数 | 说明 |
| --- | --- |
| `v1` | 第一个候选值，严格更大时返回它，相等时落选。 |
| `v2` | 第二个候选值，相等时胜出（返回它）。 |
| 返回 `T` | 较大的那个值，所有权随返回值给出。 |

- `T: Ord` 是唯一约束：`f64`、`f32` 不满足，请用其自带的 `max` 方法。
- 不 panic、不分配；比较逻辑完全由 `T` 的 `Ord` 实现决定。
- 三个及以上取最大，用 `iter().max()` 或链式 `a.max(b).max(c)`。

## 示例

### 基本比较

```rust
use std::cmp;

fn main() {
    assert_eq!(cmp::max(1, 2), 2);
    assert_eq!(cmp::max(2, 2), 2);   // 相等时返回第二个参数
    assert_eq!(cmp::max(-5, 3), 3);

    // &str 按字典序比较
    assert_eq!(cmp::max("apple", "apricot"), "apricot");

    // 传引用：返回值也是引用，两个 String 都保留
    let a = String::from("zebra");
    let b = String::from("apple");
    let bigger: &String = cmp::max(&a, &b);
    assert_eq!(bigger.as_str(), "zebra");
    assert_eq!(b, "apple");

    // 多个值交给迭代器
    let largest = [3, 1, 4, 1, 5].into_iter().max().unwrap();
    assert_eq!(largest, 5);

    println!("{a} {b} {bigger} {largest}");
}
```

### 相等时返回第二个参数

```rust
use std::cmp::{self, Ordering};

// 一个把任何值都视为「相等」的类型，用来观察取舍规则
#[derive(Eq)]
struct Equal(&'static str);

impl PartialEq for Equal {
    fn eq(&self, _other: &Self) -> bool { true }
}
impl PartialOrd for Equal {
    fn partial_cmp(&self, _other: &Self) -> Option<Ordering> { Some(Ordering::Equal) }
}
impl Ord for Equal {
    fn cmp(&self, _other: &Self) -> Ordering { Ordering::Equal }
}

fn main() {
    // 全部「相等」，max 返回第二个参数
    assert_eq!(cmp::max(Equal("v1"), Equal("v2")).0, "v2");
    // 同样的输入交给 min，返回的是第一个参数
    assert_eq!(cmp::min(Equal("v1"), Equal("v2")).0, "v1");
}
```

## 常见陷阱

1. **对 `f64` 用 `cmp::max`**：`f64` 只有 `PartialOrd`，编译报 `Ord` 未满足；改用 `a.max(b)`，并想清楚 `NaN` 应该怎么处理。
2. **以为 `max` 相等时返回第一个**：返回的是第二个；带身份信息的类型会因此拿到不同的值，`min` 才返回第一个。
3. **按值传大结构体**：`cmp::max(a, b)` 会把两个值都搬进函数，另一个被丢弃；只比较不消耗就传引用。
4. **手写 `Ord` 与 `PartialOrd` 不一致**：`max` 的结果依赖 `Ord`，两者不一致会让比较结果自相矛盾，`sort`、`BTreeMap` 也会跟着出问题。
5. **用 `max` 夹取范围**：`cmp::max(lo, cmp::min(x, hi))` 可行，但 `x.clamp(lo, hi)` 更直接（`Ord` 与 `PartialOrd` 都有 `clamp`）。
6. **对 `Option`/`Result` 直接 `max`**：它们实现 `Ord` 但语义是按变体序号比较（`None < Some`），通常你想比较的是里面的值，先 `unwrap_or`。

## 相关

- [[cmp|std::cmp 模块]]：`min`、`max` 与比较相关特质的总入口。
- [[cmp.min|min]]：取较小值，相等时返回第一个参数。
- [[cmp.Ord|Ord]]：`max` 依赖的全序特质，与 `PartialOrd` 的区别在此。
- [[cmp.Ordering|Ordering]]：`Less`、`Equal`、`Greater` 三种比较结果。
- [[iter.Iterator|Iterator]]：`iter().max()` 处理多个候选值。
