---
title: "std::prelude"
type: std-模块
module: prelude
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - prelude
一句话: 每个程序都自动带入的名字清单：Option、Result、Vec、String、Box 以及常见 trait，所以不需要手动 use。
---

# std::prelude

> [!abstract] 一句话
> prelude 是编译器在每个 crate 开头隐式插入的 `use`：`Option`、`Result`、`Vec`、`String`、`Box` 和一批常用 trait 本来就在作用域里，写代码时不用导入，也**不要**手动导入。

## 模块简介

如果没有 prelude，每个 Rust 程序开头都得先写十几行 `use`，把 `Option`、`Vec`、`String`、`Clone`、`Iterator` 一个个请进来；可反过来把所有东西都自动导入，又会污染命名空间、拖慢解析。prelude 是这两者之间的折中：只放「几乎每个程序都会用到」的名字，数量刻意压得很小。

它的收录偏好很明确——**优先收 trait**。类型只在需要时写名字，而 trait 决定了方法能不能调用：`Clone` 不在作用域里，`.clone()` 就找不到；`Iterator` 不在作用域里，`.map()` 全部失效。所以 prelude 里塞满了比较、克隆、转换、迭代、析构、线程安全这些「能力型」trait，类型则只有最常用的几个。

prelude 不是唯一一份。编译器按 edition 自动选择 `rust_2015`、`rust_2018`、`rust_2021`、`rust_2024` 中的一份（老的 `v1` 是它们的共同底座）：2021 版补进了 `TryFrom`、`TryInto`、`FromIterator`，2024 版又补进了 `Future` 与 `IntoFuture`。标准库之外还有若干**需要手动 `use` 的小 prelude**，例如 `std::io::prelude`、`std::os::unix::prelude`，它们把某个领域的一组 trait 打包，方便一次导入。

因此这一页的重点不是「怎么导入」，而是「哪些名字本来就在、哪些不在」。需要额外能力时精确 `use` 那一个 trait 即可；为了让代码「更明确」而写 `use std::prelude::rust_2021::*;`，只会得到重复导入和换 edition 时的麻烦。

## 快速上手

```rust
// 整段代码没有任何 use：下面用到的名字全部由 prelude 提供
fn main() {
    // Vec、String、ToString、From
    let names: Vec<String> = ["rust", "pin", "range"]
        .into_iter()
        .map(String::from)
        .collect();
    assert_eq!(names.len(), 3);

    // Option、Clone
    let first: Option<&String> = names.first();
    assert_eq!(first.cloned(), Some(String::from("rust")));

    // Result、PartialEq
    let parsed: Result<i32, _> = "42".parse::<i32>();
    assert_eq!(parsed.unwrap(), 42);

    // Default
    let empty: Vec<i32> = Vec::default();
    assert!(empty.is_empty());

    // Iterator、IntoIterator、Extend
    let mut acc = Vec::new();
    acc.extend(1..=3);
    let total: i32 = acc.iter().sum();
    assert_eq!(total, 6);

    // Copy、PartialOrd
    let a = 1u8;
    let b = a;
    assert!(a < b + 1);
    assert_eq!(a, b);

    println!("{:?} {}", names, total);
}
```

## prelude 里有什么

这个模块本身没有自己的条目，它是把已有类型和 trait 再导出成一份清单。下面是日常最常撞见的部分。

### 类型与值

| 名字 | 说明 |
| --- | --- |
| [[option.Option\|Option]]（含 `Some`、`None`） | 可空值，替代空指针。 |
| [[result.Result\|Result]]（含 `Ok`、`Err`） | 可恢复错误的标准容器。 |
| [[vec.Vec\|Vec]] | 动态数组，`vec!` 宏也在作用域里。 |
| [[string.String\|String]] | 拥有的 UTF-8 字符串；`&str` 是原始类型，本来就在作用域中。 |
| [[boxed.Box\|Box]] | 堆上的独占指针。 |
| [[mem.drop\|drop]] | 提前释放值，手动触发析构。 |

### trait

| 名字 | 说明 |
| --- | --- |
| [[clone.Clone\|Clone]] | `.clone()`，克隆出独立的值。 |
| [[marker.Copy\|Copy]] | 按位复制，赋值后原变量仍然可用。 |
| [[cmp.PartialEq\|PartialEq]] / [[cmp.Eq\|Eq]] | `==`、`!=`，以及「全等」标记。 |
| [[cmp.PartialOrd\|PartialOrd]] / [[cmp.Ord\|Ord]] | `<`、`>` 与全序，`sort()` 需要 `Ord`。 |
| [[default.Default\|Default]] | `T::default()`，也是 `HashMap::new` 之类的基础。 |
| [[ops.Drop\|Drop]] | 离开作用域时自动执行的析构。 |
| [[ops.Fn\|Fn]] / `FnMut` / `FnOnce` | 闭包的三种调用能力，写泛型约束时天天用。 |
| [[convert.AsRef\|AsRef]] / `AsMut` | 低成本借用转换，`impl AsRef<Path>` 的常客。 |
| [[convert.From\|From]] / [[convert.Into\|Into]] | `T::from(x)` 与 `.into()`。 |
| [[string.ToString\|ToString]] | `.to_string()`，所有实现了 `Display` 的类型自动拥有。 |
| [[iter.Iterator\|Iterator]] / [[iter.IntoIterator\|IntoIterator]] | 迭代：`.map()`、`.collect()` 与 `for` 循环都靠它们。 |
| [[iter.Extend\|Extend]] | `.extend(iter)`，`collect()` 的底层约束之一。 |
| [[iter.DoubleEndedIterator\|DoubleEndedIterator]] / [[iter.ExactSizeIterator\|ExactSizeIterator]] | `.rev()` / `.len()` 这类能力。 |
| [[marker.Send\|Send]] / [[marker.Sync\|Sync]] | 跨线程移动 / 共享的自动标记。 |
| `Sized` / `Unpin` | 编译期标记：定长类型、可安全移动的类型。 |

### 按 edition 增加的

| edition | 新增到 prelude |
| --- | --- |
| 2015 / 2018 | 上面两张表的主体（`v1` 基础清单）。 |
| 2021 | [[convert.TryFrom\|TryFrom]]、`TryInto`、[[iter.FromIterator\|FromIterator]]。 |
| 2024 | [[future.Future\|Future]]、`IntoFuture`。 |

## 注意事项

> [!warning] 不要手动 `use` prelude
> `use std::prelude::rust_2021::*;` 这类写法是纯噪音：这些名字本来就在作用域里，重复导入不会让代码「更明确」，只会让换 edition 时多一处需要同步维护的地方，还容易和本地导入撞名。真正需要显式的，是 prelude 里没有的那一个 trait。

> [!tip] `Debug` 和 `Display` 不在 prelude
> `println!("{x}")`、`{:?}` 不需要它们在作用域，格式化宏按 trait 约束工作；`#[derive(Debug)]` 也是编译器内置识别的派生宏。但如果你要在签名里写 `T: Debug`，或者手动调用 `.fmt()`，就必须 `use std::fmt::Debug;`——这时报的错是「cannot find trait `Debug` in this scope」。

> [!danger] 同名项会静默遮蔽 prelude
> 自己定义 `struct Vec;`，或者 `use 某个依赖::Clone;`，都会把 prelude 的版本顶掉：后面所有 `Vec` 和 `.clone()` 都指向你的项，报错位置却离定义很远。宏生成的代码尤其容易踩到，所以模板里常用全路径 `std::vec::Vec`、`std::string::String`。

## 相关

- [[10-模块与可见性|模块与可见性]]：`use`、路径与作用域的完整规则。
- [[15-trait 基础|trait 基础]]：为什么 trait 必须在作用域里才能调方法。
- [[option.Option|Option]]：prelude 里使用频率最高的类型。
- [[iter.Iterator|Iterator]]：prelude 收录的最大一块能力。
- [[vec.Vec|Vec]]：另一个几乎每页都会出现的名字。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 0 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

<!-- END AUTO ITEMS -->
