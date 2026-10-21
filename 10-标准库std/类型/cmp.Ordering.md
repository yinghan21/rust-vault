---
title: "std::cmp::Ordering"
type: std-条目
kind: 枚举
module: cmp
slug: cmp.Ordering
stable: "1.0.0"
tags:
  - std/类型
  - rust/基础
aliases:
  - Ordering
一句话: 比较两个值的结果，只有 Less、Equal、Greater 三种取值，是 Ord 与 PartialOrd 的输出类型。
---

# `Ordering`

> [!abstract] 一句话
> `Ordering` 是「比较结果」本身：比对方小是 `Less`，相等是 `Equal`，大是 `Greater`。它把「三态比较」从魔法整数变成了类型。

## 简介

任何实现了 [[cmp.Ord|Ord]] 的类型，`a.cmp(&b)` 都返回 `Ordering`；实现了 [[cmp.PartialOrd|PartialOrd]] 的类型，`a.partial_cmp(&b)` 返回 `Option<Ordering>`（浮点数是 `None` 的典型来源，因为 `NaN` 与任何值都不可比）。

这比 C 的 `strcmp` 返回负数/零/正数安全得多：不会是「随便一个负数」，只能是三个变体之一，`match` 时编译器还会检查你有没有漏掉分支。

几个使用要点：

- `Ordering` 自身实现 `Ord`，顺序是 `Less < Equal < Greater`，所以可以直接排序一个 `Vec<Ordering>`，也可以当 `BTreeMap` 的键。
- `reverse()` 用于把「升序」翻成「降序」，`then()` / `then_with()` 用于**多级排序**：第一关键字相等时再比第二关键字。
- 排序时不需要手写 `match`，`sort_by(|a, b| a.cmp(b))`，或者直接 `sort()`（要求元素实现 `Ord`）。

## 变体

| 变体 | 含义 |
| --- | --- |
| `Less` | 左边小于右边，即 `a < b`。 |
| `Equal` | 两边相等，即 `a == b`。 |
| `Greater` | 左边大于右边，即 `a > b`。 |

## 常用方法

共 9 个稳定方法。

### 判断变体

| 方法 | 说明 |
| --- | --- |
| `is_eq()` | 判断是否为 `Equal`。 |
| `is_ne()` | 判断是否不是 `Equal`。 |
| `is_lt()` | 判断是否为 `Less`。 |
| `is_gt()` | 判断是否为 `Greater`。 |
| `is_le()` | 判断是否为 `Less` 或 `Equal`。 |
| `is_ge()` | 判断是否为 `Greater` 或 `Equal`。 |

### 组合比较结果

| 方法 | 说明 |
| --- | --- |
| `reverse()` | 翻转结果，`Less` 与 `Greater` 互换。 |
| `then()` | 自己相等时才采用另一个比较结果。 |
| `then_with()` | 自己相等时才调用闭包求下一个结果。 |

> [!tip] `then` 与 `then_with` 的区别
> `then(other)` 先算好 `other`，`then_with(|| ...)` 只在需要时才求值。多关键字排序里第二、第三关键字可能有开销（比如拼字符串），用 `then_with` 更划算。

## 示例

### 三种取值与判断

```rust
use std::cmp::Ordering;

fn main() {
    assert_eq!(1.cmp(&2), Ordering::Less);
    assert_eq!(1.cmp(&1), Ordering::Equal);
    assert_eq!(2.cmp(&1), Ordering::Greater);

    assert!(Ordering::Less.is_lt());
    assert!(Ordering::Less.is_le());
    assert!(Ordering::Equal.is_eq());
    assert!(!Ordering::Equal.is_ne());
    assert!(Ordering::Greater.is_ge());

    // reverse 把升序翻成降序
    assert_eq!(Ordering::Less.reverse(), Ordering::Greater);
    assert_eq!(Ordering::Equal.reverse(), Ordering::Equal);

    // 三态结果可以直接 match，编译器会检查分支完整性
    let label = match 3.cmp(&5) {
        Ordering::Less => "小于",
        Ordering::Equal => "等于",
        Ordering::Greater => "大于",
    };
    assert_eq!(label, "小于");
}
```

### 多关键字排序

```rust
use std::cmp::Ordering;

fn main() {
    let mut users = [("amy", 30), ("bob", 25), ("cat", 30)];

    // 先按年龄升序，年龄相同时再按名字升序
    users.sort_by(|a, b| a.1.cmp(&b.1).then_with(|| a.0.cmp(&b.0)));
    assert_eq!(users, [("bob", 25), ("amy", 30), ("cat", 30)]);

    // then 适用于已经算好的比较结果；reverse 用于降序
    users.sort_by(|a, b| b.1.cmp(&a.1).then(Ordering::Equal));
    assert_eq!(users, [("amy", 30), ("cat", 30), ("bob", 25)]);
}
```

## 常见陷阱

1. **用 `as i32` 之类把 `Ordering` 转数字**：官方没有稳定的判别值转换，别依赖 `Less == -1`；需要数字就自己 `match` 出 `-1`、`0`、`1`。
2. **浮点比较得到 `None`**：`partial_cmp` 返回 `Option<Ordering>`，`NaN` 参与时是 `None`；用 `total_cmp`（`f64` 的方法）或显式处理 `None`，不要 `unwrap`。
3. **`sort_by` 里比较方向写反**：`sort_by(|a, b| b.cmp(a))` 才是降序，写反了排序结果看上去「只是有点怪」，很难排查。
4. **自己实现 `Ord` 时与 `PartialOrd` 不一致**：两者结果必须一致（`a.cmp(b) == Equal` 等价于 `a == b`），否则 `sort`、`BTreeMap` 的行为不可预期。
5. **比较闭包里做了昂贵计算**：`sort_by` 会调用 `O(n log n)` 次比较，避免在里面分配字符串或加锁；先预处理成可比较的键再排序。

## 相关

- [[cmp|std::cmp 模块]]：`Ord`、`PartialOrd`、`min`、`max` 都在这里。
- [[cmp.Ord|Ord]]：全序比较特质，`cmp` 返回 `Ordering`。
- [[cmp.PartialOrd|PartialOrd]]：偏序比较特质，`partial_cmp` 返回 `Option<Ordering>`。
- [[option.Option|Option]]：`partial_cmp` 的返回值外层，也是 `then` 的好搭档。
- [[08-枚举与模式匹配|模式匹配]]：用 `match` 处理三个变体是最清晰的写法。
