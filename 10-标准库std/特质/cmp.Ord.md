---
title: "std::cmp::Ord"
type: std-条目
kind: 特质
module: cmp
slug: cmp.Ord
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - Ord
一句话: 定义全序比较 cmp，任何两个值都能分出大小，是排序与 BTreeMap 的前提。
---

# Ord

> [!abstract] 一句话
> `Ord` 在 [[cmp.Eq|Eq]] 和 [[cmp.PartialOrd|PartialOrd]] 之上要求「任意两个值都能比出大小」，核心方法 `cmp` 直接返回 `Ordering` 而不是 `Option`。`f64` 因 `NaN` 破坏三分律被排除，所以浮点不能直接排序。

## 简介

定义是 `pub trait Ord: Eq + PartialOrd<Self> { fn cmp(&self, other: &Self) -> Ordering; }`。注意两点：`Rhs` 被固定为 `Self`（全序不允许跨类型比较），以及返回类型没有 `Option`——`cmp` 必须给每个输入一个确定答案。

`Ord` 是**全序**：对任意 `a`、`b`，`a < b`、`a == b`、`a > b` 三者恰有一个成立（三分律）。而 [[cmp.PartialOrd|PartialOrd]] 允许「谁都不成立」，也就是不可比。这就是 `f64` 卡住的地方：`NaN` 与任何值的三个关系全为假，三分律被打破。

除了继承来的要求，`Ord` 还要求 `cmp` 与 `max`、`min`、`clamp` 的结果一致，且 `cmp` 与 `PartialEq::eq` 一致（`cmp` 返回 `Equal` 当且仅当 `eq` 为真）。违反这些是**逻辑错误**：标准库不保证由此产生的行为，但绝不会因此出现未定义行为，`unsafe` 代码也不能依赖这些方法的正确性。

实践中实现 `Ord` 有两条路。简单类型直接 `#[derive(PartialEq, Eq, PartialOrd, Ord)]`，四个 trait 一起派生，逻辑天然一致。需要自定义顺序时手写 `cmp`，并且**只写这一份逻辑**：`partial_cmp` 返回 `Some(self.cmp(other))`，`eq` 用 `self.cmp(other) == Ordering::Equal`。否则两套逻辑各写一遍，迟早不一致，clippy 的 `derive_ord_xor_partial_ord` 就是在防这个。

### 为什么 f64 不实现 Ord

`f64` 只有 `PartialOrd`。原因不在于「浮点不精确」这种含糊说法，而在于三分律：

| 表达式 | 结果 |
| --- | --- |
| `NaN < 1.0` | `false` |
| `NaN == 1.0` | `false` |
| `NaN > 1.0` | `false` |

三个都为假，`cmp` 无从返回。硬要编一个答案（比如把 `NaN` 当作最大）就会破坏「相等则同哈希、相同则同序」的连锁约定，排序结果依赖于输入顺序，二分查找也可能失效。

实际需要的通常是「按某种确定顺序排」而不是数学上的全序，所以标准库给了 `f64::total_cmp`：它按 IEEE 754 的 `totalOrder` 定义比较，把 `NaN`、`-0.0`、`0.0` 都排进确定位置。用它配 `sort_by` 即可；只是它不构成 `Ord` 实现，所以 `BTreeMap<f64, _>` 依旧编译不过。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `cmp()` | 比较两者并返回 `Ordering`，供排序与有序容器使用。 |

签名是 `fn cmp(&self, other: &Self) -> Ordering`。借用两个值，不消耗它们；必须是反对称且传递的。

## 提供的方法

| 方法 | 说明 |
| --- | --- |
| `max()` | 返回两个值中较大的一个，相等时返回 `other`。 |
| `min()` | 返回两个值中较小的一个，相等时返回 `self`。 |
| `clamp()` | 把值限制在 `min..=max` 区间内。 |

签名分别是 `fn max(self, other: Self) -> Self`、`fn min(self, other: Self) -> Self`、`fn clamp(self, min: Self, max: Self) -> Self`，三者都要求 `Self: Sized` 并按值消耗参数（`i32` 这类 `Copy` 类型看不出差别）。`max`、`min` 稳定于 1.21.0，`clamp` 稳定于 1.50.0。

两个细节：`clamp` 在 `min > max` 时 panic；两个值相等时 `max` 返回第二个参数、`min` 返回第一个参数，对带身份的类型（引用、句柄）这一点会影响结果。

## 与相邻 trait 的关系

| 维度 | `PartialOrd` | `Ord` |
| --- | --- | --- |
| 序的类型 | 部分序，可有不可比 | 全序，任意两值可比 |
| 核心方法 | `partial_cmp` 返回 `Option<Ordering>` | `cmp` 返回 `Ordering` |
| supertrait | `PartialEq` | `Eq` + `PartialOrd` |
| `f64` | 实现 | 不实现（`NaN` 破坏三分律） |
| 排序 API | `sort_by`、`sort_by_key` | `sort`、`sort_unstable`、`BinaryHeap`、`BTreeMap` |
| 派生 | `#[derive(PartialOrd)]` | `#[derive(Ord)]`，要求字段全为 `Ord` |

继承链是 `Eq: PartialEq`，`Ord: Eq + PartialOrd`，所以一个 `Ord` 类型自动是 `Eq`、`PartialEq`、`PartialOrd`。反过来，只实现 `Ord` 而不实现 `PartialOrd` 是不允许的——编译器会要求补上 `PartialOrd`。

这也划出了容器的分工：`HashMap` 要的是 [[hash.Hash|Hash]] + `Eq`（无序、靠哈希），`BTreeMap`、`BTreeSet`、`BinaryHeap` 要的是 `Ord`（有序、靠比较）。`Ord` 类型还能直接用 `==`，因为 `Eq` 是它的 supertrait。

## 示例

### 派生并按字段顺序排序

```rust
#[derive(PartialEq, Eq, PartialOrd, Ord, Debug)]
struct Point {
    x: i32,
    y: i32,
}

fn main() {
    let mut points = vec![
        Point { x: 1, y: 2 },
        Point { x: 1, y: 1 },
        Point { x: 0, y: 9 },
    ];

    // 派生实现按字段声明顺序比较：先 x，再 y
    points.sort();

    assert_eq!(points[0], Point { x: 0, y: 9 });
    assert_eq!(points[1], Point { x: 1, y: 1 });
    assert_eq!(points[2].y, 2);
}
```

### 手写 cmp 并在 partial_cmp 中委托

```rust
use std::cmp::Ordering;

#[derive(Debug, PartialEq, Eq)]
struct Task {
    priority: u8,
    id: u32,
}

impl Ord for Task {
    fn cmp(&self, other: &Self) -> Ordering {
        // 数字小的优先级高，排前面；同优先级按 id 稳定区分
        self.priority.cmp(&other.priority).then(self.id.cmp(&other.id))
    }
}

impl PartialOrd for Task {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        // 只有一份比较逻辑，全序，永远比得出来
        Some(self.cmp(other))
    }
}

fn main() {
    let mut tasks = vec![
        Task { priority: 2, id: 1 },
        Task { priority: 1, id: 9 },
        Task { priority: 2, id: 0 },
    ];
    tasks.sort();

    assert_eq!(tasks[0], Task { priority: 1, id: 9 });
    assert_eq!(tasks[1], Task { priority: 2, id: 0 });
    assert_eq!(tasks.iter().max().map(|t| t.id), Some(1));
}
```

### max、min 与 clamp

```rust
fn main() {
    assert_eq!(7.clamp(1, 5), 5);
    assert_eq!((-3).clamp(1, 5), 1);
    assert_eq!(3.clamp(1, 5), 3);

    // max/min 按值消耗，i32 是 Copy，原变量仍可用
    let label = 3.max(8);
    assert_eq!(label, 8);

    let mut values = vec![3, 1, 2];
    values.sort();
    assert_eq!(values, vec![1, 2, 3]);
    assert_eq!(values.iter().max(), Some(&3));
}
```

### 有序映射按键的 Ord 顺序遍历

```rust
use std::collections::BTreeMap;

fn main() {
    let mut scores = BTreeMap::new();
    scores.insert(3, "c");
    scores.insert(1, "a");
    scores.insert(2, "b");

    let keys: Vec<_> = scores.keys().copied().collect();
    assert_eq!(keys, vec![1, 2, 3]);
    // 键有全序，才能按区间取子集
    assert_eq!(scores.range(2..).count(), 2);
}
```

## 常见陷阱

1. **手写 `Ord` 却派生 `PartialOrd`**：`<` 走一套逻辑、`cmp` 走另一套，排序结果与比较结果矛盾。手写 `Ord` 时 `partial_cmp` 必须返回 `Some(self.cmp(other))`。
2. **`cmp` 与 `eq` 不一致**：例如 `cmp` 只比价格、`eq` 比全部字段。`BTreeMap` 会把「不相等但 `cmp` 相等」的两个键视为同一个，插入时悄悄覆盖。
3. **给含 `f64` 字段的结构体派生 `Ord`**：编译失败；要么把字段换成整数，要么手写 `cmp` 并在其中用 `total_cmp`。
4. **以为 `sort` 和 `sort_by` 只差写法**：`sort` 要求 `Ord`，实现稳定排序；`sort_unstable` 更快但相等元素顺序不保证。
5. **`max`/`min` 当成借用方法用**：它们按值接收 `self` 与 `other`，想保留原值就得 `Copy` 或先 `clone`；在累加循环里 `acc = acc.max(x)` 会移动 `acc`。
6. **`clamp` 参数顺序写反**：`min > max` 直接 panic，提前用 `assert!(min <= max)` 或调整调用顺序。
7. **自定义比较只比部分字段却要求 `Eq` 一致**：`Ord` 的 `Equal` 必须与 `PartialEq` 的 `true` 完全对应，二者错开会出现「能插入两个相等键」的怪象。

## 相关

- [[cmp|std::cmp 模块]]：`Ord` 所属模块。
- [[cmp.PartialOrd|PartialOrd]]：`Ord` 的强约束版本，允许不可比。
- [[cmp.Eq|Eq]]：`Ord` 的 supertrait，提供相等语义。
- [[cmp.Ordering|Ordering]]：`cmp` 的返回值。
- [[collections.BTreeMap|BTreeMap]]、[[collections.BTreeSet|BTreeSet]]：要求键实现 `Ord`。
- [[primitive.浮点类型|f64]]：没有全序，因此不实现 `Ord`。
