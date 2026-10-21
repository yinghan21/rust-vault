---
title: "std::any"
type: std-模块
module: any
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - any
一句话: 动态类型与类型反射：用 `Any` 把值装进 trait 对象，用 `TypeId` 与类型名做运行时判断。
---

# std::any

> [!abstract] 一句话
> `std::any` 提供运行时的「类型识别」能力：把任意具体类型装进 `dyn Any`，事后再判断它到底是什么类型、并把值取回来。

## 模块简介

Rust 是静态类型语言，泛型在编译期单态化，正常情况下「这个值是什么类型」在运行时根本不存在。`std::any` 是这个规则的逃生舱：所有 `'static` 类型都自动实现 `Any`，把值放进 `&dyn Any`、`&mut dyn Any` 或 `Box<dyn Any>` 之后，就能在运行时检查它是不是某个具体类型。

三个类型的分工很清晰。`TypeId` 是类型的全局唯一标识，可以比较、可以打印，适合做「类型 → 数据」的映射键。`Any` 在作为 trait 对象时才有用：`&dyn Any` 有 `is` 与 `downcast_ref`，`&mut dyn Any` 多一个 `downcast_mut`，`Box<dyn Any>` 再多一个 `downcast`。`type_name` 与 `type_name_of_val` 则返回类型名字符串，几乎只用于日志和调试输出。

它的用途集中在插件式结构、通用容器、以及 `Box<dyn Error>` 之类「先统一存起来、事后还原」的场景。需要特别注意它的局限：`Any` 只能判断**是不是某个具体类型**，不能判断**是否实现了某个 trait**——后者要靠 trait 对象；同时 `Any` 要求 `'static`，带借用生命周期的类型放不进去。

## 快速上手

```rust
use std::any::{type_name, Any, TypeId};

fn show(value: &dyn Any) {
    if let Some(text) = value.downcast_ref::<String>() {
        println!("是 String：{text}");
    } else if let Some(n) = value.downcast_ref::<i32>() {
        println!("是 i32：{n}");
    } else {
        println!("其他类型，TypeId = {:?}", value.type_id());
    }
}

fn main() {
    let boxed: Box<dyn Any> = Box::new(42i32);

    // 注意：直接对 Box 调用 type_id 得到的是 Box<dyn Any> 自己的标识
    // 先解引用成 &dyn Any，才拿到内部对象的类型标识
    assert_eq!((*boxed).type_id(), TypeId::of::<i32>());

    show(&"你好".to_string());
    show(&7i32);
    show(&1.5f64);

    println!("i32 的类型名是 {}", type_name::<i32>());
    println!("值的类型名是 {}", std::any::type_name_of_val(&boxed));
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| `TypeId` | 类型的全局唯一标识，可用于比较与作为映射键。 |
| `TypeId::of` | 取出某个具体类型的 `TypeId`。 |
| `Any` | 模拟动态类型的 trait，所有 `'static` 类型都自动实现。 |
| `Any::is` | 判断内部值是否是指定类型。 |
| `Any::downcast_ref` | 尝试取出 `&T`，类型不符返回 `None`。 |
| `Any::downcast_mut` | 尝试取出 `&mut T`。 |
| `Box<dyn Any>::downcast` | 尝试把 `Box<dyn Any>` 转成 `Box<T>`。 |
| `type_name` | 返回某个类型的名称字符串。 |
| `type_name_of_val` | 返回某个值的类型名称，不必写泛型参数。 |

## 注意事项

> [!warning] `.type_id()` 会返回容器自己的类型
> 在 `Box<dyn Any>`、`Arc<dyn Any>` 这类智能指针上直接调用 `.type_id()`，得到的是容器类型（如 `Box<dyn Any>`）的标识，而不是内部值的标识。先解引用成 `&dyn Any` 再调用，才是内部对象的类型。

> [!danger] `Any` 要求 `'static`
> 带借用生命周期的类型无法放进 `dyn Any`，编译会直接报生命周期错误。需要保存「可能借用外部数据」的值时，用泛型参数或显式生命周期，别硬塞进 `dyn Any`。

> [!tip] 类型名只适合看，不适合判断
> `type_name` 返回的字符串是实现细节，格式可能随编译器版本变化，不要拿它做逻辑分支；需要可靠的类型判断请比较 `TypeId`。

## 相关

- [[模块索引]]
- [[16-trait 对象与动态分发|trait 对象]]：`dyn Any` 就是 trait 对象的典型用法。
- [[error|std::error 模块]]：`Box<dyn Error>` 常与向下转型配合使用。
- [[marker|std::marker 模块]]：`Sized`、`'static` 等约束决定了 `Any` 的适用范围。
- [[option|std::option 模块]]：`downcast_ref` 返回的正是 `Option<&T>`。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 7 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`TypeId`](https://doc.rust-lang.org/std/any/struct.TypeId.html)

### 特质

- [`Any`](https://doc.rust-lang.org/std/any/trait.Any.html)
- [`TryAsDynCompatible`](https://doc.rust-lang.org/std/any/trait.TryAsDynCompatible.html)

### 函数

- [`type_name`](https://doc.rust-lang.org/std/any/fn.type_name.html)
- [`type_name_of_val`](https://doc.rust-lang.org/std/any/fn.type_name_of_val.html)
- [`try_as_dyn`](https://doc.rust-lang.org/std/any/fn.try_as_dyn.html)
- [`try_as_dyn_mut`](https://doc.rust-lang.org/std/any/fn.try_as_dyn_mut.html)

<!-- END AUTO ITEMS -->
