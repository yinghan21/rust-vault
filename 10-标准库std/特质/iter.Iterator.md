---
title: "std::iter::Iterator"
type: std-条目
kind: 特质
module: iter
slug: iter.Iterator
stable: "1.0.0"
tags:
  - std/特质
  - std/类型
aliases:
  - Iterator
一句话: 迭代器的主特质，只要求实现 next，其余 60 个稳定方法都由默认实现提供。
---

# `Iterator`

> [!abstract] 一句话
> `Iterator` 是 Rust 迭代器体系的主特质：实现者只需提供 `next`，就能免费得到 `map`、`filter`、`collect`、`fold` 等 60 个稳定方法。

## 简介

`Iterator` 描述「能按顺序一个个产出元素」的东西。它只有一个**必须实现**的方法 `next`，其余 60 个稳定方法都有默认实现，因此自定义迭代器非常省事。所有 `for` 循环、`collect`、`sum`、`chain` 都建立在它之上。

它的方法分成两类：一类返回新的迭代器（适配器，如 `map`、`filter`、`take`），**惰性**求值，不消费就不干活；另一类返回单个结果（消费型，如 `collect`、`fold`、`count`），会消耗迭代器本身。

和相邻概念的区别：`Iterator` 是「能产出」，[[iter.IntoIterator|IntoIterator]] 是「能被转换成迭代器」（`for` 循环真正要求的是后者），[[iter.FromIterator|FromIterator]] 是「能从迭代器造出来」（`collect` 的目标）。

```rust
fn main() {
    // 数组的三重转换：容器 -> 迭代器 -> 结果
    let v = [1, 2, 3];
    let doubled: Vec<i32> = v.into_iter().map(|x| x * 2).collect();
    assert_eq!(doubled, vec![2, 4, 6]);
}
```

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `next(&mut self)` | 返回下一个元素，耗尽后返回 `None`。 |

> [!important] `size_hint` 建议一并实现
> `size_hint` 有默认实现（返回 `(0, None)`），但重写它能帮 `collect` 预分配、让 `chain` 之类的适配器给出更准的长度提示。

## 提供的方法

以下 60 个方法全部有默认实现，按用途分四组。

### 长度与位置

| 方法 | 说明 |
| --- | --- |
| `size_hint()` | 返回剩余长度的下界与可选上界。 |
| `count()` | 消耗迭代器，统计并返回迭代次数。 |
| `last()` | 消耗迭代器，返回最后一个元素。 |
| `nth(n)` | 返回第 `n` 个元素，跳过前面 `n` 个。 |
| `step_by(step)` | 返回每隔 `step` 个元素取一个的迭代器。 |

### 构造新迭代器（适配器）

| 方法 | 说明 |
| --- | --- |
| `chain(other)` | 依次串联两个迭代器。 |
| `zip(other)` | 把两个迭代器配对成元组迭代器。 |
| `map(f)` | 对每个元素应用闭包生成新迭代器。 |
| `enumerate()` | 为每个元素附上从 0 开始的索引。 |
| `filter(p)` | 只保留判断为 `true` 的元素。 |
| `filter_map(f)` | 同时过滤和映射，丢弃 `None`。 |
| `peekable()` | 返回可用 `peek` 预看下一个元素的迭代器。 |
| `skip(n)` | 跳过前 `n` 个元素。 |
| `take(n)` | 只取前 `n` 个元素。 |
| `skip_while(p)` | 跳过开头满足条件的元素后返回其余。 |
| `take_while(p)` | 只取开头满足条件的元素。 |
| `map_while(f)` | 边映射边取，遇到 `None` 即停止。 |
| `scan(state, f)` | 携带可变状态的 `map`，可提前终止。 |
| `flat_map(f)` | 映射并展平嵌套结果。 |
| `flatten()` | 直接展平元素中嵌套的迭代器。 |
| `fuse()` | 首次返回 `None` 后不再产出。 |
| `inspect(f)` | 逐项旁路观察元素后原样传下。 |
| `by_ref()` | 借用迭代器本身，便于部分消耗。 |
| `cycle()` | 无限重复整个迭代器。 |
| `rev()` | 反转迭代方向，需双端迭代器。 |
| `copied()` | 把 `&T` 元素复制成 `T`。 |
| `cloned()` | 把 `&T` 元素克隆成 `T`。 |

### 消费与聚集

| 方法 | 说明 |
| --- | --- |
| `collect()` | 把元素收集进实现了 `FromIterator` 的类型。 |
| `partition(p)` | 按条件把元素分进两个集合。 |
| `fold(init, f)` | 逐个累积元素得到单个结果。 |
| `try_fold(init, f)` | 带短路的 `fold`，出错立即返回。 |
| `reduce(f)` | 用首元素作初值累积，空则返回 `None`。 |
| `for_each(f)` | 对每个元素调用闭包。 |
| `try_for_each(f)` | 对每项调用可失败闭包，遇错停止。 |
| `sum()` | 求和所有元素。 |
| `product()` | 求积所有元素。 |
| `unzip()` | 把元素为元组的迭代器拆成两个集合。 |

### 查询与比较

| 方法 | 说明 |
| --- | --- |
| `all(p)` | 判断是否所有元素都满足条件。 |
| `any(p)` | 判断是否存在元素满足条件。 |
| `find(p)` | 返回第一个满足条件的元素。 |
| `find_map(f)` | 返回第一个映射得到 `Some` 的结果。 |
| `position(p)` | 返回第一个满足条件的元素下标。 |
| `rposition(p)` | 从右往左找，返回满足条件的下标。 |
| `max()` | 返回最大元素，空迭代器为 `None`。 |
| `min()` | 返回最小元素，空迭代器为 `None`。 |
| `max_by_key(f)` | 按键函数返回最大值对应元素。 |
| `max_by(cmp)` | 按自定义比较函数返回最大元素。 |
| `min_by_key(f)` | 按键函数返回最小值对应元素。 |
| `min_by(cmp)` | 按自定义比较函数返回最小元素。 |
| `cmp(other)` | 与其他迭代器按字典序比较。 |
| `partial_cmp(other)` | 按字典序返回偏序比较结果。 |
| `eq(other)` | 判断两迭代器元素是否完全相同。 |
| `ne(other)` | 判断两迭代器元素是否不同。 |
| `lt(other)` | 判断本迭代器字典序是否小于另一个。 |
| `le(other)` | 判断字典序是否小于或等于另一个。 |
| `gt(other)` | 判断字典序是否大于另一个。 |
| `ge(other)` | 判断字典序是否大于或等于另一个。 |
| `is_sorted()` | 判断元素是否已按升序排列。 |
| `is_sorted_by(cmp)` | 用比较函数判断是否已排序。 |
| `is_sorted_by_key(f)` | 用键函数判断是否已排序。 |

> [!tip] `step_by` 已在「长度与位置」表中列出
> 它同时是适配器，下面的速查表不再重复列举。

### 适配器速查表

适配器都是惰性的，返回一个包裹原迭代器的结构体；把返回值存进变量时不需要写类型。

| 适配器 | 说明 |
| --- | --- |
| `step_by(n)` | 返回 `StepBy<Self>`：按步长取样。 |
| `chain(u)` | 返回 `Chain<Self, U::IntoIter>`：首尾相连。 |
| `zip(u)` | 返回 `Zip<Self, U::IntoIter>`：两项配成元组。 |
| `map(f)` | 返回 `Map<Self, F>`：逐项变换。 |
| `filter(p)` | 返回 `Filter<Self, P>`：只留有谓词为真的项。 |
| `filter_map(f)` | 返回 `FilterMap<Self, F>`：变换并丢弃 `None`。 |
| `enumerate()` | 返回 `Enumerate<Self>`：附带下标。 |
| `peekable()` | 返回 `Peekable<Self>`：支持 `peek` 预看。 |
| `skip_while(p)` | 返回 `SkipWhile<Self, P>`：跳过开头区间。 |
| `take_while(p)` | 返回 `TakeWhile<Self, P>`：只留开头区间。 |
| `map_while(f)` | 返回 `MapWhile<Self, P>`：遇到 `None` 截止。 |
| `skip(n)` | 返回 `Skip<Self>`：丢弃前 `n` 项。 |
| `take(n)` | 返回 `Take<Self>`：保留前 `n` 项。 |
| `scan(st, f)` | 返回 `Scan<Self, St, F>`：带状态累积。 |
| `flat_map(f)` | 返回 `FlatMap<Self, U, F>`：变换后展平。 |
| `flatten()` | 返回 `Flatten<Self>`：直接展平一层。 |
| `fuse()` | 返回 `Fuse<Self>`：`None` 之后恒为 `None`。 |
| `inspect(f)` | 返回 `Inspect<Self, F>`：旁路观察。 |
| `rev()` | 返回 `Rev<Self>`：反向产出。 |
| `cycle()` | 返回 `Cycle<Self>`：无限循环。 |
| `copied()` | 返回 `Copied<Self>`：复制引用目标。 |
| `cloned()` | 返回 `Cloned<Self>`：克隆引用目标。 |
| `by_ref()` | 返回 `&mut Self`：临时借用迭代器。 |

## 关联类型

| 关联类型 | 说明 |
| --- | --- |
| `type Item;` | 迭代器产出的元素类型，必须由实现者指定。 |

## 示例

### 组合适配器处理数据

```rust
fn main() {
    let v = vec![1, 2, 3, 4, 5, 6];

    // 过滤偶数、乘 10、收集成新 Vec
    let evens: Vec<i32> = v.iter().copied().filter(|x| x % 2 == 0).map(|x| x * 10).collect();
    assert_eq!(evens, vec![20, 40, 60]);

    // 消费型方法：求和、找位置、判断
    assert_eq!(v.iter().sum::<i32>(), 21);
    assert_eq!(v.iter().position(|&x| x > 4), Some(4));
    assert!(v.iter().all(|&x| x > 0));

    // zip 配对，unzip 拆开
    let (names, lens): (Vec<&str>, Vec<usize>) = ["ab", "cde", "f"]
        .iter()
        .map(|s| (*s, s.len()))
        .unzip();
    assert_eq!(names, vec!["ab", "cde", "f"]);
    assert_eq!(lens, vec![2, 3, 1]);
}
```

### 自己实现一个迭代器

```rust
struct Countdown(u32);

impl Iterator for Countdown {
    type Item = u32;

    fn next(&mut self) -> Option<u32> {
        if self.0 == 0 {
            None
        } else {
            let v = self.0;
            self.0 -= 1;
            Some(v)
        }
    }

    // 剩余长度是可精确计算的，重写 size_hint 能让 collect 预分配
    fn size_hint(&self) -> (usize, Option<usize>) {
        let n = self.0 as usize;
        (n, Some(n))
    }
}

fn main() {
    assert_eq!(Countdown(3).size_hint(), (3, Some(3)));
    assert_eq!(Countdown(3).collect::<Vec<u32>>(), vec![3, 2, 1]);
    assert_eq!(Countdown(4).count(), 4);
    assert_eq!(Countdown(9).last(), Some(1));
}
```

## 常见陷阱

1. **适配器是惰性的**：`map`、`filter` 不调用 `next` 就什么也不做；必须用 `for_each`、`collect`、`sum` 等消费型方法收尾。
2. **消费型方法会拿走 `self`**：`count`、`last`、`collect` 之后再想用原迭代器会编译失败；需要提前 `clone`，或先用 `by_ref()` 借用。
3. **`filter` 之后长度不再精确**：`filter` 不实现 [[iter.ExactSizeIterator|ExactSizeIterator]]，`size_hint` 只给 `(0, Some(n))`，别靠它做内存分配。
4. **`zip` 以短的一侧为准**：两侧长度不等时，多余元素被静默丢弃，不会报错。
5. **排序类判断依赖 `PartialOrd`**：`is_sorted` 遇到 `NaN` 之类的偏序值，结果可能不符合直觉，需要稳定语义时改用自己的比较函数。

## 相关

- [[iter|std::iter 模块]]：迭代器相关的标准库条目与适配器。
- [[iter.IntoIterator|IntoIterator]]：`for` 循环真正依赖的特质。
- [[iter.FromIterator|FromIterator]]：`collect` 的目标特质。
- [[iter.DoubleEndedIterator|DoubleEndedIterator]]：支持从尾部取元素。
- [[18-迭代器|迭代器]]：学习笔记中的迭代器章节。
