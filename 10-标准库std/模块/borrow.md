---
title: "std::borrow"
type: std-模块
module: borrow
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - borrow
一句话: 借用相关的三个工具：`Borrow` / `BorrowMut` 提供跨类型的借用契约，`ToOwned` 与 `Cow` 负责借用与拥有之间的转换。
---

# std::borrow

> [!abstract] 一句话
> `std::borrow` 定义了「按另一种类型借用自己」的规则，以及一个读多写少时很好用的写时克隆智能指针 `Cow`。

## 模块简介

`std::borrow` 要解决的是「同一个数据，用不同但等价的类型来表示」。最典型的一对是 `String` 与 `str`：`String` 拥有数据，`&str` 借用同样的数据。`Borrow<str>` 就是这条关系的正式声明，标准库的 `HashMap::get`、`BTreeMap::get` 都建立在它之上——所以你能用 `&str` 直接查一个 `HashMap<String, _>`。`BorrowMut` 是它的可变版本。

`ToOwned` 则把 `Clone` 推广到「借用数据」上。`Clone` 只能从 `&T` 得到 `T`，而 `ToOwned` 允许从 `&Borrowed` 得到另一种拥有所有权的类型：`str: ToOwned<Owned = String>`、`[T]: ToOwned<Owned = Vec<T>>`。`Cow<'a, B>`（clone-on-write）把这两件事组合成一个枚举：`Borrowed` 时借别人的数据、不分配；需要修改时 `to_mut()` 克隆一次，变成 `Owned` 之后随便改。

实际使用它的地方通常是「函数既想接受 `&str` 又想接受 `String`，还不想强制调用方分配」：参数写 `Cow<'_, str>`，纯透传时零成本，真要改的时候才付一次拷贝。要注意 `Borrow` 是**契约**而不只是转换：借用出来的形式必须与自身在 `Eq`、`Hash`、`Ord` 上表现一致，否则哈希表会出现「存进去了却查不到」。这也是它和 [[convert|std::convert]] 里 `AsRef` 的核心区别——`AsRef` 只要求能转，不要求语义一致。

## 快速上手

```rust
use std::borrow::{Cow, ToOwned};
use std::collections::HashMap;

fn main() {
    // Cow：只在需要修改时才克隆底层数据
    let mut title: Cow<str> = Cow::Borrowed("rust");
    title.to_mut().push_str(" 标准库");
    assert_eq!(title, "rust 标准库");

    // 只读时按 &str 使用，两次调用共享同一块数据
    fn word_count(text: &str) -> usize {
        text.split_whitespace().count()
    }
    assert_eq!(word_count(&title), 2);

    // ToOwned：从借用数据得到拥有所有权的版本
    let owned: String = "abc".to_owned();
    let borrowed: &str = owned.as_str();

    // Borrow：HashMap<String, _> 可以直接用 &str 查询
    let mut scores: HashMap<String, u8> = HashMap::new();
    scores.insert("小明".to_string(), 90);
    let key: &str = "小明";
    assert_eq!(scores.get(key), Some(&90));

    println!("{} / {} / {}", title, borrowed, scores.len());
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[borrow.Borrow|Borrow]] | 以另一种类型借用自身，`HashMap` 查询依赖它。 |
| `BorrowMut` | `Borrow` 的可变版本，返回 `&mut Borrowed`。 |
| `ToOwned` | `Clone` 对借用数据的推广，产出拥有所有权的类型。 |
| [[borrow.Cow|Cow]] | 写时克隆智能指针，枚举 `Borrowed` 与 `Owned`。 |
| `Cow::Borrowed` | 包装一份借用数据的变体，不分配内存。 |
| `Cow::Owned` | 包装一份拥有所有权数据的变体。 |
| `Cow::to_mut` | 需要修改时克隆出 `&mut B`，之后就是拥有状态。 |
| `Cow::into_owned` | 取出拥有所有权的版本，必要时才克隆。 |
| `Cow<str>` / `Cow<[T]>` | 实际项目里最常见的两种实例化。 |

## 注意事项

> [!danger] `Borrow` 是契约，不是普通转换
> 实现 `Borrow` 的类型必须保证借用出来的形式与自身在 `Eq`、`Hash`、`Ord` 上完全一致。只想要「能转成 `&str`」请实现 `AsRef`；把 `Borrow` 当作 `AsRef` 用，会让 `HashMap`、`BTreeMap` 的行为变得难以预期。

> [!tip] `Cow` 的写时复制只发生一次
> `to_mut()` 只在当前还是 `Borrowed` 时克隆一次，之后都直接修改拥有的数据；纯只读的 `&*cow`、`cow.len()` 不会触发分配。所以「大部分情况只读、偶尔修改」的解析结果、配置合并非常适合 `Cow`。

> [!warning] 生命周期会跟着走
> `Cow<'a, B>` 带生命周期，`'a` 结束之后就不能再持有借用版本。想在结构体里长期保存，通常直接存 `String` / `Vec`；`Cow` 更适合函数参数与短生命周期的中间结果。

## 相关

- [[模块索引]]
- [[convert|std::convert 模块]]：`AsRef`、`From` 等更宽松的转换 trait。
- [[clone|std::clone 模块]]：`Clone` 与 `ToOwned` 的分工。
- [[string|std::string 模块]]：`String` 与 `str` 的借用关系。
- [[17-生命周期|生命周期]]：`Cow<'a, B>` 里那个 `'a` 的含义。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 4 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 枚举

- [[borrow.Cow|`Cow`]]

### 特质

- [[borrow.Borrow|`Borrow`]]
- [`BorrowMut`](https://doc.rust-lang.org/std/borrow/trait.BorrowMut.html)
- [`ToOwned`](https://doc.rust-lang.org/std/borrow/trait.ToOwned.html)

<!-- END AUTO ITEMS -->
