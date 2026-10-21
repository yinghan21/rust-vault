---
title: "std::ops::Add"
type: std-条目
kind: 特质
module: ops
slug: ops.Add
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - Add
一句话: 定义二元加号 + 的行为，通过 Output 关联类型决定 a + b 的结果类型。
---

# `Add`

> [!abstract] 一句话
> `Add` 让 `+` 对自定义类型可用：`a + b` 会展开成 `a.add(b)`，结果类型由关联类型 `Output` 指定——所以两边相加不一定得到同一种类型。

## 简介

运算符在 Rust 里不是特例，而是普通 trait 方法。`a + b` 的糖衣下是 `Add::add(a, b)`，编译器据此在 trait 系统里查找实现。

`Add` 的签名里有两个类型位置：`Rhs` 是右操作数（默认 `Self`，可改成别的类型），`Output` 是结果类型。`std::time::SystemTime` 就实现了 `Add<Duration>`，于是 `SystemTime + Duration` 合法，而 `SystemTime + SystemTime` 不合法。

`Add` 是 `Copy` 无关的：它按值接收 `self`，所以 `a + b` 会移动两个操作数。想要「用完还能再用」，要么类型是 `Copy`，要么额外实现 `Add<&T> for &T`。

只要类型实现了 `Add`，`+=` 并不会自动跟着可用——那需要单独的 `AddAssign`；两个特质互相独立。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `add(self, rhs)` | 执行 `+` 运算，返回 `Self::Output`。 |
| `type Output` | 关联类型，声明相加结果的类型。 |

完整签名：`fn add(self, rhs: Rhs) -> Self::Output`。

`Output` 必须写出来，没有默认值——这正是「加法结果可能是别的类型」的表达方式。

## 与相邻 trait 的关系

| trait | 关系 |
| --- | --- |
| `AddAssign` | `+=` 的实现端，与 `Add` 完全独立，需要单独实现。 |
| `Sum` | 迭代器求和用 `Sum<Self::Item>`，其实现常通过反复 `Add`。 |
| `Sub` / `Mul` / `Div` | 同族运算符特质，形式完全一致（`Rhs` + `Output`）。 |
| `Copy` | 不参与运算语义，但没实现时 `a + b` 会移走操作数。 |

## 示例

### 基本实现

```rust
use std::ops::Add;

#[derive(Debug, Copy, Clone, PartialEq)]
struct Point {
    x: i32,
    y: i32,
}

impl Add for Point {
    // Rhs 省略即为 Self
    type Output = Self;

    fn add(self, other: Self) -> Self::Output {
        Self {
            x: self.x + other.x,
            y: self.y + other.y,
        }
    }
}

fn main() {
    let sum = Point { x: 1, y: 0 } + Point { x: 2, y: 3 };
    assert_eq!(sum, Point { x: 3, y: 3 });
}
```

### 换 `Rhs` 类型，`Output` 不一定是 `Self`

```rust
use std::ops::Add;

#[derive(Debug, Copy, Clone, PartialEq)]
struct Vec2 {
    x: f64,
    y: f64,
}

// 同类型相加
impl Add for Vec2 {
    type Output = Vec2;

    fn add(self, rhs: Vec2) -> Vec2 {
        Vec2 { x: self.x + rhs.x, y: self.y + rhs.y }
    }
}

// 另一种 Rhs：向量 + 标量，输出仍是 Vec2
impl Add<f64> for Vec2 {
    type Output = Vec2;

    fn add(self, rhs: f64) -> Vec2 {
        Vec2 { x: self.x + rhs, y: self.y + rhs }
    }
}

fn main() {
    let v = Vec2 { x: 1.0, y: 2.0 };
    assert_eq!(v + v, Vec2 { x: 2.0, y: 4.0 });
    assert_eq!(v + 0.5, Vec2 { x: 1.5, y: 2.5 });
}
```

### 泛型实现，靠约束传递 `Output`

```rust
use std::ops::Add;

#[derive(Debug, Copy, Clone, PartialEq)]
struct Point<T> {
    x: T,
    y: T,
}

// 要求 T 自己也能相加且结果仍是 T，否则 Output = Self 无法成立
impl<T: Add<Output = T>> Add for Point<T> {
    type Output = Self;

    fn add(self, other: Self) -> Self::Output {
        Self {
            x: self.x + other.x,
            y: self.y + other.y,
        }
    }
}

fn main() {
    assert_eq!(
        Point { x: 1, y: 0 } + Point { x: 2, y: 3 },
        Point { x: 3, y: 3 }
    );
}
```

## 常见陷阱

1. **忘了写 `type Output`**：`Add` 没有默认关联类型，漏写直接编译失败。
2. **以为实现 `Add` 就自动有 `+=`**：`+=` 属于 `AddAssign`，要另外写 `add_assign(&mut self, rhs)`。
3. **操作数被移走**：`+` 按值接收，非 `Copy` 类型用完即失效；需要复用就实现 `Add<&T> for &T`，或先 `clone()`。
4. **`Output` 乱设导致类型不匹配**：`a + b` 的结果类型完全由 `Output` 决定，`let p: Point = a + b;` 在 `Output = &Point` 时无法成立。
5. **引用组合不会自动生成**：`&a + &b` 需要你手写 `impl Add<&T> for &T`，标准库不会为自定义类型补上。
6. **整数溢出语义**：内置整数在 debug 下溢出 panic、release 下回绕；用 `checked_add` / `wrapping_add` 明确意图。
7. **孤儿规则**：给外部类型实现 `Add` 必须有本地类型参与，通常包一层新类型再用。

## 相关

- [[ops|std::ops 模块]]：加减乘除与索引、调用特质总览。
- [[ops.Index|Index]]：同样用关联类型 `Output` 的运算特质。
- [[ops.Deref|Deref]]：另一个改运行语义的运算符特质。
- [[primitive.整数类型|整数类型]]：内置整数溢出的具体规则。
- [[14-泛型|泛型]]：给运算符实现加泛型约束的写法。
