---
title: "std::mem::drop"
type: std-条目
kind: 函数
module: mem
slug: mem.drop
stable: "1.0.0"
tags:
  - std/类型
aliases:
  - "drop"
  - "mem::drop"
一句话: "把值按值接管并立刻丢弃，用来提前结束作用域；对 Copy 类型毫无作用，本质是空函数体加一次参数移除。"
---

# `drop`

> [!abstract] 一句话
> `std::mem::drop(x)` 把 `x` 移动进函数，函数体是空的，于是 `x` 在函数返回前被自动析构——这就是「提前释放」。它没有任何魔法，签名是 `pub fn drop<T>(_x: T)`。

## 简介

Rust 的值在离开作用域时自动析构。偶尔你想让它**现在**就析构，而不是等到块结束：提前释放一个大 `Vec` 的堆内存、提前释放锁、提前减掉 `Rc` 的引用计数。实现方式就是把它按值交给一个什么都不做的函数。

官方文档给的定义就一行：`pub fn drop<T>(_x: T) {}`。参数用下划线命名（`_x`），意思是「函数体不读它」，但因为它是按值参数，所有权已经转移进函数，函数返回时 `_x` 会被正常析构——析构发生在函数内部，不是你手写的那行。这就是「调用 `drop` 会释放值」的全部原因。

有两个边界必须讲清。第一，**`Copy` 类型没有作用**：`drop(42)`、`drop(true)` 传进去的是副本，原值依然存在，`assert_eq!(n, 42)` 照样通过。第二，**不能拿它调 `Drop::drop`**：手工调用析构方法是编译错误（`E0040`），要用就只能靠值被 drop，也就是这个函数。

`drop(&x)` 也是合法的，但它只「丢弃一个引用」——引用没有析构逻辑，等于什么都没做；不过在实践中 `drop(&guard)` 这类写法有时仍有用，因为它的参数表达式结束会提前结束借用，而 `drop(guard)` 才是真正释放。

## 签名与参数

```text
pub fn drop<T>(_x: T)
```

| 参数 | 说明 |
| --- | --- |
| `_x` | 按值接管要丢弃的值，所有权转移进函数，返回前自动析构。 |
| 返回 `()` | 无返回值，不 panic、不分配；对 `Copy` 类型是纯粹的空操作。 |

- `T` 无任何约束，任何类型都能传，包括引用、闭包、`MutexGuard`。
- 它与 `Drop` 特质不同：`Drop::drop(&mut self)` 由编译器在析构时调用，不能手工调用；`mem::drop` 是普通的按值函数。
- `drop` 在 prelude 里，直接写 `drop(x)` 即可，不必 `use std::mem::drop`。

## 示例

### 提前释放与引用计数

```rust
use std::rc::Rc;

fn main() {
    let v = vec![1, 2, 3];
    drop(v); // 显式丢弃，堆内存立刻归还

    // Rc 的计数能直接看到 drop 的效果
    let a = Rc::new(String::from("hi"));
    assert_eq!(Rc::strong_count(&a), 1);

    let b = Rc::clone(&a);
    assert_eq!(Rc::strong_count(&a), 2);

    drop(b); // 提前把 b 丢掉，计数立刻回到 1
    assert_eq!(Rc::strong_count(&a), 1);

    println!("{a}");
}
```

### 对 `Copy` 类型是空操作

```rust
fn main() {
    // Copy 类型传进去的是副本，原值不受影响
    let n = 42;
    drop(n);
    assert_eq!(n, 42);

    let flag = true;
    drop(flag);
    assert!(flag);

    // 引用同理：丢弃引用不影响被引用的值
    let owned = String::from("hello");
    drop(&owned);
    assert_eq!(owned.len(), 5);

    // 想真正提前释放，就交出不带 & 的值
    drop(owned);

    println!("{n} {flag}");
}
```

## 常见陷阱

1. **以为 `drop` 能清掉 `Copy` 值**：`drop(42)` 之后 `42` 仍在原变量里，`Copy` 意味着「复制后就地仍然有效」，没有任何函数能绕过这一点。
2. **手工调用 `Drop::drop`**：`x.drop()` 报 `E0040: explicit destructor calls not allowed`，只能用 `mem::drop(x)` 或让它自然离开作用域。
3. **`drop(&x)` 当成释放**：丢的是引用不是值，值要等作用域结束才析构；不过 `drop(&guard)` 有时用于提前结束借用，容易看花眼。
4. **在 `Drop` 实现里再调 `drop` 同一对象**：会造成重复析构的错觉甚至死循环，析构函数里应只做清理，不要再 self 相关的 `drop`。
5. **用它来「解锁」却传了引用**：`drop(guard)` 才释放 `MutexGuard` 的锁，`drop(&guard)` 只是结束这次借用。

## 相关

- [[mem|std::mem 模块]]：`drop` 与 `swap`、`take`、`replace` 并列。
- [[ops.Drop|Drop]]：自定义析构逻辑的特质，`mem::drop` 只是触发它的手段之一。
- [[mem.replace|replace]]：丢掉旧值时通常直接丢弃返回值，不必显式 `drop`。
- [[rc.Rc|Rc]]：判断「值有没有被释放」最直观的工具，`strong_count` 立刻反映。
- [[20-智能指针|智能指针]]：`Box`、`Rc`、`Arc` 的析构行为都依赖值被 drop。
