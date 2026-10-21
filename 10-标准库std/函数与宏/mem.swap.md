---
title: "std::mem::swap"
type: std-条目
kind: 函数
module: mem
slug: mem.swap
stable: "1.0.0"
tags:
  - std/类型
aliases:
  - "swap"
  - "mem::swap"
一句话: "交换两个可变引用指向的值，双方都不会被提前析构；不分配、不拷贝元素、不会 panic。"
---

# `swap`

> [!abstract] 一句话
> `std::mem::swap(&mut a, &mut b)` 把两块内存里的值对调，两边始终都是「已初始化」的合法值。它是安全函数，不需要 `unsafe`，也不会 panic。

## 简介

交换两个值在别的语言里通常要一个临时变量：`let t = a; a = b; b = t;`。在 Rust 里这样写会因为「把 `a` 移走」而被借用检查器拦住——`a` 移走的瞬间，它在原地是未初始化的，如果赋值前发生 panic，`a` 就会被重复析构或读到垃圾。

`mem::swap` 正是为此设计的：它在实现上用一次 `ptr::swap` 逐字节对调两块内存，因此**两个位置从头到尾都是初始化的**，不存在中间的空洞，也就不需要 `unsafe` 让调用方保证任何事。它只搬动值本身（对 `Vec`、`String` 来说就是那三个字：指针、长度、容量），不复制堆上的元素。

函数的两个参数都是 `&mut T`，所以调用处要用 `&mut` 显式借用。返回值是 `()`。因为没有 panic 分支、没有分配，它是真正的零成本抽象，编译后与手写三次移动等价。

顺带说明几个常见的「交换」入口：切片有两个元素要换用 `slice::swap(i, j)`；整个 `Vec` 的两个元素交换可以用 `v.swap(i, j)`；只想换掉某处旧值、新的来自别处就用 [[mem.replace|replace]]，不想给新值就用 [[mem.take|take]]。

## 签名与参数

```text
pub fn swap<T>(x: &mut T, y: &mut T)
```

| 参数 | 说明 |
| --- | --- |
| `x` | 第一个位置的可变引用，交换后持有原来 `y` 的值。 |
| `y` | 第二个位置的可变引用，交换后持有原来 `x` 的值。 |
| 返回 `()` | 原地完成，无返回值；不 panic、不分配。 |

- 泛型 `T` 没有 `Clone`、`Copy`、`Default` 等任何约束，任意大小的类型都能换。
- 两个 `&mut` 必须指向**互不重叠**的位置，这是可变引用借用规则本身要求的，`mem::swap(&mut a, &mut a)` 会在编译期被拒绝。
- 同一个结构体的多个字段属于互不重叠的借用，可以直接换；但 `v[i]`、`arr[i]` 这类下标要经过 `IndexMut`，取不出两个 `&mut`，索引交换请用 `slice::swap` / `Vec::swap` / 数组自带的 `swap` 方法。

## 示例

### 基本交换与字段交换

```rust
use std::mem;

#[derive(Debug, PartialEq)]
struct Point {
    x: i32,
    y: i32,
}

fn main() {
    let mut x = 5;
    let mut y = 42;

    mem::swap(&mut x, &mut y);
    assert_eq!(x, 42);
    assert_eq!(y, 5);

    // 同一结构体的两个字段是互不重叠的借用，可以直接换
    let mut p = Point { x: 1, y: 2 };
    mem::swap(&mut p.x, &mut p.y);
    assert_eq!(p, Point { x: 2, y: 1 });

    // 数组/切片的下标要走 IndexMut，取不到两个 &mut，得用自带的 swap
    let mut arr = [1, 2, 3];
    arr.swap(0, 2);
    assert_eq!(arr, [3, 2, 1]);

    println!("{p:?} {arr:?} {x} {y}");
}
```

### 交换 `Vec` 只搬三个字

```rust
use std::mem;

fn main() {
    let mut a = vec![1, 2, 3];
    let mut b = Vec::new();

    // 不是逐元素复制，而是把 (ptr, len, cap) 对调
    mem::swap(&mut a, &mut b);
    assert!(a.is_empty());
    assert_eq!(b, vec![1, 2, 3]);

    // 常见用法：把「当前缓冲」换出来处理，下一轮用空的新缓冲
    let mut current = vec![String::from("hello")];
    let mut next = Vec::new();
    mem::swap(&mut current, &mut next);
    assert!(current.is_empty());
    assert_eq!(next[0], "hello");

    println!("{next:?}");
}
```

## 常见陷阱

1. **对同一个变量取两次 `&mut`**：`mem::swap(&mut a, &mut a)` 报 `cannot borrow a as mutable more than once`，编译器不会因为「逻辑上是空操作」而放行。
2. **想交换 Vec 里的两个元素却对元素取了 `&mut`**：`mem::swap(&mut v[0], &mut v[1])` 因为两次 `IndexMut` 借用重叠而失败，改用 `v.swap(0, 1)`。
3. **在切片上用 `mem::swap`**：两个下标是运行时变量时借不到 `&mut`，改用 `slice::swap(i, j)`。
4. **以为它会 copy 一份**：`mem::swap` 不做 `Clone`，堆上数据只是换了主人，交换两个大 `Vec` 也是常数时间。
5. **拿它当「重置」手段**：交换后旧值仍在另一处，要清空请用 [[mem.take|take]]（默认值）或 [[mem.replace|replace]]（指定新值）。

## 相关

- [[mem|std::mem 模块]]：`swap`、`take`、`replace`、`drop` 这一组内存操作的归属模块。
- [[mem.replace|replace]]：把新值放进某一个位置，返回旧值。
- [[mem.take|take]]：用 `Default` 填充某个位置并取走旧值。
- [[vec.Vec|Vec]]：`Vec::swap` 是交换下标元素的专用方法。
- [[primitive.slice|Type slice]]：`slice::swap(i, j)` 处理运行时下标。
