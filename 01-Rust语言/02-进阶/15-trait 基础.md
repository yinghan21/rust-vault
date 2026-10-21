---
title: "trait 基础"
type: 学习笔记
stage: 进阶
order: 15
tags:
  - rust/进阶
aliases:
  - trait
  - trait 基础
一句话: trait 定义「类型能做什么」，实现方与调用方靠它解耦，且与继承无关。
updated: 2025-06-10
---

# trait 基础

> [!abstract] 一句话
> trait 是一组方法签名的契约：谁 `impl` 了它，谁就能被当作「实现了这个 trait 的类型」使用——这是 Rust 唯一的抽象共享机制。

## 为什么需要它

Java / C++ 用**继承**共享行为，代价是强耦合（子类被迫接受父类的全部）和脆弱基类问题。Rust 没有继承，只有 trait：接口对应 Java 的 `interface`（还能带默认实现与关联类型），抽象基类对应 `trait` + 默认方法，多重继承对应「一个类型可以实现任意多个 trait」，模板约束对应 trait bound。

## 定义与实现

```rust
trait Summary {
    fn author(&self) -> String;
    // 默认方法：可以调用同一 trait 的其他方法，但访问不到字段
    fn summarize(&self) -> String { format!("{} 的文章", self.author()) }
}

struct Article { title: String, author: String }
struct Tweet { user: String }

impl Summary for Article {
    fn author(&self) -> String { self.author.clone() }
    fn summarize(&self) -> String { format!("《{}》", self.title) } // 覆盖默认实现
}

impl Summary for Tweet { fn author(&self) -> String { self.user.clone() } }

fn main() {
    let a = Article { title: String::from("泛型"), author: String::from("张三") };
    assert_eq!(a.summarize(), "《泛型》");
    assert_eq!(Tweet { user: String::from("ferris") }.summarize(), "ferris 的文章");
}
```

## 关联类型 vs 泛型参数

```rust
trait Container {
    type Item; // 关联类型：每个实现者只能选定一个 Item
    fn first(&self) -> Option<&Self::Item>;
}

struct Numbers(Vec<i32>);

impl Container for Numbers {
    type Item = i32;
    fn first(&self) -> Option<&Self::Item> { self.0.first() }
}

fn main() {
    assert_eq!(Numbers(vec![7, 8]).first(), Some(&7));
}
```

一个类型对同一 trait 只能给出**一个** `Item`，调用处也不用标注；若写成 `trait C<T>`，同一类型就能分别对 `i32`、`String` 实现多次，代价是调用处常要写 `C<i32>`。标准库里 `Iterator::Item`、`Deref::Target` 用关联类型，`From<T>`、`AsRef<T>` 用泛型参数。**一个类型只该有一种答案时，用关联类型。**

## 孤儿规则

不能给「外部的类型」实现「外部的 trait」：

```text
impl std::fmt::Display for i32 {   // ❌ E0117
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result { write!(f, "{}", self) }
}
```

理由是**一致性**（coherence）：若两个 crate 都能给 `i32` 加 `Display`，下游就不知道用哪一份。规则是 `impl Trait for Type` 中，trait 或 type 至少有一个属于当前 crate。合规路径有两条：

```rust
struct Meters(f64); // newtype：为自己的类型实现外部 trait

impl std::fmt::Display for Meters {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{} m", self.0)
    }
}

fn main() {
    assert_eq!(Meters(3.5).to_string(), "3.5 m");
}
```

## blanket impl

`impl<T: 某约束> Trait for T` 表示「所有满足条件的类型都自动实现它」，标准库大量使用（`impl<T: Display> ToString for T`）：

```rust
trait Describe {
    fn describe(&self) -> String;
}

impl<T: std::fmt::Display> Describe for T {
    fn describe(&self) -> String { format!("值 = {}", self) }
}

fn main() {
    assert_eq!(42.describe(), "值 = 42");
    assert_eq!("hi".describe(), "值 = hi");
}
```

代价是**覆盖面太大**：有了 blanket impl 之后，再给某个具体类型写特化实现就会冲突，通常只能改设计。

## `impl Trait` 作参数与返回值

```rust
fn show(item: impl std::fmt::Display) -> String { format!("<{}>", item) }

fn main() {
    assert_eq!(show(1), "<1>");
}
```

- 参数位置的 `impl Trait` 是泛型参数的语法糖，不能 turbofish 指定。
- 返回位置的 `impl Trait` 只能返回**一种**具体类型，要返回多种得用 [[16-trait 对象与动态分发|trait 对象]]；捕获入参生命周期时要写 `+ '_`。

## 常见错误与解决

| 错误 | 原因 | 解决 |
| --- | --- | --- |
| `E0117: only traits defined in the current crate ...` | 违反孤儿规则 | 用 newtype 包装，或改给自己的类型实现 |
| `E0046: not all trait items implemented` | 漏实现必须项 | 补全方法，或给 trait 加默认实现 |
| `E0277: the trait bound ... is not satisfied` | 调用处类型没实现所需 trait | 补 `impl`，或在签名里加 bound |

## 练习

1. 定义 `trait Area { fn area(&self) -> f64; }`，给圆和矩形实现，并写一个接收 `impl Area` 的函数。

## 相关

- [[14-泛型|泛型]]：`T: Trait` 约束与单态化。
- [[16-trait 对象与动态分发|trait 对象]]：把 trait 当类型用的另一种方式。
- 常用条目：[[fmt.Display|Display]]、[[string.ToString|ToString]]、[[convert.From|From]]。
