---
title: "std::mem::take"
type: std-条目
kind: 函数
module: mem
slug: mem.take
stable: "1.40.0"
tags:
  - std/类型
aliases:
  - "take"
  - "mem::take"
一句话: "把 dest 换成 T::default()，返回被换下来的旧值；等价于 replace(dest, T::default())，要求 T: Default。"
---

# `take`

> [!abstract] 一句话
> `std::mem::take(&mut dest)` 用 `T::default()` 把 `dest` 填上，同时把原来的值取出来返回。它是 `replace(dest, T::default())` 的简写，比手写「取走再重新赋值」短，而且不会留下未初始化的空洞。

## 简介

「把一个字段取出来、原地留个空的」在 Rust 里很常见：`Vec` 的处理函数想交出缓冲、状态机想切换状态、`Option` 想拿走内部值。手写会撞上借用检查器：

```text
let buf = self.buf;      // error: cannot move out of `self.buf` which is behind a mutable reference
self.buf = Vec::new();
```

`mem::take` 用默认值填坑，一次完成这两步，且**不需要 `Clone`**——这正是它与 `self.buf.clone()` 的关键区别：`T` 只要实现 `Default`，有没有 `Clone` 都行。

函数与返回值的对应关系是 `pub fn take<T: Default>(dest: &mut T) -> T`：参数是可变引用，返回**被替换下来的旧值**（不是新值），返回值类型与位置上的类型相同。默认值来自 `T::default()`：`Vec` 是空向量、`String` 是空串、`Option` 是 `None`、整数是 `0`、实现了 `Default` 的结构体是各字段的默认值。

请注意一个容易混的点：`Option::take()` 是**方法**，不需要 `Default` 之外的东西（`Option<T>: Default` 恒为 `None`），语义与 `mem::take(&mut opt)` 相同；但 `mem::take` 是自由函数，对任意 `T: Default` 都可用。

## 签名与参数

```text
pub fn take<T: Default>(dest: &mut T) -> T
```

| 参数 | 说明 |
| --- | --- |
| `dest` | 要被「取空」的位置的可变引用，函数返回后里面是 `T::default()`。 |
| `T: Default` | 唯一约束：必须能用 `T::default()` 造出一个合法值来填坑。 |
| 返回 `T` | 替换下来的**旧值**，所有权移交给调用方。 |

| 想要的效果 | 用什么 |
| --- | --- |
| 取走旧值，留一个默认值 | `mem::take(&mut x)` |
| 取走旧值，留一个你指定的值 | [[mem.replace|replace]]，`mem::replace(&mut x, new)` |
| 只交换两个位置的值 | [[mem.swap|swap]]，`mem::swap(&mut a, &mut b)` |
| `Option` 专用的取走 | `opt.take()`，效果等价 |

## 示例

### 取走字段又不破坏结构体

```rust
use std::mem;

#[derive(Default)]
struct Buffer<T> {
    buf: Vec<T>,
}

impl<T> Buffer<T> {
    // 不用 Clone、也不用再写 `self.buf = Vec::new()` 这种方式
    fn take_all(&mut self) -> Vec<T> {
        mem::take(&mut self.buf)
    }
}

fn main() {
    let mut b = Buffer { buf: vec![1, 2, 3] };
    let taken = b.take_all();
    assert_eq!(taken, vec![1, 2, 3]);

    // 取走之后字段是 Default 的空 Vec，结构体依然可用
    assert!(b.buf.is_empty());
    assert!(b.take_all().is_empty());

    println!("{taken:?}");
}
```

### 常见默认值一览

```rust
use std::mem;

fn main() {
    let mut v: Vec<i32> = vec![1, 2];
    let old = mem::take(&mut v);
    assert_eq!(old, vec![1, 2]);
    assert!(v.is_empty());

    let mut s = String::from("hello");
    assert_eq!(mem::take(&mut s), "hello");
    assert_eq!(s, "");

    let mut opt: Option<i32> = Some(7);
    assert_eq!(mem::take(&mut opt), Some(7));
    assert_eq!(opt, None);

    let mut n = 42;
    assert_eq!(mem::take(&mut n), 42);
    assert_eq!(n, 0);

    println!("{v:?} {s:?} {opt:?} {n}");
}
```

## 常见陷阱

1. **类型没有实现 `Default`**：`mem::take(&mut x)` 会报 `T: Default` 未满足，这时用 [[mem.replace|replace]] 给一个你造的值。
2. **以为 `Default` 是「清空但保留容量」**：`Vec::default()` 是容量为 0 的新 `Vec`，原来那块堆内存已随旧值交给你，若还想复用其中容量得自己 `clear()`。
3. **忘了它需要 `&mut`**：对 `&T` 调不了，也不能对不可变字段调；结构体方法要声明 `&mut self`。
4. **在 `Option` 上用 `mem::take` 却把结果丢了**：`mem::take(&mut opt);` 会取走值并立即丢弃，想知道取到的是什么就得绑定返回值。
5. **把 `mem::take` 和 `Cell::take` 搞混**：`Cell<T: Default>` 有同名的 `take` 方法，无需 `&mut`，但那是 `cell` 模块的语义，两者不要混着讲。

## 相关

- [[mem|std::mem 模块]]：`take` 与 `swap`、`replace`、`drop` 一起构成内存操作工具箱。
- [[mem.replace|replace]]：可以指定填充值，不必依赖 `Default`。
- [[default.Default|Default]]：`take` 的唯一约束，也解释了各种类型的默认值。
- [[option.Option|Option]]：`opt.take()` 与 `mem::take(&mut opt)` 等价。
- [[string.String|String]]、[[vec.Vec|Vec]]：最常被 `take` 的两个类型，默认值分别是空串与空向量。
