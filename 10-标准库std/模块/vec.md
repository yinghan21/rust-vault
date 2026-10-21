---
title: "std::vec"
type: std-模块
module: vec
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - vec
一句话: "可增长的堆分配数组 Vec<T>，以及 vec! 宏和它的几个专用迭代器。"
---

# std::vec

> [!abstract] 一句话
> `std::vec` 是 `Vec<T>` 的家：堆上连续的、可增长的数组，外加 `vec!` 宏和配对的迭代器类型。

## 模块简介

`std::vec` 提供 `Vec<T>` —— 堆分配的**连续可增长数组**。按下标随机访问是 O(1)，尾部 `push` 均摊 O(1)，尾部 `pop` O(1)。它还保证单次分配不会超过 `isize::MAX` 字节，所以长度永远能安全地放进 `usize`。

模块导出的东西分三类：主角 [[vec.Vec|Vec]]；它的几个专用迭代器 `vec::IntoIter`、`vec::Drain`、`vec::Splice`、`vec::ExtractIf`（分别由 `into_iter` / `drain` / `splice` / `extract_if` 产生，日常几乎不需要手写这些类型名）；以及构造宏 [[macro.vec|vec!]]。`vec!` 在 `std::vec` 里定义，再通过 `#[macro_export]` 提到 crate 根，所以直接写 `vec![1, 2, 3]` 或 `vec![0u8; 16]` 就行，不必 `use std::vec`。

与相邻结构的分工：`[T; N]` 是栈上的定长数组，`&[T]` 是借用视图，只有 `Vec<T>` 拥有数据并且能长能缩。函数参数尽量收 `&[T]`（`&Vec<T>` 会自动解引用过去），返回值才用 `Vec<T>`。需要两端都能高效增删时换 [[collections.VecDeque|VecDeque]]：`Vec` 只在尾部便宜，`insert(0, x)` 和 `remove(0)` 都要搬动整个数组。

内部模型是「指针 + 长度 + 容量」三件套：`len` 是已初始化的元素个数，`capacity` 是不重新分配的前提下还能放多少。容量涨上去不会自动还回来，要收回得显式 `shrink_to_fit`。

## 快速上手

```rust
fn main() {
    // vec! 宏：最常用的构造方式
    let mut v = vec![1, 2, 3];
    assert_eq!(v.len(), 3);
    assert!(v.capacity() >= v.len());

    v[0] = 10;
    v.push(4);
    assert_eq!(v.pop(), Some(4));
    assert_eq!(v.get(99), None); // get 越界返回 None；v[99] 会 panic

    // 借用迭代，把每个元素翻倍后收集成新的 Vec
    let doubled: Vec<i32> = v.iter().map(|x| x * 2).collect();
    assert_eq!(doubled, vec![20, 4, 6]);

    // drain 取走区间，原 Vec 只留下前半段
    let mut tail: Vec<i32> = v.drain(1..).collect();
    tail.extend_from_slice(&[7, 8]);
    assert_eq!(v, vec![10]);
    assert_eq!(tail, vec![2, 3, 7, 8]);

    // 预分配容量，避免反复扩容
    let mut buf: Vec<u8> = Vec::with_capacity(16);
    buf.extend_from_slice(b"hello");
    assert_eq!(String::from_utf8(buf).unwrap(), "hello");
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[vec.Vec|Vec]] | 堆分配、可增长的连续数组，本模块的主角。 |
| [[macro.vec|vec!]] | 按列表或「初值; 个数」构造 `Vec` 的宏。 |
| `Vec::new` / `Vec::with_capacity` | 建空向量 / 预分配容量以减少扩容。 |
| `Vec::push` / `Vec::pop` | 尾部入栈 / 出栈，均摊 O(1)。 |
| `Vec::insert` / `Vec::remove` | 在指定位置插入 / 删除，O(n)。 |
| `Vec::get` / `Vec::get_mut` | 按下标取引用，越界返回 `None`。 |
| `Vec::len` / `is_empty` / `capacity` | 长度 / 是否为空 / 当前容量。 |
| `Vec::iter` / `iter_mut` | 借用迭代元素，不消耗向量。 |
| `Vec::into_iter` | 消耗向量，产出 `vec::IntoIter`。 |
| `Vec::drain` | 取出区间元素，返回 `vec::Drain`。 |
| `Vec::extend_from_slice` | 在尾部追加一个切片。 |
| `Vec::retain` | 只保留满足条件的元素，原地压缩。 |
| `Vec::sort` / `dedup` | 排序 / 去掉相邻重复元素。 |
| `vec::ExtractIf` | 用闭包决定元素去留的迭代器。 |

## 注意事项

> [!danger] 下标越界会 panic
> `v[i]` 越界直接 panic，带边界来源的外部数据请用 `get` / `first` / `last`。空向量上 `pop()` 返回 `None`，但 `remove(0)`、`v[0]`、`last().unwrap()` 都会炸。

> [!warning] 扩容与容量
> 持着 `&v[0]` 时再 `v.push(1)` 编译不通过 —— 借用检查器已经挡住了扩容后的悬垂引用，你只需要操心性能：知道规模时用 `Vec::with_capacity` 预分配，避免多次搬移；`capacity` 只增不减，长期存活的大向量记得 `shrink_to_fit`。

> [!tip] 选型速查
> 只在尾部增删、按下标访问 → `Vec`；两端都要 push/pop → [[collections.VecDeque|VecDeque]]；按 key 查找 → `HashMap`；要求有序 → `BTreeMap`；长度编译期已知 → 数组。另外 `Vec::remove(0)` 是 O(n)，顺序不重要时 `swap_remove` 是 O(1)。

## 相关

- [[collections|std::collections 模块]]：`VecDeque`、`HashMap` 等其它容器。
- [[collections.VecDeque|VecDeque]]：两端都要高效增删时的替代品。
- [[slice|std::slice 模块]]：`&[T]` 上的排序、查找、切分方法。
- [[12-集合类型|集合类型]]：各容器的对比与选择。
- [[18-迭代器|迭代器]]：`iter` / `into_iter` 之后接的适配器链。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 6 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`Drain`](https://doc.rust-lang.org/std/vec/struct.Drain.html)
- [`ExtractIf`](https://doc.rust-lang.org/std/vec/struct.ExtractIf.html)
- [`IntoIter`](https://doc.rust-lang.org/std/vec/struct.IntoIter.html)
- [`Splice`](https://doc.rust-lang.org/std/vec/struct.Splice.html)
- [[vec.Vec|`Vec`]]
- [`PeekMut`](https://doc.rust-lang.org/std/vec/struct.PeekMut.html)

<!-- END AUTO ITEMS -->
