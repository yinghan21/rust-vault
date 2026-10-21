---
title: "std::primitive::reference"
type: std-条目
kind: 原始类型
module: primitive
slug: primitive.reference
stable: "1.0.0"
tags:
  - std/类型
aliases:
  - Type reference
一句话: 引用 `&T` 与 `&mut T`，是对某个值的借用，保证非空、对齐且指向有效数据。
---

# `&T` / `&mut T`

> [!abstract] 一句话
> 引用是**对某个值的借用**：`&T` 是共享（只读）借用，可以同时存在多个；`&mut T` 是可变（独占）借用，同一时刻只能有一个，且不能与共享借用并存。

## 简介

获得引用的方式有两种：对值使用 `&` / `&mut` 运算符，或在模式里写 `ref` / `ref mut`。引用本身是个指针，但比裸指针多了三条**编译器保证**：非空、对齐、指向一个有效的 `T` 值。因此 `&bool` 只能指向存放 `0`/`1` 的内存，而 `Option<&T>` 的内存布局与「可空但已对齐的指针」相同，可以安全地跨 FFI 传递。

绝大多数情况下引用用起来就像被引用的值本身：字段访问、方法调用、下标都自动解引用，比较运算符也会透明地转发到被引用值的实现上，所以 `&i32` 可以直接和 `&i32` 比大小。`&T` 实现 `Copy`（复制的是地址），`&mut T` **不实现** `Copy`，只能移动或重新借用。

引用是 Rust 借用检查的核心：[[05-所有权|所有权]] 说明值归谁所有，借用规则说明「谁能读、谁能写」；一个引用的有效期由 [[17-生命周期|生命周期]] 标注和推断。它和裸指针 `*const T` / `*mut T` 的分工是：日常代码用引用，需要跨 FFI、做自引用结构或手写容器时才用裸指针并加 `unsafe`。

## 常用方法

数据源中引用的稳定方法为 **0 个**：`&T` / `&mut T` 没有固有方法，所有能力来自运算符语法、自动解引用与 trait 实现。

- **解引用**：`*r` 取出被引用的值；对实现了 `Deref` 的类型（如 [[boxed.Box|Box]]、[[string.String|String]]），`*` 会逐层深入到目标类型。
- **自动解引用**：`r.method()`、`r.field`、`r[i]` 都会自动按需加 `*` 或取地址，无需手写 `(*r).method()`。
- **重新借用**：`&*r`、`&mut *r` 从一个引用得到新的引用，可变引用靠它「再借一次」而不移动。
- **比较**：`==`、`<` 转发到被引用值的 `PartialEq` / `PartialOrd`，比较的是**值**而不是地址；比较地址用 `std::ptr::eq`。
- **Deref 强制转换**：`&String` → `&str`、`&Vec<T>` → `&[T]`、`&Box<T>` → `&T` 在函数调用处自动发生。

## 示例

```rust
use std::ptr;

fn main() {
    let mut x = 5;

    // 共享引用：同一时刻可以同时存在多个
    let a = &x;
    let b = &x;
    assert_eq!(*a + *b, 10);

    // == 比较值，ptr::eq 比较地址
    assert_eq!(a, b);
    assert!(ptr::eq(a, b));

    // 共享借用全部结束后，才能取得可变借用
    let m = &mut x;
    *m += 1;
    assert_eq!(x, 6);
}
```

引用作为参数时的自动解引用与重新借用：

```rust
fn first_word(s: &str) -> &str {
    s.split_whitespace().next().unwrap_or("")
}

fn total(data: &[i32]) -> i32 {
    data.iter().sum()
}

fn main() {
    let owned = String::from("hello world");
    assert_eq!(first_word(&owned), "hello"); // &String 自动转成 &str

    let v = vec![1, 2, 3];
    assert_eq!(total(&v), 6); // &Vec<i32> 自动转成 &[i32]

    let mut n = 1;
    {
        let m = &mut n;
        *m = 2;

        // &mut T 不实现 Copy，要再借一次只能写 &mut *m
        let again = &mut *m;
        *again = 3;
    }
    assert_eq!(n, 3);
}
```

## 常见陷阱

1. **可变借用与共享借用并存**：`let a = &v; let b = &mut v;` 直接编译不过；对策是把前一个借用的使用范围缩小到 `{}` 里。
2. **`&mut T` 被当成可复制的**：`let b = a;` 会移动可变引用，`a` 之后不可用；需要继续用就写 `&mut *a` 重新借用。
3. **返回局部变量的引用**：函数里创建的值的引用不能返回，编译器会报生命周期错误；对策是返回拥有型（`String`、`Vec<T>`）或让调用方传入缓冲区。
4. **误把 `==` 当比较地址**：引用上的 `==` 比较被引用的值，两个不同变量但值相等时也为 `true`；要判断是否同一块内存用 `std::ptr::eq`。
5. **函数签名写过重的引用类型**：`fn f(s: &String)` 会拒绝 `&str` 调用，尽量写 `&str` / `&[T]` / `&dyn Trait`，让 Deref 强制转换发挥作用。

## 相关

- [[primitive|std::primitive 模块]]：`reference`、`tuple`、`array` 等原始类型页的入口。
- [[06-借用与引用|借用]]：借用规则、可变借用的独占性、NLL 之后的作用域判断。
- [[17-生命周期|生命周期]]：引用有效性如何被标注与推断。
- [[ptr|std::ptr 模块]]：`ptr::eq`、`ptr::read` 等裸指针操作，与引用互补。
- [[05-所有权|所有权]]：引用解决「不交出所有权也能使用值」的问题。
