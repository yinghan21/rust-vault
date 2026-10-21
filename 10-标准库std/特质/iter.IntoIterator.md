---
title: "std::iter::IntoIterator"
type: std-条目
kind: 特质
module: iter
slug: iter.IntoIterator
stable: "1.0.0"
tags:
  - std/特质
  - std/类型
aliases:
  - IntoIterator
一句话: 定义类型如何转换成迭代器，实现它就能直接用于 for 循环。
---

# `IntoIterator`

> [!abstract] 一句话
> `IntoIterator` 定义「一个值怎么变成迭代器」：实现它之后，该类型就能直接写进 `for` 循环，`iter()`、`into_iter()` 之类的方法才有落点。

## 简介

`for x in something` 里的 `something` 必须实现 `IntoIterator`，而不是 `Iterator`。编译器会自动在循环开头插入一次 `into_iter()`，再不断调用 `next()`。所以给自定义集合实现 `IntoIterator`，等于给它开了 `for` 循环的通行证。

一个类型可以有多份实现：标准库里 `Vec<T>` 同时实现了 `IntoIterator<Item = T>`（消耗所有权）、`IntoIterator<Item = &T>`（`&vec`）和 `IntoIterator<Item = &mut T>`（`&mut vec`），这正是 `for x in &v` 与 `for x in v` 行为不同的原因。

与相邻概念区别：`Iterator` 是「已经是迭代器、能产出元素」；`IntoIterator` 是「还不是迭代器，但能转成迭代器」。`&mut I`（`I: Iterator`）本身也实现了 `IntoIterator`，所以迭代器可以直接进 `for` 循环。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `into_iter(self)` | 消耗 `self`，返回 `Self::IntoIter` 迭代器。 |

## 提供的方法

本特质没有提供默认实现的方法，转换逻辑全部写在 `into_iter` 里。

## 关联类型

| 关联类型 | 说明 |
| --- | --- |
| `type Item;` | 迭代器产出的元素类型。 |
| `type IntoIter;` | 转换所得的迭代器类型，产出的 `Item` 须相同。 |

## 示例

### 三种借用形式

```rust
fn main() {
    let v = vec![1, 2, 3];

    // 按值：元素被移动出去
    let owned: Vec<i32> = v.clone().into_iter().collect();
    assert_eq!(owned, vec![1, 2, 3]);

    // 按引用：元素是 &i32
    let by_ref: Vec<&i32> = (&v).into_iter().collect();
    assert_eq!(by_ref, vec![&1, &2, &3]);

    // 不可变借用下，for 循环也拿到 &i32
    let mut sum = 0;
    for x in &v {
        sum += *x;
    }
    assert_eq!(sum, 6);

    // v 仍然可用
    assert_eq!(v.len(), 3);
}
```

### 给自定义集合实现 `IntoIterator`

```rust
use std::vec::IntoIter;

#[derive(Debug)]
struct Bag(Vec<i32>);

impl Bag {
    fn new() -> Bag {
        Bag(Vec::new())
    }

    fn add(&mut self, v: i32) {
        self.0.push(v);
    }
}

impl IntoIterator for Bag {
    type Item = i32;
    type IntoIter = IntoIter<i32>;

    fn into_iter(self) -> Self::IntoIter {
        self.0.into_iter()
    }
}

// 再给 &Bag 一份实现，让 for 循环也能借用它
impl<'a> IntoIterator for &'a Bag {
    type Item = &'a i32;
    type IntoIter = std::slice::Iter<'a, i32>;

    fn into_iter(self) -> Self::IntoIter {
        self.0.iter()
    }
}

fn main() {
    let mut bag = Bag::new();
    bag.add(1);
    bag.add(2);

    let mut total = 0;
    for x in &bag {
        total += *x;
    }
    assert_eq!(total, 3);

    for (i, x) in bag.into_iter().enumerate() {
        assert_eq!(i as i32 + 1, x);
    }
}
```

## 常见陷阱

1. **`for x in v` 会移动 `v`**：想保留集合就用 `&v` 或 `v.iter()`，否则循环结束后 `v` 已被消耗。
2. **`&mut I` 也实现了 `IntoIterator`**：`for x in &mut it` 不会复制迭代器，循环结束后 `it` 已被耗尽；要重复遍历请克隆迭代器或改用 `&v`。
3. **只实现 `IntoIterator` 不会自动得到 `iter()`**：`iter()` 是各集合自己的固有方法，不是 `IntoIterator` 的一部分。
4. **关联类型不能写错**：`IntoIter` 必须真的实现 `Iterator<Item = Item>`，否则 `next()` 调不通，编译器会直接报 trait 约束不满足。
5. **别在 `into_iter` 里做隐式深拷贝**：消耗式实现应转移所有权；需要借用语义时另写 `&T` 的实现。

## 相关

- [[iter|std::iter 模块]]：迭代器相关条目总览。
- [[iter.Iterator|Iterator]]：真正定义 `next` 的主特质。
- [[iter.FromIterator|FromIterator]]：反向的转换方向，`collect` 依赖它。
- [[iter.Extend|Extend]]：把迭代器内容追加进已有集合。
- [[18-迭代器|迭代器]]：学习笔记中的迭代器章节。
