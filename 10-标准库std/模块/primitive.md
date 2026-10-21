---
title: "std::primitive"
type: std-模块
module: primitive
stable: "1.43.0"
unstable: false
tags:
  - std/模块
  - std/类型
aliases:
  - primitive
一句话: "把原始类型（bool、i32、str、[T] 等）再导出成一个模块，好在名字被遮蔽时用全路径精确指向原始类型。"
---

# std::primitive

> [!abstract] 一句话
> `std::primitive` 只是把原始类型再导出成普通模块：`std::primitive::bool` 永远指向原始类型 `bool`，即使当前作用域里有个同名的 `struct bool`。

## 模块简介

原始类型不属于任何模块。`i32`、`bool`、`str`、`[T]`、`(A, B)`、`&T`、`*const T` 都由编译器内置，在任何模块、任何位置都能直接写出来——这也是为什么你从来不需要 `use std::primitive::i32;`。

`std::primitive` 做的事情很简单：把这些原始类型**再导出**成一个普通模块，于是多了一种绝对路径写法 `std::primitive::bool`。它存在的唯一理由是**名字遮蔽**：一旦你自己定义了 `struct bool`、`type str = ...`，或者宏展开时注入了同名类型，裸写 `bool` 指向的可能就不是原始类型了；此时 `std::primitive::bool` 仍然精确命中原始类型。官方文档也直说，这通常只在宏生成的代码里有意义——那段代码不知道调用方作用域里有什么名字。

用法上把它当成原始类型的命名空间即可：`std::primitive::usize`、`std::primitive::f64` 都是普通类型名，可以出现在字段类型、泛型实参、`as` 转换里；`std::primitive::str` 还能作为类型路径去调用 `str` 的固有方法。它不提供任何新能力，原始类型的方法文档仍然归到各自的「原始类型页」下。

## 快速上手

```rust
use std::primitive;

// 我们自己定义了一个叫 bool 的类型，它会遮蔽原始类型 bool
struct bool {
    value: primitive::bool,
}

impl bool {
    // 关联常量的类型必须写全路径，否则会递归指向 struct 自己
    const ENABLED: primitive::bool = true;
}

fn main() {
    let flag = bool { value: bool::ENABLED };
    assert!(flag.value);

    // primitive 里每个原始类型都可以当普通类型名使用
    let count: primitive::usize = 3;
    let ratio: primitive::f64 = count as primitive::f64 / 2.0;
    assert_eq!(ratio, 1.5);

    // str 的固有方法也能通过类型路径调用
    let text: &primitive::str = " 你好 ";
    assert_eq!(<primitive::str>::trim(text), "你好");

    println!("{} {} {}", flag.value, count, ratio);
}
```

## 常用条目

这个模块没有自己的条目，它是一份指向原始类型的别名清单。下表是「原始类型 ↔ 本库方法笔记」的对应关系。

| 条目 | 说明 |
| --- | --- |
| [[primitive.bool\|bool]] | 布尔值，只有 `true` / `false` 两个取值。 |
| [[primitive.char\|char]] | 单个 Unicode 标量值，4 字节定长。 |
| [[primitive.整数类型\|整数类型]] | `i8`…`i128`、`isize` 与 `u8`…`u128`、`usize` 合并成一页。 |
| [[primitive.浮点类型\|浮点类型]] | `f32` 与 `f64`，IEEE-754 二进制浮点数。 |
| [[primitive.str\|str]] | UTF-8 字符串切片，不定长，只能通过指针使用。 |
| [[primitive.slice\|slice]] | `[T]`，不定长切片，数组与 `Vec` 的公共视图。 |
| [[primitive.array\|array]] | `[T; N]`，长度写在类型里的定长数组。 |
| [[primitive.tuple\|tuple]] | `(A, B, …)`，字段按位置访问的异构组合。 |
| [[primitive.reference\|reference]] | `&T` 与 `&mut T`，借用检查的主角。 |
| `*const T` / `*mut T` | 原始指针，方法在 [[ptr\|std::ptr]] 里。 |
| `fn(A) -> B` | 函数指针，可当 `Fn` 用，见 [[ops.Fn\|Fn]]。 |
| `!` | never 类型，表示永不返回，用于发散表达式。 |

## 注意事项

> [!warning] 遮蔽是静默发生的
> 定义 `struct bool` 之后，本模块内所有裸写 `bool` 的地方都变成你的类型，编译器不会为此单独警告（只有命名风格 lint 哼一声），错误往往在很远的调用点才爆出来。宏里在类型位置使用外部传入的名字时，优先写 `std::primitive::` 全路径，或者用 `$crate::` 路径。

> [!tip] 它不解决「有没有」，只解决「是哪一个」
> `use std::primitive::i32;` 是可写但无意义的：裸写 `i32` 一直有效。这个模块不导入任何能力，只是给原始类型提供一个不会被遮蔽的路径；遇到「cannot find type」的错误，来这里 import 是没用的。

> [!danger] `str` 和 `[T]` 是不定长类型
> 它们的「大小」只有运行时才知道，所以不能作为局部变量、函数参数或返回值的类型直接出现：`let s: str = "x";` 永远编译不过，必须写成 `&str`、`Box<str>`、`&[T]`。`std::primitive::str` 之所以能用，是因为对它取了引用。

## 相关

- [[03-变量与数据类型|变量与数据类型]]：原始类型的赋值、推导与转换。
- [[primitive.str|str]]：最常用也最容易误解的原始类型。
- [[primitive.整数类型|整数类型]]：溢出、位运算与 `as` 转换规则。
- [[primitive.array|array]]：定长数组，与切片的关系。
- [[str|std::str]]：`str` 那一组模块级函数。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 0 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

<!-- END AUTO ITEMS -->
