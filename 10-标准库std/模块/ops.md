---
title: "std::ops"
type: std-模块
module: ops
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - ops
一句话: "运算符重载：把 +、*、[]、*v、() 等运算符接到自定义类型上的特质。"
---

# std::ops

> [!abstract] 一句话
> `std::ops` 给每个运算符配了一个特质：实现 `Add` 就能用 `+`，实现 `Index` 就能用 `[]`，实现 `Deref` 就能用 `*`——运算符重载在 Rust 里就是实现这些特质。

## 模块简介

Rust 不允许用户定义新运算符，但允许为已有运算符提供实现。`std::ops` 里的每个特质都绑定一个固定的运算符号：`Add` 对应 `+`、`Mul` 对应 `*`、`Rem` 对应 `%`、`Neg` 对应一元 `-`、`Not` 对应 `!`、`Index` 对应 `v[i]`、`Deref` 对应 `*v`、`Fn` 对应 `f()`。所以「重载运算符」在 Rust 里的准确说法是「为类型实现对应的 ops 特质」。

模块按功能分组。算术：`Add`/`Sub`/`Mul`/`Div`/`Rem`，每个都有对应的 `AddAssign` 等赋值版本，**两者必须分别实现**。位运算：`BitAnd`/`BitOr`/`BitXor`/`Shl`/`Shr` 及各自的 `*Assign`。一元：`Neg`、`Not`。索引：`Index`/`IndexMut`，返回关联类型 `Output` 的引用。解引用：`Deref`/`DerefMut`，也是方法调用自动解引用和 `&T` 到 `&U` 强制转换的基础。调用：`Fn`/`FnMut`/`FnOnce`，闭包自动实现。范围：`Range`/`RangeFrom`/`RangeTo`/`RangeInclusive`/`RangeToInclusive`/`RangeFull`，以及统一描述它们的 `RangeBounds` 与端点枚举 `Bound`。另外还有负责析构的 `Drop` 与显式控制流的 `ControlFlow`。

两条使用原则。第一，语义要符合直觉：`Mul` 就该像乘法，别让 `+` 改动内部状态或返回 `()`。第二，`Output` 不必等于 `Self`，`impl Mul<f64> for Point` 让标量乘法返回一个新点很自然，但同一类型的同一运算不要有多种互相矛盾的含义。注意 `=` 没有对应特质，所以无法自定义赋值语义；想要自定义运算符只能靠宏。

## 快速上手

```rust
use std::ops::{Add, Index, Mul, Neg};

#[derive(Debug, Clone, Copy, PartialEq)]
struct Point {
    x: f64,
    y: f64,
}

impl Add for Point {
    type Output = Point;
    fn add(self, rhs: Point) -> Point {
        Point { x: self.x + rhs.x, y: self.y + rhs.y }
    }
}

// Output 可以与 Self 不同，也可以对不同类型的右操作数实现
impl Mul<f64> for Point {
    type Output = Point;
    fn mul(self, k: f64) -> Point {
        Point { x: self.x * k, y: self.y * k }
    }
}

impl Neg for Point {
    type Output = Point;
    fn neg(self) -> Point {
        Point { x: -self.x, y: -self.y }
    }
}

struct Names(Vec<String>);

impl Index<usize> for Names {
    type Output = String;
    fn index(&self, i: usize) -> &String {
        &self.0[i]
    }
}

fn main() {
    let a = Point { x: 1.0, y: 2.0 };
    let b = Point { x: 3.0, y: 4.0 };
    assert_eq!(a + b, Point { x: 4.0, y: 6.0 });
    assert_eq!(a * 2.0, Point { x: 2.0, y: 4.0 });
    assert_eq!(-a, Point { x: -1.0, y: -2.0 });

    let names = Names(vec![String::from("甲"), String::from("乙")]);
    assert_eq!(names[1], "乙");

    // 范围类型也来自这里，并可当迭代器使用
    let sum: i32 = (1..=4).sum();
    assert_eq!(sum, 10);
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[ops.Add\|Add]] | `+`，关联类型 `Output` 决定结果类型。 |
| `ops::Sub` / `ops::Mul` / `ops::Div` / `ops::Rem` | 其余四个算术运算符。 |
| `ops::AddAssign` 等 `*Assign` | `+=`、`-=`、`*=`、`/=`、`%=`，需单独实现。 |
| `ops::Neg` / `ops::Not` | 一元 `-` 与逻辑取反 `!`。 |
| `ops::BitAnd` / `ops::BitOr` / `ops::BitXor` | 位与、位或、位异或。 |
| `ops::Shl` / `ops::Shr` | 左移 `<<` 与右移 `>>`。 |
| [[ops.Index\|Index]] | `v[i]` 只读索引，返回 `&Output`。 |
| `ops::IndexMut` | `v[i] = x` 的可变索引。 |
| [[ops.Deref\|Deref]] | `*v` 与解引用强制转换的基础。 |
| [[ops.Drop\|Drop]] | 析构钩子 `fn drop(&mut self)`。 |
| [[ops.Fn\|Fn]] / [[ops.FnMut\|FnMut]] / [[ops.FnOnce\|FnOnce]] | 调用运算符，闭包与函数指针据此实现。 |
| [[ops.Range\|Range]] | `start..end` 的类型，同时实现 `Iterator`。 |
| `ops::RangeInclusive` / `ops::RangeFrom` / `ops::RangeFull` | `..=end`、`start..`、`..`。 |
| `ops::RangeBounds` / `ops::Bound` | 统一处理各种范围及其端点。 |
| `ops::ControlFlow` | `Continue`/`Break` 的显式循环控制枚举。 |

## 注意事项

> [!warning] 算术与赋值要成对实现
> 实现 `Add` 不会自动带来 `AddAssign`。惯用做法是让 `AddAssign` 复用 `Add` 的逻辑，或让 `Add` 基于 `AddAssign` 与 `Clone` 实现，避免两份逻辑漂移。

> [!tip] `Index` 的 `Output` 只给引用
> `Index::index` 必须返回 `&Self::Output`，不能返回临时值，所以不要把 `Output` 设成 `String` 之类需要构造的类型；需要「算出来再返回」请用方法而不是 `[]`。

> [!danger] `Deref` 滥用会毁掉可读性
> 盲目为业务类型实现 `Deref` 会触发方法解析与方法链上的自动解引用，让调用者分不清方法来自哪一层。除了智能指针与包装类型，用 `AsRef` 或普通方法更清晰。

## 相关

- [[ops.Range|Range]]：范围类型与 `Index`/`Iterator` 的关系。
- [[range|std::range]]：范围相关的辅助函数与边界语义。
- [[20-智能指针|智能指针]]：`Deref`/`DerefMut` 支撑的自动解引用。
- [[15-trait 基础|trait 基础]]：关联类型与 `Output` 的写法。
- [[09-方法与 impl|方法与 impl]]：为自定义类型添加 `impl` 的位置与规则。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 55 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [[ops.Range|`Range`]]
- [`RangeFrom`](https://doc.rust-lang.org/std/ops/struct.RangeFrom.html)
- [`RangeFull`](https://doc.rust-lang.org/std/ops/struct.RangeFull.html)
- [`RangeInclusive`](https://doc.rust-lang.org/std/ops/struct.RangeInclusive.html)
- [`RangeTo`](https://doc.rust-lang.org/std/ops/struct.RangeTo.html)
- [`RangeToInclusive`](https://doc.rust-lang.org/std/ops/struct.RangeToInclusive.html)
- [`Yeet`](https://doc.rust-lang.org/std/ops/struct.Yeet.html)

### 枚举

- [`Bound`](https://doc.rust-lang.org/std/ops/enum.Bound.html)
- [`ControlFlow`](https://doc.rust-lang.org/std/ops/enum.ControlFlow.html)
- [`CoroutineState`](https://doc.rust-lang.org/std/ops/enum.CoroutineState.html)
- [`OneSidedRangeBound`](https://doc.rust-lang.org/std/ops/enum.OneSidedRangeBound.html)

### 特质

- [[ops.Add|`Add`]]
- [`AddAssign`](https://doc.rust-lang.org/std/ops/trait.AddAssign.html)
- [`AsyncFn`](https://doc.rust-lang.org/std/ops/trait.AsyncFn.html)
- [`AsyncFnMut`](https://doc.rust-lang.org/std/ops/trait.AsyncFnMut.html)
- [`AsyncFnOnce`](https://doc.rust-lang.org/std/ops/trait.AsyncFnOnce.html)
- [`BitAnd`](https://doc.rust-lang.org/std/ops/trait.BitAnd.html)
- [`BitAndAssign`](https://doc.rust-lang.org/std/ops/trait.BitAndAssign.html)
- [`BitOr`](https://doc.rust-lang.org/std/ops/trait.BitOr.html)
- [`BitOrAssign`](https://doc.rust-lang.org/std/ops/trait.BitOrAssign.html)
- [`BitXor`](https://doc.rust-lang.org/std/ops/trait.BitXor.html)
- [`BitXorAssign`](https://doc.rust-lang.org/std/ops/trait.BitXorAssign.html)
- [[ops.Deref|`Deref`]]
- [`DerefMut`](https://doc.rust-lang.org/std/ops/trait.DerefMut.html)
- [`Div`](https://doc.rust-lang.org/std/ops/trait.Div.html)
- [`DivAssign`](https://doc.rust-lang.org/std/ops/trait.DivAssign.html)
- [[ops.Drop|`Drop`]]
- [[ops.Fn|`Fn`]]
- [[ops.FnMut|`FnMut`]]
- [[ops.FnOnce|`FnOnce`]]
- [[ops.Index|`Index`]]
- [`IndexMut`](https://doc.rust-lang.org/std/ops/trait.IndexMut.html)
- [`Mul`](https://doc.rust-lang.org/std/ops/trait.Mul.html)
- [`MulAssign`](https://doc.rust-lang.org/std/ops/trait.MulAssign.html)
- [`Neg`](https://doc.rust-lang.org/std/ops/trait.Neg.html)
- [`Not`](https://doc.rust-lang.org/std/ops/trait.Not.html)
- [`RangeBounds`](https://doc.rust-lang.org/std/ops/trait.RangeBounds.html)
- [`Rem`](https://doc.rust-lang.org/std/ops/trait.Rem.html)
- [`RemAssign`](https://doc.rust-lang.org/std/ops/trait.RemAssign.html)
- [`Shl`](https://doc.rust-lang.org/std/ops/trait.Shl.html)
- [`ShlAssign`](https://doc.rust-lang.org/std/ops/trait.ShlAssign.html)
- [`Shr`](https://doc.rust-lang.org/std/ops/trait.Shr.html)
- [`ShrAssign`](https://doc.rust-lang.org/std/ops/trait.ShrAssign.html)
- [`Sub`](https://doc.rust-lang.org/std/ops/trait.Sub.html)
- [`SubAssign`](https://doc.rust-lang.org/std/ops/trait.SubAssign.html)
- [`CoerceUnsized`](https://doc.rust-lang.org/std/ops/trait.CoerceUnsized.html)
- [`Coroutine`](https://doc.rust-lang.org/std/ops/trait.Coroutine.html)
- [`DerefPure`](https://doc.rust-lang.org/std/ops/trait.DerefPure.html)
- [`DispatchFromDyn`](https://doc.rust-lang.org/std/ops/trait.DispatchFromDyn.html)
- [`FromResidual`](https://doc.rust-lang.org/std/ops/trait.FromResidual.html)
- [`IntoBounds`](https://doc.rust-lang.org/std/ops/trait.IntoBounds.html)
- [`OneSidedRange`](https://doc.rust-lang.org/std/ops/trait.OneSidedRange.html)
- [`Receiver`](https://doc.rust-lang.org/std/ops/trait.Receiver.html)
- [`Residual`](https://doc.rust-lang.org/std/ops/trait.Residual.html)
- [`Try`](https://doc.rust-lang.org/std/ops/trait.Try.html)

<!-- END AUTO ITEMS -->
