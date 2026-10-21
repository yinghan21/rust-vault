---
title: "std::cmp::min"
type: std-条目
kind: 函数
module: cmp
slug: cmp.min
stable: "1.0.0"
tags:
  - std/类型
aliases:
  - "min"
  - "cmp::min"
一句话: "按 Ord 比较并返回两个值中较小的那个；两者相等时返回第一个参数，按值传入、按值返回。"
---

# `min`

> [!abstract] 一句话
> `std::cmp::min(a, b)` 比较两个同类型的值，返回较小的那个。两个值相等时**返回第一个参数**。它要求 `T: Ord`，参数按值传入、按值返回。

## 简介

`cmp::min` 是「取两者较小」的通用函数，任何实现了 `Ord` 的类型都能用：整数、`&str`、`String`、`char`、元组、`Vec`（按字典序）、以及你自己 `derive(Ord)` 的结构体与枚举。

它和浮点上的 `f64::min` 方法不是一回事。`Ord` 要求全序，而 `f64` 有 `NaN`，所以 `f64`/`f32` 只实现 `PartialOrd`，**不能**传给 `cmp::min`。要比较浮点，用 `a.min(b)`（`f64` 的方法）或 `partial_cmp` 自己处理 `NaN`。

相等时的取舍值得记住：`cmp::min` 在 `a <= b` 时返回 `a`，也就是说相等时返回**第一个**参数；对应的 `cmp::max` 相等时返回**第二个**参数。两者都保持「传入顺序」的对称性，习惯上让 `min` 偏左、`max` 偏右。这个细节只在类型带有身份信息（例如同一个键绑定不同数据）时才看得出来。

参数按值传入意味着它会**移动**非 `Copy` 类型：`cmp::min(String::from("a"), s)` 之后两个 `String` 都归函数管理，只返回其中一个，另一个被丢弃。要保留所有权就传引用——`&T` 同样实现 `Ord`，`cmp::min(&a, &b)` 返回 `&T`。

## 签名与参数

```text
pub fn min<T: Ord>(v1: T, v2: T) -> T
```

| 参数 | 说明 |
| --- | --- |
| `v1` | 第一个候选值，相等时胜出（返回它）。 |
| `v2` | 第二个候选值，严格更小时返回它。 |
| 返回 `T` | 较小的那个值，所有权随返回值给出。 |

- `T: Ord` 是唯一约束：`f64`、`f32` 不满足（只有 `PartialOrd`），不能直接用。
- 不 panic、不分配；内部按 `Ord` 比较，比较逻辑由你的实现决定。
- 三个及以上取最小，用 `iter().min()` 或 `(a).min(b).min(c)` 链式调用。

## 示例

### 基本比较

```rust
use std::cmp;

fn main() {
    assert_eq!(cmp::min(1, 2), 1);
    assert_eq!(cmp::min(2, 2), 2);   // 相等时返回第一个参数
    assert_eq!(cmp::min(-5, 3), -5);

    // &str 按字典序（逐字节）比较
    assert_eq!(cmp::min("b", "a"), "a");
    assert_eq!(cmp::min("apple", "apricot"), "apple");

    // 传引用就不交出所有权，返回的也是引用
    let a = String::from("zebra");
    let b = String::from("apple");
    let smaller: &String = cmp::min(&a, &b);
    assert_eq!(smaller.as_str(), "apple");
    assert_eq!(a, "zebra");          // a、b 都还在

    println!("{a} {b} {smaller}");
}
```

### 相等时返回第一个参数

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
    // 全部「相等」，min 返回第一个参数
    assert_eq!(cmp::min(Equal("v1"), Equal("v2")).0, "v1");
    // 同样的输入交给 max，返回的是第二个参数
    assert_eq!(cmp::max(Equal("v1"), Equal("v2")).0, "v2");
}
```

## 常见陷阱

1. **拿 `f64` 调 `cmp::min`**：`f64` 没有实现 `Ord`，编译失败；用 `a.min(b)`（`f64` 的方法）或先处理 `NaN`。
2. **以为它会 clone**：参数按值传入，`cmp::min(s1, s2)` 会消耗两个 `String`，只还你一个；保留所有权请传 `&`。
3. **多个值只靠链式 `min`**：`a.min(b).min(c)` 可用，但数组或集合请用 `iter().min()`（返回 `Option<&T>`）更清晰。
4. **忘了 `Ord` 的实现必须与 `PartialOrd`、`Eq` 一致**：手写 `Ord` 却不满足自反/传递性，会让 `min`/`max`/排序给出意外结果。
5. **以为相等时返回哪个无所谓**：带身份信息的类型（例如同键不同载荷）会因此拿到不同的值，`min` 取第一个、`max` 取第二个。
6. **对大结构体按值比较**：`cmp::min(big_struct_a, big_struct_b)` 会把两个大值都搬进函数，传引用更省。

## 相关

- [[cmp|std::cmp 模块]]：`min`、`max`、`Ord`、`Ordering` 都在这里。
- [[cmp.max|max]]：取较大值，相等时返回第二个参数。
- [[cmp.Ord|Ord]]：`min`/`max` 依赖的全序特质，与 `PartialOrd` 的区别在此。
- [[cmp.Ordering|Ordering]]：比较的三种结果变体。
- [[iter.Iterator|Iterator]]：`iter().min()` / `max()` 处理多个值。
