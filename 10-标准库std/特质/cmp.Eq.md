---
title: "std::cmp::Eq"
type: std-条目
kind: 特质
module: cmp
slug: cmp.Eq
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - Eq
一句话: 给 PartialEq 补上自反性，是没有任何方法的「承诺」；f64 因 NaN 被排除在外。
---

# Eq

> [!abstract] 一句话
> `Eq` 是一个空特质：它不添加任何方法，只声明「我的 `==` 是真正的等价关系，`a == a` 恒为真」。`f64` 做不到这一点，所以不实现它，也就不能当 `HashMap` 的键。

## 简介

定义只有一行：`pub trait Eq: PartialEq<Self> {}`。`Eq` 是 `PartialEq` 的 subtrait，没有关联项、没有方法、没有默认实现。写 `impl Eq for MyType {}` 时，编译器不会检查任何东西——它检查不了「自反、对称、传递」这类数学性质。

所以 `Eq` 在类型系统中的角色是**标记**：把一个「实现者保证满足」的契约变成可写进泛型边界的约束。这份契约包含：

| 性质 | 含义 |
| --- | --- |
| 自反 | 对任意 `a` 都有 `a == a`，这正是 `PartialEq` 不要求的 |
| 对称 | `a == b` 则 `b == a`，`PartialEq` 已要求 |
| 传递 | `a == b`、`b == c` 则 `a == c`，`PartialEq` 已要求 |
| 与 `Hash` 一致 | 若同时实现 [[hash.Hash|Hash]]，`a == b` 必须 `hash(a) == hash(b)` |

违反这些要求的后果是**逻辑错误**：不会产生未定义行为，但容器可能「存进去、查不到」。因此 `Eq` 不是 `unsafe` 特质，标准库实现里也没有任何 `unsafe` 代码依赖它。

标准库用它来表达「可靠的相等」：`HashMap<K, V>` 要求 `K: Eq + Hash`，`HashSet<T>` 同样；`BTreeMap<K, V>` 要求 `K: Ord`，而 `Ord: Eq`，所以排序容器顺带就要了 `Eq`。

### 为什么 f64 不实现 Eq

`f64` 实现了 `PartialEq`，但故意不实现 `Eq`。原因是 IEEE 754 规定 `NaN` 与任何值（包括它自己）比较都返回 `false`：

```text
NaN == NaN  →  false
```

「自反性」被破坏，`f64` 就不满足 `Eq` 的契约。而这不是疏忽，是语言刻意留下的缺口：如果硬给 `f64` 实现 `Eq`，`HashMap<f64, _>` 就会允许插入 `NaN` 键，然后永远无法用另一个 `NaN` 把它取出来——因为 `get` 先算哈希再比 `eq`，而 `NaN != NaN`。

即使你愿意「自己承担风险」，孤儿规则也堵死了这条路：`f64` 与 `Eq` 都来自标准库，外部 crate 里 `impl Eq for f64` 会报 E0117。标准库的选择是让你显式地选择一种语义：

- 按位比较：`a.to_bits() == b.to_bits()`，注意 `0.0` 与 `-0.0` 位模式不同；
- 用全序：`f64::total_cmp`，它把 `NaN` 也纳入排序，可以用 `sort_by` 但不能当 `Ord`（`total_cmp` 只是一个方法）。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| （无） | 空特质，只写 `impl Eq for MyType {}` 即可。 |

前提是该类型已经实现了 `PartialEq`。空的 impl 不是偷懒，而是一句签名：「我保证等价关系成立」。

```rust
#[derive(PartialEq, Debug)]
struct Book {
    isbn: i32,
}

// 只比较一个整数，自反、对称、传递都成立，可以放心承诺
impl Eq for Book {}

fn main() {
    let b1 = Book { isbn: 7 };
    let b2 = Book { isbn: 7 };

    assert!(b1 == b2);
    assert!(b1 == b1);
}
```

## 提供的方法

无。`eq` 与 `ne` 都继承自 [[cmp.PartialEq|PartialEq]]，比较操作符 `==`、`!=` 也来自那里。`Eq` 唯一的产出是「可以放进要求 `Eq` 的泛型边界」。

## 与相邻 trait 的关系

`PartialEq` → `Eq` 是加法：多一条自反性，零个方法。

| 维度 | `PartialEq` | `Eq` |
| --- | --- | --- |
| 自反性 | 不要求 | 要求，`a == a` 恒真 |
| 方法 | `eq` 必须实现，`ne` 自带 | 无 |
| `f64` | 实现 | 不实现（`NaN != NaN`） |
| 能否作 `HashMap` 键 | 单独不够，还差 `Eq` 与 `Hash` | 满足一半条件 |
| 派生 | `#[derive(PartialEq)]` | `#[derive(Eq)]`，要求字段全为 `Eq` |

与 `Ord` 的关系：`Ord: Eq + PartialOrd`。排序需要先能判断「相等」，所以 `Eq` 在继承链的中间；反过来，只实现 `Eq` 并不能让类型进入 `BTreeMap`，还需要 [[cmp.Ord|Ord]]。

与 `Hash` 的关系是一条横跨两个 trait 的契约：`a == b` ⇒ `hash(a) == hash(b)`。这条契约无法由编译器检查，只能写在文档里靠实现者遵守；`HashMap` 的正确性完全建立在它之上。

## 示例

### 派生 Eq 后作为 HashMap 键

```rust
use std::collections::HashMap;

#[derive(PartialEq, Eq, Hash, Debug)]
struct User {
    id: u32,
}

fn main() {
    let mut visits: HashMap<User, u32> = HashMap::new();

    visits.insert(User { id: 1 }, 10);
    // 同一个键再插一次，覆盖而不是新增
    visits.insert(User { id: 1 }, 20);

    assert_eq!(visits.len(), 1);
    assert_eq!(visits[&User { id: 1 }], 20);
}
```

### 自定义相等后再补 Eq

手写 `PartialEq` 时可以定义任意规则，但只有规则满足等价关系时才能写 `Eq`。大小写不敏感的比较是对称、传递、自反的，所以合格——不过此时**哈希也必须用同一套规则**。

```rust
use std::collections::HashMap;
use std::hash::{Hash, Hasher};

struct CaseInsensitive(String);

impl PartialEq for CaseInsensitive {
    fn eq(&self, other: &Self) -> bool {
        self.0.to_lowercase() == other.0.to_lowercase()
    }
}

// 大小写不敏感的相等满足等价关系，可以承诺 Eq
impl Eq for CaseInsensitive {}

impl Hash for CaseInsensitive {
    fn hash<H: Hasher>(&self, state: &mut H) {
        // 必须与 eq 使用同一套规范化，否则键查不到
        self.0.to_lowercase().hash(state);
    }
}

fn main() {
    let mut map = HashMap::new();
    map.insert(CaseInsensitive("Rust".to_string()), 1);

    assert_eq!(map.get(&CaseInsensitive("RUST".to_string())), Some(&1));
}
```

### f64 被挡在门外时的替代做法

```rust
fn main() {
    // f64 没有 Ord，因此 sort 与 BTreeMap 都用不了；
    // total_cmp 提供包含 NaN 的全序，只适合直接排序
    let mut values = vec![f64::NAN, 1.0, -0.0, 0.0];
    values.sort_by(f64::total_cmp);

    // 顺序完全确定：-0.0 排最前，NaN 被排到最后
    assert_eq!(values.len(), 4);
    assert!(values[0].is_sign_negative());
    assert!(values[3].is_nan());
}
```

## 常见陷阱

1. **结构体里含 `f64` 却派生 `Eq`**：`#[derive(Eq)]` 要求每个字段都是 `Eq`，含浮点字段直接编译失败。要么换成整数/定点数，要么放弃「相等」语义。
2. **手写 `PartialEq` 后仍用派生的 `Hash`**：`eq` 忽略大小写，`hash` 却按原样计算，于是相等值的哈希不同，`HashMap` 里出现「插入成功、查询失败」。
3. **想给 `f64` 补 `impl Eq`**：孤儿规则禁止，E0117 会拦下来；这不是能靠 `unsafe` 绕过的限制。
4. **以为 `Eq` 会带来额外方法**：它一个方法都没有，所有比较能力都来自 `PartialEq`。
5. **以为 `Eq` 能替代 `Ord`**：`Eq` 只说「相不相等」，不说「谁大谁小」；`BTreeMap`、`BinaryHeap` 需要的是 `Ord`。
6. **`-0.0 == 0.0` 的直觉**：浮点比较里它们相等，但 `to_bits` 不同；一旦用位模式当键，就要自己决定把哪个零规范化。

## 相关

- [[cmp|std::cmp 模块]]：`Eq` 所属模块。
- [[cmp.PartialEq|PartialEq]]：`Eq` 的 supertrait，提供全部方法。
- [[cmp.Ord|Ord]]：全序，`Ord: Eq`，排序容器的真正要求。
- [[hash.Hash|Hash]]：与 `Eq` 共享一致性契约，`HashMap` 键的另一半。
- [[collections.HashMap|HashMap]]：要求 `K: Eq + Hash`。
- [[primitive.浮点类型|f64]]：不满足自反性，因此不实现 `Eq`。
