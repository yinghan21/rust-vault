---
title: "std::array"
type: std-模块
module: array
stable: "1.35.0"
unstable: false
tags:
  - std/模块
aliases:
  - array
一句话: 固定长度数组 `[T; N]` 的构造、转换工具与按值迭代器。
---

# std::array

> [!abstract] 一句话
> `std::array` 是 `[T; N]` 的配套模块：几个构造与转换函数，加上数组「按值迭代」用的 `IntoIter`，以及切片转数组失败时的错误类型。

## 模块简介

Rust 的数组 `[T; N]` 把长度写进了类型：`[u8; 4]` 和 `[u8; 8]` 是两个不同的类型，大小在编译期就固定，数据直接放在栈上（或所在的结构体里），没有额外的长度字段和堆分配。这个模块负责「怎么把数组造出来、怎么和切片互转、怎么把元素一个个拿走」。

模块本身很小，常用的就三件事。构造：`from_fn` 按索引生成每个元素，最灵活；`repeat` 克隆一个值填满；`from_ref` / `from_mut` 把单值引用包装成长度为 1 的数组引用，不发生拷贝。转换：切片转数组用 `<[T; N]>::try_from`，长度不对会得到 `TryFromSliceError`。迭代：`array::IntoIter` 就是 `into_iter()` 的返回类型，逐个交出元素的所有权。

数组的绝大多数「操作型」方法（`map`、`each_ref`、`as_slice` 等）挂在 `[T; N]` 自己的固有方法上，不在这个模块里。日常用它和 [[slice|std::slice]] 打交道：数组引用可以自动退化为切片传参，需要动态长度时则换成 [[vec|std::vec]] 的 `Vec<T>`。

## 快速上手

```rust
use std::array;

fn main() {
    // 按索引生成数组，结果为 0、1、4、9、16
    let squares: [i32; 5] = array::from_fn(|i| (i * i) as i32);
    assert_eq!(squares, [0, 1, 4, 9, 16]);

    // 把单个值的引用包装成长度为 1 的数组引用，不发生拷贝
    let x = 7u8;
    let one: &[u8; 1] = array::from_ref(&x);
    assert_eq!(one, &[7]);

    // 按值迭代数组，逐个交出元素本身（2021 版行为）
    let sum: i32 = squares.into_iter().sum();
    assert_eq!(sum, 30);

    // 长度不对的切片转数组会得到 TryFromSliceError
    let failed = <[i32; 2]>::try_from(&squares[..3]);
    assert!(failed.is_err());

    println!("{squares:?} 求和 = {sum}");
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| `array::from_fn` | 用「索引 → 元素」的闭包生成数组。 |
| `array::repeat` | 反复克隆同一个值来填充数组。 |
| `array::from_ref` | 把 `&T` 变成 `&[T; 1]`，零拷贝。 |
| `array::from_mut` | 把 `&mut T` 变成 `&mut [T; 1]`，零拷贝。 |
| `array::try_from_fn` | 逐元素构造，允许每个元素构造失败。 |
| `array::IntoIter` | `[T; N]` 的按值迭代器，交出元素所有权。 |
| `array::TryFromSliceError` | 切片长度与数组长度不符时的错误类型。 |
| `<[T; N]>::map` | 逐元素映射，长度不变。 |
| `<[T]>::try_into` | 把切片转成数组，长度不符返回错误。 |
| `&[T; N]` 到 `&[T]` | 数组引用自动退化为切片，可直接传参。 |

## 注意事项

> [!warning] 版本差异：`into_iter()` 的行为
> 2021 版里 `arr.into_iter()` 是按值迭代，交出元素本身；2015 / 2018 版出于兼容考虑会得到引用。迁移旧代码时如果依赖「迭代出来是 `&T`」，需要显式写 `arr.iter()`。

> [!danger] 长度必须在编译期确定
> `[T; N]` 的 `N` 只能是常量：运行期才知道长度的场景要用 `Vec<T>` 或 `Box<[T]>`。从切片转数组请用 `try_into`，长度不符会返回 `TryFromSliceError`，不要用 `unwrap` 掩盖真正的外部输入问题。

> [!tip] 大数组注意栈空间
> 数组直接放在栈上，几百 KB 以上的数组容易把栈撑爆。需要大缓冲区时优先用 `Vec` 或 `Box<[T]>`；注意 `Box::new([0; N])` 也会先在栈上构造再移动，特别大时仍可能溢出。

## 相关

- [[模块索引]]
- [[slice|std::slice 模块]]：数组与切片之间的转换与常用方法。
- [[vec|std::vec 模块]]：长度在运行期可变时的选择。
- [[iter|std::iter 模块]]：`IntoIter` 与迭代器适配器的关系。
- [[03-变量与数据类型|变量与数据类型]]：数组类型的基本语法。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 7 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`IntoIter`](https://doc.rust-lang.org/std/array/struct.IntoIter.html)
- [`TryFromSliceError`](https://doc.rust-lang.org/std/array/struct.TryFromSliceError.html)

### 函数

- [`from_fn`](https://doc.rust-lang.org/std/array/fn.from_fn.html)
- [`from_mut`](https://doc.rust-lang.org/std/array/fn.from_mut.html)
- [`from_ref`](https://doc.rust-lang.org/std/array/fn.from_ref.html)
- [`repeat`](https://doc.rust-lang.org/std/array/fn.repeat.html)
- [`try_from_fn`](https://doc.rust-lang.org/std/array/fn.try_from_fn.html)

<!-- END AUTO ITEMS -->
