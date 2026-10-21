---
title: "std::ops::Fn"
type: std-条目
kind: 特质
module: ops
slug: ops.Fn
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - Fn
一句话: 不可变接收者的调用运算契约，只读环境或完全不捕获的闭包会自动实现它。
---

# `Fn`

> [!abstract] 一句话
> `Fn` 是「可以被反复调用、且调用时不改动自身状态」的那一类可调用值：只读取捕获变量（或不捕获任何东西）的闭包，以及函数指针，都自动实现它。

## 简介

Rust 有三个调用特质，按「调用要多少权限」从宽到严排列：`Fn` 只要 `&self`，`FnMut` 要 `&mut self`，`FnOnce` 要 `self`。`Fn` 最严格地保证了调用不改变状态，所以也最容易被反复调用、被共享引用调用。

它不是函数指针 `fn`。`Fn` 是特质，能被泛型约束（零成本、单态化），也能做成 `Box<dyn Fn()>`（动态分发）；`fn` 是具体的指针类型，装不下捕获的环境。

一个关键事实：`Fn` 是**自动实现**的。编译器看闭包体怎么使用捕获变量，就挑能满足约束的最「弱」的那一档——只要只读访问，就得到 `Fn`。这个判定发生在类型检查阶段，你无法写 `impl Fn<..> for MyType`（`call` 至今仍是不稳定特性）。

## 必须实现

无需也不能手动实现。`Fn` 的调用方法 `call` 尚未稳定，自定义类型写不出 `impl Fn<..>`；唯一的来源是编译器为闭包、函数指针以及 `&F` 自动生成的实现。

能用的是「要求它」：把 `F: Fn(参数) -> 返回值` 写成泛型约束。

## 提供的方法

`Fn` 没有稳定的公开方法，调用一律通过语法 `f(args)` 触发。可用的能力是继承来的：`Fn` 是 `FnMut` 的子特质，因此任何 `F: Fn` 也可以当 `FnMut` 和 `FnOnce` 使用。

## 与相邻 trait 的关系

| trait | 关系 |
| --- | --- |
| `FnMut` | 直接超特质（`Fn: FnMut`）：能在 `Fn` 上做的事，`FnMut` 场合都能用。 |
| `FnOnce` | 最顶层超特质（`Fn: FnMut: FnOnce`），`Fn` 值也能按值消耗调用。 |
| `fn(..) -> ..` | 函数指针：既实现全部三个调用特质，又能装进泛型之外的字段。 |
| 引用 `&F` | 当 `F: Fn` 时 `&F` 也实现 `Fn`，所以可以共享借用着反复调用。 |

闭包实际实现哪一档，取决于**捕获方式**：

| 闭包对捕获变量的用法 | 得到的实现 |
| --- | --- |
| 不捕获，或只读取（`&T`） | `Fn`，可重复调用 |
| 需要修改（`&mut T`） | `FnMut`，可重复调用但需要独占借用 |
| 移出/消耗捕获值（`T`） | `FnOnce`，只能调用一次 |

## 示例

### 泛型约束 `Fn`

```rust
fn call_with_one<F>(func: F) -> usize
where
    F: Fn(usize) -> usize,
{
    // Fn 代表可以反复调用，这里调用两次也不会出问题
    func(1) + func(1)
}

fn main() {
    let square = |x: usize| x * x;

    // 直接调用闭包
    assert_eq!(square(5), 25);

    // 传进泛型函数：单态化，没有虚表开销
    assert_eq!(call_with_one(square), 2);
    assert_eq!(call_with_one(|x| x * 2), 4);

    // 不捕获环境的闭包可以强转成函数指针
    let as_fn: fn(usize) -> usize = square;
    assert_eq!(as_fn(4), 16);
}
```

### 只读捕获的闭包仍是 `Fn`

```rust
fn repeat_twice<F: Fn() -> usize>(f: F) -> usize {
    f() + f()
}

fn main() {
    let base: usize = 10;
    // 只读访问 base，编译器给的是 Fn
    let read_base = || base;

    assert_eq!(repeat_twice(read_base), 20);
    // 只借用不移动，base 之后照常使用
    assert_eq!(base, 10);
}
```

## 常见陷阱

1. **以为 `move` 就等于 `FnOnce`**：`move` 只改变捕获方式（按值搬进闭包），若闭包只读取这些值，它实现的仍然是 `Fn`。
2. **在 `Fn` 约束里改捕获变量**：`|..| count += 1` 需要可变借用，编译器会提示要求 `FnMut`，换成 `F: FnMut` 并把参数声明为 `mut`。
3. **捕获与借用打架**：闭包持有 `v` 的不可变借用期间，外部不能再 `v.push(..)`，否则报借用冲突；提前 `drop(closure)` 或用 `move` 转移所有权。
4. **泛型 `Fn` 与 `fn` 指针混用**：`F: Fn()` 单态化、零成本，但不能存进同一个 `Vec`；需要异构集合时用 `Vec<Box<dyn Fn()>>`。
5. **返回引用的闭包写不出来**：`|x| &x` 会因生命周期无法表达而报错，改用 `fn(&T) -> &T` 这样的函数指针。
6. **把闭包塞进结构体字段**：字段类型不能是 `impl Fn`，要写 `Box<dyn Fn()>` 或加类型参数。

## 相关

- [[ops.FnMut|FnMut]]：需要修改捕获变量的那一档。
- [[ops.FnOnce|FnOnce]]：会消耗捕获变量、只能调用一次的那一档。
- [[19-闭包|闭包]]：捕获方式与调用特质的完整推导规则。
- [[16-trait 对象与动态分发|trait 对象]]：`Box<dyn Fn()>` 与静态分发的取舍。
- [[iter.Iterator|Iterator]]：`map` / `filter` 等适配器大量使用 `Fn` 系列约束。
- [[ops|std::ops 模块]]：运算符与调用特质总览。
