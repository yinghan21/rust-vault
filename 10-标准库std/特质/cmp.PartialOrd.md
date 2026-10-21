---
title: "std::cmp::PartialOrd"
type: std-条目
kind: 特质
module: cmp
slug: cmp.PartialOrd
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - PartialOrd
一句话: 定义 <、<=、>、>= 与 partial_cmp，允许「无法比较」返回 None，因此 f64 也能实现。
---

# PartialOrd

> [!abstract] 一句话
> `PartialOrd` 让类型支持 `<`、`<=`、`>`、`>=`，核心是 `partial_cmp`：它返回 `Option<Ordering>`，`None` 表示「这两个值不可比」。浮点的 `NaN` 就落在这个洞里，所以 `f64` 有 `PartialOrd` 而没有 [[cmp.Ord|Ord]]。

## 简介

定义是 `pub trait PartialOrd<Rhs: ?Sized = Self>: PartialEq<Rhs>`。它有两个特点：一是以 `PartialEq` 为 supertrait，二是比较结果用 `Option<Ordering>` 包了一层。

这层 `Option` 就是「Partial」的全部含义——**部分序**：并非任意两个值都能分出大小。`f64::NAN` 是标准反例：

```text
NaN < 1.0  →  false
NaN > 1.0  →  false
NaN == 1.0 →  false
```

三者全不成立，`partial_cmp` 只能返回 `None`。如果比较结果不是 `Option` 而是 `Ordering`，实现者就被迫为不可比的情况编一个答案，数学上就假了。

只有 `partial_cmp` 必须实现，`lt`、`le`、`gt`、`ge` 都有默认实现，它们把 `partial_cmp` 的结果与对应的 `Ordering` 比较；`None` 时一律返回 `false`。这解释了为什么 `NaN <= NaN` 也是 `false`。

实现时有两条一致性要求，编译器不检查：`a == b` 当且仅当 `partial_cmp` 返回 `Some(Equal)`；`a < b` 当且仅当返回 `Some(Less)`，`le`/`gt`/`ge` 同理。如果打算同时实现 `Ord`，标准库建议把比较逻辑只写一份在 `Ord::cmp` 里，然后让 `partial_cmp` 返回 `Some(self.cmp(other))`，避免两套逻辑漂移。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `partial_cmp()` | 返回两者的大小关系，不可比时返回 `None`。 |

签名是 `fn partial_cmp(&self, other: &Rhs) -> Option<Ordering>`。`Ordering` 见 [[cmp.Ordering|Ordering]]，它只有 `Less`、`Equal`、`Greater` 三个值。

## 提供的方法

| 方法 | 说明 |
| --- | --- |
| `lt()` | 判断 `self` 是否小于 `other`，对应 `<`。 |
| `le()` | 判断是否小于或等于，对应 `<=`。 |
| `gt()` | 判断是否大于，对应 `>`。 |
| `ge()` | 判断是否大于或等于，对应 `>=`。 |

四者的默认实现都是「`partial_cmp` 返回 `Some(期望的 Ordering)`」，因此不可比时统一为 `false`。除非有特别的优化，不需要覆写它们。

## 与相邻 trait 的关系

| 维度 | `PartialOrd` | `Ord` |
| --- | --- | --- |
| 可比性 | 允许不可比，`partial_cmp` 返回 `None` | 任意两值都能比，`cmp` 直接返回 `Ordering` |
| 必须实现 | `partial_cmp` | `cmp` |
| supertrait | `PartialEq` | `Eq` + `PartialOrd` |
| `f64` | 实现 | 不实现 |
| 能用的排序 API | `sort_by`、`sort_by_key` | `sort`、`sort_unstable`、`BTreeMap`、`BinaryHeap` |
| 派生要求 | 字段都实现 `PartialOrd` | 字段都实现 `Ord` |

两个 trait 的关系是「弱版 / 强版」：`Ord` 一定蕴含 `PartialOrd`，反向不成立。这也意味着泛型函数里写 `T: PartialOrd` 就拿不到 `v.sort()`——那是 `Ord` 的方法，编译器会报 E0277。

还有一处容易忽略：`PartialOrd` 与 `PartialEq` 必须讲同一个故事。如果 `partial_cmp` 只比较价格、`eq` 却比较全部字段，那么 `a == b` 为假而 `a.partial_cmp(b) == Some(Equal)` 可能为真，`max`、`min`、`clamp` 的结果都会变得难以解释。

## 示例

### 派生实现按声明顺序比较

```rust
#[derive(PartialEq, PartialOrd, Debug)]
enum Priority {
    Low,
    Normal,
    High,
}

fn main() {
    // 枚举的派生顺序就是声明顺序：Low < Normal < High
    assert!(Priority::Low < Priority::High);
    assert!(Priority::High > Priority::Normal);
    assert!(Priority::Low <= Priority::Low);
    assert_eq!(Priority::Normal.partial_cmp(&Priority::High), Some(std::cmp::Ordering::Less));
}
```

### 不可比的情况

```rust
fn main() {
    let nan = f64::NAN;

    // 四个比较全部为 false，谁也没赢
    assert!(!(nan < 1.0));
    assert!(!(nan > 1.0));
    assert!(!(nan <= 1.0));
    assert!(!(nan >= 1.0));

    // partial_cmp 直接说明「不可比」
    assert_eq!(nan.partial_cmp(&1.0), None);

    // 正因为有 None，对浮点排序不能用 unwrap 了事
    assert_eq!(1.0f64.partial_cmp(&2.0), Some(std::cmp::Ordering::Less));
}
```

### 手写部分序

```rust
use std::cmp::Ordering;

#[derive(Debug)]
struct Version {
    major: u32,
    minor: u32,
}

impl PartialEq for Version {
    fn eq(&self, other: &Self) -> bool {
        self.major == other.major && self.minor == other.minor
    }
}

impl PartialOrd for Version {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        // 只要结果总能比出来，就包一层 Some
        Some((self.major, self.minor).cmp(&(other.major, other.minor)))
    }
}

fn main() {
    let a = Version { major: 1, minor: 2 };
    let b = Version { major: 1, minor: 10 };

    assert!(a < b);
    assert_eq!(a.partial_cmp(&b), Some(Ordering::Less));
    assert!(b >= a);
}
```

## 常见陷阱

1. **对浮点写 `partial_cmp(...).unwrap()`**：遇到 `NaN` 立即 panic。排序浮点改用 `sort_by(f64::total_cmp)`，它给出包含 `NaN` 的全序。
2. **`partial_cmp` 与 `eq` 不一致**：一个按价格、一个按全部字段，`<` 和 `==` 会给出自相矛盾的答案，`min`/`max`/`clamp` 随之失真。
3. **手写 `Ord` 却派生 `PartialOrd`**：两套比较逻辑各自演化，`<` 与 `cmp` 迟早不一致。手写 `Ord` 时 `partial_cmp` 必须写成 `Some(self.cmp(other))`。
4. **以为派生 `PartialOrd` 按判别值排序**：默认按字段/变体的声明顺序；想让枚举按数值排，需要显式写出判别值并保证顺序一致。
5. **`if` 里只有两个分支**：`NaN` 让 `<` 和 `>` 同时为假，`if a < b { ... } else { ... }` 的 `else` 其实混进了「不可比」的情况，必要时显式判断 `partial_cmp`。
6. **泛型边界写宽了**：`T: PartialOrd` 就能比较，但不能 `sort()`；想要排序得收紧到 `T: Ord`。

## 相关

- [[cmp|std::cmp 模块]]：`PartialOrd` 所属模块。
- [[cmp.Ord|Ord]]：全序版本，排序容器的要求。
- [[cmp.PartialEq|PartialEq]]：相等语义必须与顺序一致。
- [[cmp.Ordering|Ordering]]：`Less`、`Equal`、`Greater` 三态。
- [[primitive.浮点类型|f64]]：因 `NaN` 只实现 `PartialOrd`。
- [[12-集合类型|集合类型]]：`BTreeMap`、`BinaryHeap` 的排序约束从这里来。
