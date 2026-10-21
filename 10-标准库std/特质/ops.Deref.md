---
title: "std::ops::Deref"
type: std-条目
kind: 特质
module: ops
slug: ops.Deref
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - Deref
一句话: 定义 *v 解引用与解引用强制转换，智能指针靠它把方法调用转发给内部值。
---

# Deref

> [!abstract] 一句话
> `Deref` 规定「用 `*v` 能拿到什么」：它给出一个 `&Target`，编译器据此在方法调用和引用传递处插入隐含的解引用，这就是解引用强制转换。

## 简介

`Deref` 只定义一个动作：`fn deref(&self) -> &Self::Target`。它让 `*v` 这件事有法可依 —— 对 `Box<T>` 得到 `T`，对 `String` 得到 `str`，对 `Vec<T>` 得到 `[T]`，对你写的包装类型则得到你指定的 `Target`。

它的重要性远不止 `*` 运算符。编译器在「解引用强制转换」（deref coercion）中会静默插入 `Deref::deref` 调用，最常见的三个场合是：

- 方法调用：`String` 上调 `.len()`，通过 `Deref` 找到 `str::len`；`Box<T>` 上的方法转发给 `T`。
- 引用传递：`fn f(s: &str)` 可以接收 `&String`，因为 `&String` 能强制转换成 `&str`。
- 自动多级套用：`&Box<String>` 会一路降到你需要的 `&str`，中间每一步都靠 `Deref`。

正因为编译器会**不打招呼地**插入调用，官方文档专门警告：只在「智能指针」语义下实现 `Deref`。它的设计目的是让自定义指针型容器表现得像指针，而不是用来模拟继承或省掉一层 `.0`。想给包装类型提供内部类型的只读视图，用 [[convert.AsRef|AsRef]] 或显式方法更合适。

可变场景由 `DerefMut` 承担：只有同时实现了 `DerefMut`，`w.push(x)` 这类需要 `&mut` 的方法调用才能通过自动解引用找到。

## 必须实现

| 项目 | 说明 |
| --- | --- |
| `type Target` | 解引用后得到的类型，允许 `?Sized`。 |
| `deref()` | 返回指向内部数据的 `&Target`。 |

签名是 `fn deref(&self) -> &Self::Target`。关联类型 `Target` 默认要求 `Sized`，但 `Deref` 特意声明了 `Target: ?Sized`，否则指向 `str`、`[T]`、`dyn Trait` 就无法实现。`deref` 返回的是**引用**，所以你永远不能通过它「搬走」内部值 —— 这是它与 `Into`、`AsRef` 最根本的分工。

## 与相邻 trait 的关系

这三个特质签名相似（都返回引用），契约完全不同：

| 维度 | `Deref` | `AsRef` | `Borrow` |
| --- | --- | --- | --- |
| 方向 | 沿 `Target` 单向解引用 | 任意方向、任意目标类型 | 借出一个「等价」的表示 |
| 是否隐式 | 是，编译器自动插入 | 否，需显式调用 | 否 |
| 关键要求 | 只能有一个 `Target` | 可同时实现多个 `AsRef<T>` | 必须与 `Eq`/`Hash`/`Ord` 一致 |
| 典型用途 | 智能指针、容器 | 泛型参数放宽（`impl AsRef<Path>`） | `HashMap` 用 `&str` 查 `String` 键 |

`Deref` 与 `AsRef` 的分水岭在于**唯一性**：`Deref::Target` 是关联类型，一个类型只能有一个；`AsRef<T>` 是泛型参数，一个类型可以同时实现 `AsRef<str>`、`AsRef<[u8]>`、`AsRef<Path>`。正因为 `Deref` 唯一且隐式，它才不能滥用。

## 示例

### 自定义包装类型与解引用强制转换

```rust
use std::ops::Deref;

struct Wrapper(Vec<i32>);

impl Deref for Wrapper {
    type Target = Vec<i32>;

    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

fn main() {
    let w = Wrapper(vec![3, 1, 2]);

    // 显式解引用
    assert_eq!((*w)[0], 3);
    // 自动解引用后调用 Vec 的方法
    assert_eq!(w.len(), 3);
    // 解引用强制转换：&Wrapper -> &Vec<i32> -> &[i32]
    let slice: &[i32] = &w;
    assert_eq!(slice, &[3, 1, 2]);
}
```

### 方法解析：调用内部类型的方法

```rust
use std::ops::Deref;

struct Meters(f64);

impl Deref for Meters {
    type Target = f64;

    fn deref(&self) -> &f64 {
        &self.0
    }
}

fn main() {
    let m = Meters(2.5);

    // *m 得到 f64（Copy），可直接参与运算
    assert_eq!(*m + 1.0, 3.5);
    // 编译器自动加 * 调用 f64::floor
    assert_eq!(m.floor(), 2.0);
}
```

### 配上 `DerefMut` 才能调用可变方法

```rust
use std::ops::{Deref, DerefMut};

struct Stack(Vec<i32>);

impl Deref for Stack {
    type Target = Vec<i32>;

    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

impl DerefMut for Stack {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.0
    }
}

fn main() {
    let mut s = Stack(vec![1]);
    // 需要 &mut Vec<i32>，靠 DerefMut 自动解引用
    s.push(2);
    assert_eq!(s.len(), 2);
    assert_eq!(*s, [1, 2]);
}
```

## 常见陷阱

1. **为了「复用内部类型的方法」而实现 `Deref`**：这是最典型的误用。官方明确建议只把它留给智能指针；newtype 的正确做法是 `AsRef` 加少量转发方法，否则封装会失效。
2. **忽略封装泄漏**：`Target` 的全部方法与特质实现都会变成你的类型的一部分，`Target` 上游一改，你的 API 就静默改变；你自有的同名方法会遮蔽 `Target` 的方法，阅读代码时容易看错调用目标。
3. **只实现 `Deref` 却调可变方法**：`w.push(x)` 需要 `&mut Target`，必须再实现 `DerefMut`，否则报 `cannot borrow ... as mutable`。
4. **把 `Target` 写成引用类型**：`type Target = &Vec<i32>` 会让 `deref` 返回 `&&Vec<i32>`；正确的写法是直接写 `Vec<i32>`。
5. **以为解引用强制转换处处生效**：它只在「目标类型已知」的位置发生。`let x = &s;` 得到 `&String`，写 `let x: &str = &s;` 才会转换。
6. **试图从自定义 `Deref` 类型中移动内容**：`let v = *w;` 报错，`deref` 只给引用；`Box<T>` 能这么做是因为编译器为它开了特例。

## 相关

- [[ops|std::ops 模块]]：`Deref`、`DerefMut` 与其他运算符特质。
- [[convert.AsRef|AsRef]]：同一件事的显式、可多目标版本。
- [[borrow.Borrow|Borrow]]：带一致性契约的借用特质。
- [[boxed.Box|Box]]：`Deref` 最经典的实现者。
- [[string.String|String]]、[[vec.Vec|Vec]]：依靠 `Deref` 提供 `str` 与 `[T]` 的视图。
- [[20-智能指针|智能指针]]：`Deref` 与自动解引用的整体设计。
