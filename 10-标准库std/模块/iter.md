---
title: "std::iter"
type: std-模块
module: iter
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - iter
一句话: "可组合的外部迭代：Iterator 特质与 map/filter/zip/chain 等惰性适配器。"
---

# std::iter

> [!abstract] 一句话
> `std::iter` 是 Rust 迭代器体系的家：核心是只有一个 `next` 方法的 `Iterator` 特质，配套一整套惰性、可组合、零成本的适配器。

## 模块简介

Rust 的 `for` 循环不是语言内置的魔法，而是对 `IntoIterator` + `Iterator` 的语法糖。任何实现了 `Iterator` 的类型都能用 `for` 遍历，也能链上 `map`/`filter`/`fold` 等方法。`std::iter` 就是这个体系的全部公开表面。

取迭代器有三种方式，对应三种所有权：`v.iter()` 借用元素（`Item = &T`），`v.iter_mut()` 可变借用（`Item = &mut T`），`v.into_iter()` 消耗集合并按值产出（`Item = T`）。写 `for x in &v` 等价于借用版，`for x in v` 等价于消耗版。

模块里的结构体（`Map`、`Filter`、`Enumerate`、`Zip`、`Chain`、`Peekable`……）几乎都是**适配器类型**，平时由方法返回，你不需要手写它们的名字。真正要看的是几个特质：`Iterator` 提供能力，`IntoIterator` 让类型能进 `for`，`FromIterator` 负责 `collect`，`Extend` 负责往已有集合追加，`DoubleEndedIterator`/`ExactSizeIterator`/`FusedIterator` 描述额外能力（能双向取、长度精确、耗尽后恒为 `None`）。

适配器是**惰性**的：`v.iter().map(f)` 本身不执行任何操作，只有遇到消费方法（`collect`、`fold`、`sum`、`count`、`for_each`、`next`）才逐个拉取。这个设计让编译器能把整条链内联成一次遍历，因此链式写法在优化后与手写循环速度相同——这就是常说的零成本抽象。

## 快速上手

```rust
use std::iter;

fn main() {
    let nums = vec![1, 2, 3, 4, 5, 6];

    // 一条链完成筛选 + 变换 + 收集，只遍历一次
    let evens_squared: Vec<i32> = nums.iter().filter(|n| *n % 2 == 0).map(|n| n * n).collect();
    assert_eq!(evens_squared, vec![4, 16, 36]);

    // enumerate 带下标，take 只取前 n 个
    let pairs: Vec<(usize, &i32)> = nums.iter().enumerate().take(2).collect();
    assert_eq!(pairs[1].0, 1);

    // 消费方法：sum / fold 把迭代器折叠成一个值
    let total: i32 = nums.iter().copied().sum();
    assert_eq!(total, 21);
    let product = nums.iter().copied().fold(1, |acc, n| acc * n);
    assert_eq!(product, 720);

    // 现场造迭代器再拼接
    let chained: Vec<i32> = iter::once(0).chain(nums.iter().copied().take(2)).collect();
    assert_eq!(chained, vec![0, 1, 2]);

    // zip 把两个迭代器并行拉链，短的先结束
    let zipped: Vec<(i32, &str)> = nums.iter().copied().zip(["a", "b"]).collect();
    assert_eq!(zipped, vec![(1, "a"), (2, "b")]);

    // find 返回第一个满足条件的元素
    assert_eq!(nums.iter().copied().find(|n| *n > 3), Some(4));

    // peekable 允许先看下一个元素再决定是否消费
    let mut it = nums.iter().peekable();
    assert_eq!(it.peek(), Some(&&1));
    assert_eq!(it.next(), Some(&1));
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[iter.Iterator\|Iterator]] | 迭代器核心特质，只需实现 `next`。 |
| [[iter.IntoIterator\|IntoIterator]] | 让类型能用于 `for` 与 `.into_iter()`。 |
| [[iter.FromIterator\|FromIterator]] | 从迭代器 `collect` 出一个集合。 |
| [[iter.Extend\|Extend]] | 用迭代器内容向已有集合追加。 |
| [[iter.DoubleEndedIterator\|DoubleEndedIterator]] | 支持两端取值，`rev` 的前提。 |
| [[iter.ExactSizeIterator\|ExactSizeIterator]] | 长度精确已知，可直接 `len`。 |
| `iter::Map` / `iter::Filter` | `map` / `filter` 返回的惰性适配器。 |
| `iter::Enumerate` / `iter::Zip` | 附带下标 / 并行拉链。 |
| `iter::Chain` / `iter::Rev` | 首尾相接 / 反向遍历。 |
| `iter::Peekable` | 可预看下一个元素。 |
| `iter::Take` / `iter::Skip` | 取前 n 个 / 跳过前 n 个。 |
| `iter::Fuse` / `iter::FusedIterator` | 耗尽后恒返回 `None`。 |
| `iter::once` / `iter::empty` | 构造单元素 / 空迭代器。 |
| `iter::repeat` / `iter::from_fn` | 无限重复 / 用闭包现场造迭代器。 |
| `iter::Sum` / `iter::Product` | 支撑 `sum` 与 `product` 聚合。 |

## 注意事项

> [!tip] 适配器不消费就不干活
> `v.iter().map(f);` 这行什么都不做，编译器还会给出 `unused_must_use` 警告。链的末端一定要有消费方法，或者把适配器返回给调用方。

> [!warning] `next` 返回 `None` 之后
> 多数适配器在返回 `None` 后继续调用 `next` 行为未指定，只有实现了 `FusedIterator` 的才保证永远返回 `None`。要在 `None` 之后继续安全使用，先调 `.fuse()`。

> [!danger] 别在循环里累加中间集合
> 每次 `collect` 都会分配内存。中途筛选请继续用适配器链，最后一次性收集；确实需要提前退出时用 `try_fold` 或 `find`/`any`，不要 `collect` 后再判断。

## 相关

- [[18-迭代器|迭代器]]：`Iterator` 方法全表与惰性求值讲解。
- [[collections|std::collections]]：`Vec`、`HashMap` 等集合的迭代器来源。
- [[option|std::option]]：`Option` 也能当 0 或 1 个元素的迭代器。
- [[range|std::range]]：`0..n` 这类范围本身也是迭代器。
- [[19-闭包|闭包]]：`map`、`filter`、`fold` 的参数都是闭包。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 60 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`Chain`](https://doc.rust-lang.org/std/iter/struct.Chain.html)
- [`Cloned`](https://doc.rust-lang.org/std/iter/struct.Cloned.html)
- [`Copied`](https://doc.rust-lang.org/std/iter/struct.Copied.html)
- [`Cycle`](https://doc.rust-lang.org/std/iter/struct.Cycle.html)
- [`Empty`](https://doc.rust-lang.org/std/iter/struct.Empty.html)
- [`Enumerate`](https://doc.rust-lang.org/std/iter/struct.Enumerate.html)
- [`Filter`](https://doc.rust-lang.org/std/iter/struct.Filter.html)
- [`FilterMap`](https://doc.rust-lang.org/std/iter/struct.FilterMap.html)
- [`FlatMap`](https://doc.rust-lang.org/std/iter/struct.FlatMap.html)
- [`Flatten`](https://doc.rust-lang.org/std/iter/struct.Flatten.html)
- [`FromFn`](https://doc.rust-lang.org/std/iter/struct.FromFn.html)
- [`Fuse`](https://doc.rust-lang.org/std/iter/struct.Fuse.html)
- [`Inspect`](https://doc.rust-lang.org/std/iter/struct.Inspect.html)
- [`Map`](https://doc.rust-lang.org/std/iter/struct.Map.html)
- [`MapWhile`](https://doc.rust-lang.org/std/iter/struct.MapWhile.html)
- [`Once`](https://doc.rust-lang.org/std/iter/struct.Once.html)
- [`OnceWith`](https://doc.rust-lang.org/std/iter/struct.OnceWith.html)
- [`Peekable`](https://doc.rust-lang.org/std/iter/struct.Peekable.html)
- [`Repeat`](https://doc.rust-lang.org/std/iter/struct.Repeat.html)
- [`RepeatN`](https://doc.rust-lang.org/std/iter/struct.RepeatN.html)
- [`RepeatWith`](https://doc.rust-lang.org/std/iter/struct.RepeatWith.html)
- [`Rev`](https://doc.rust-lang.org/std/iter/struct.Rev.html)
- [`Scan`](https://doc.rust-lang.org/std/iter/struct.Scan.html)
- [`Skip`](https://doc.rust-lang.org/std/iter/struct.Skip.html)
- [`SkipWhile`](https://doc.rust-lang.org/std/iter/struct.SkipWhile.html)
- [`StepBy`](https://doc.rust-lang.org/std/iter/struct.StepBy.html)
- [`Successors`](https://doc.rust-lang.org/std/iter/struct.Successors.html)
- [`Take`](https://doc.rust-lang.org/std/iter/struct.Take.html)
- [`TakeWhile`](https://doc.rust-lang.org/std/iter/struct.TakeWhile.html)
- [`Zip`](https://doc.rust-lang.org/std/iter/struct.Zip.html)
- [`ArrayChunks`](https://doc.rust-lang.org/std/iter/struct.ArrayChunks.html)
- [`ByRefSized`](https://doc.rust-lang.org/std/iter/struct.ByRefSized.html)
- [`FromCoroutine`](https://doc.rust-lang.org/std/iter/struct.FromCoroutine.html)
- [`Intersperse`](https://doc.rust-lang.org/std/iter/struct.Intersperse.html)
- [`IntersperseWith`](https://doc.rust-lang.org/std/iter/struct.IntersperseWith.html)
- [`MapWindows`](https://doc.rust-lang.org/std/iter/struct.MapWindows.html)

### 特质

- [[iter.DoubleEndedIterator|`DoubleEndedIterator`]]
- [[iter.ExactSizeIterator|`ExactSizeIterator`]]
- [[iter.Extend|`Extend`]]
- [[iter.FromIterator|`FromIterator`]]
- [`FusedIterator`](https://doc.rust-lang.org/std/iter/trait.FusedIterator.html)
- [[iter.IntoIterator|`IntoIterator`]]
- [[iter.Iterator|`Iterator`]]
- [`Product`](https://doc.rust-lang.org/std/iter/trait.Product.html)
- [`Sum`](https://doc.rust-lang.org/std/iter/trait.Sum.html)
- [`Step`](https://doc.rust-lang.org/std/iter/trait.Step.html)
- [`TrustedLen`](https://doc.rust-lang.org/std/iter/trait.TrustedLen.html)
- [`TrustedStep`](https://doc.rust-lang.org/std/iter/trait.TrustedStep.html)

### 函数

- [`chain`](https://doc.rust-lang.org/std/iter/fn.chain.html)
- [`empty`](https://doc.rust-lang.org/std/iter/fn.empty.html)
- [`from_fn`](https://doc.rust-lang.org/std/iter/fn.from_fn.html)
- [`once`](https://doc.rust-lang.org/std/iter/fn.once.html)
- [`once_with`](https://doc.rust-lang.org/std/iter/fn.once_with.html)
- [`repeat`](https://doc.rust-lang.org/std/iter/fn.repeat.html)
- [`repeat_n`](https://doc.rust-lang.org/std/iter/fn.repeat_n.html)
- [`repeat_with`](https://doc.rust-lang.org/std/iter/fn.repeat_with.html)
- [`successors`](https://doc.rust-lang.org/std/iter/fn.successors.html)
- [`zip`](https://doc.rust-lang.org/std/iter/fn.zip.html)
- [`from_coroutine`](https://doc.rust-lang.org/std/iter/fn.from_coroutine.html)

### 宏

- [`iter`](https://doc.rust-lang.org/std/iter/macro.iter.html)

<!-- END AUTO ITEMS -->
