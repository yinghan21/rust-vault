---
title: "std::ops::FnMut"
type: std-条目
kind: 特质
module: ops
slug: ops.FnMut
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - FnMut
一句话: 可变接收者的调用运算契约，会修改捕获变量的闭包自动实现它。
---

# `FnMut`

> [!abstract] 一句话
> `FnMut` 是「可以反复调用、并且允许在调用之间累积状态」的可调用值：它拿 `&mut self` 调用，所以既能读也能改捕获的变量，但调用方必须能可变借用它。

## 简介

`FnMut` 处在调用特质链的中间：`Fn` 是它的子特质，它是 `FnOnce` 的子特质。也就是说，任何 `Fn` 都能当 `FnMut` 用，任何 `FnMut` 都能当 `FnOnce` 用，反过来不成立。

它的语义是「一次调用可能改变自身，但类型仍然值得再调用一次」。典型例子是累加器、排序比较器、`for_each` 里的计数闭包。因为要拿 `&mut self`，被调用的闭包变量本身必须声明为 `mut`，或者以 `&mut` 的形式借出去——而 `&mut F` 在 `F: FnMut` 时也实现 `FnMut`，这让「临时借用一下闭包」成为可能。

编译器对闭包的推导是从弱到强的：只有当闭包体真的修改了某个捕获变量，才升格为 `FnMut`；一旦把捕获值移出去（消费掉），就变成 `FnOnce`。

## 必须实现

无需也不能手动实现。`call_mut` 尚未稳定，自定义类型写不出 `impl FnMut<..>`；实现由编译器为闭包和函数指针自动生成。

能做的只有写约束：`F: FnMut(参数) -> 返回值`。

## 提供的方法

`FnMut` 没有稳定的公开方法，调用通过 `f(args)` 完成。它继承了 `FnOnce` 的调用能力，因此既能反复调用，也能在需要时按值消耗。

## 与相邻 trait 的关系

| trait | 关系 |
| --- | --- |
| `Fn` | 子特质：`Fn` 值可当 `FnMut` 用，反之不行（`Fn` 承诺不改状态）。 |
| `FnOnce` | 超特质：`FnMut` 值可直接传给要求 `FnOnce` 的参数。 |
| `&mut F` | 当 `F: FnMut` 时 `&mut F` 也实现 `FnMut`，可临时借用闭包。 |
| `Iterator` | `map`、`filter`、`for_each`、`sort_by_key` 都要求 `FnMut`。 |

## 示例

### 修改捕获变量的闭包

```rust
fn do_twice<F>(mut func: F)
where
    F: FnMut(),
{
    // 同一个闭包调用两次，第二次能看到第一次留下的状态
    func();
    func();
}

fn main() {
    let mut x: usize = 1;

    // 闭包可变借用 x，所以得到 FnMut
    do_twice(|| x += 2);
    assert_eq!(x, 5);

    // 排序比较器是 FnMut 最常见的用途
    let mut words = vec!["bb", "a", "ccc"];
    words.sort_by_key(|w| w.len());
    assert_eq!(words, ["a", "bb", "ccc"]);
}
```

### 用 `&mut` 借用闭包，用完还能继续调

```rust
fn call_many<F: FnMut()>(mut f: F, times: usize) {
    for _ in 0..times {
        f();
    }
}

fn main() {
    let mut count = 0;
    {
        let mut tick = || count += 1;
        // 传 &mut tick：借用闭包本身，闭包不会被消耗
        call_many(&mut tick, 3);
        tick();
    }
    // 闭包离开作用域，count 的借用结束
    assert_eq!(count, 4);
}
```

## 常见陷阱

1. **闭包变量没加 `mut`**：`let tick = || count += 1; tick();` 会报「cannot borrow as mutable」，声明处要写 `let mut tick`。
2. **在 `Fn` 约束下要求可变**：函数写成 `F: Fn()` 却调用会改状态的闭包，编译不过；把约束放宽成 `F: FnMut()` 并在参数上写 `mut`。
3. **借用冲突**：闭包可变借用 `count` 期间，外部再读 `count` 会冲突；用 `{}` 缩小闭包作用域或先 `drop`。
4. **想存进 `Vec` 里复用**：`FnMut` 闭包各是不同类型，要同构集合请用 `Vec<Box<dyn FnMut()>>`。
5. **在迭代器链里修改外部变量**：`map` 要求 `FnMut` 没问题，但把 `&mut` 借给闭包后原变量在链结束前不可用，容易误判为「借用没还」。
6. **误以为 `FnMut` 只能调一次**：它可以无限次调用，只是每次都要求独占借用；只能调一次的语义属于 `FnOnce`。

## 相关

- [[ops.Fn|Fn]]：更严格的只读调用特质。
- [[ops.FnOnce|FnOnce]]：最宽松、只能调用一次的那一档。
- [[19-闭包|闭包]]：捕获与借用如何决定闭包实现哪个特质。
- [[iter.Iterator|Iterator]]：`map`、`for_each` 的 `FnMut` 约束。
- [[18-迭代器|迭代器]]：迭代器适配器与闭包配合的实践。
- [[ops|std::ops 模块]]：运算符与调用特质总览。
