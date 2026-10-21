---
title: "std::slice"
type: std-模块
module: slice
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - slice 模块
  - 切片模块
一句话: 原始类型 [T] 的配套模块：切片的借用语义、切片专属方法，以及分块/滑窗等迭代器。
---

# std::slice

> [!abstract] 一句话
> `std::slice` 是原始类型 [[primitive.slice|slice]]（写作 `[T]`）的配套模块：这里放切片产生的一次性迭代器和几个构造函数，真正的切片操作挂在 `[T]` 自己的方法上。

## 模块简介

切片 `[T]` 是「**一段连续存放、长度已知的同类型元素**」，但它是一个**动态大小类型**（DST）：长度在编译期不确定，所以永远不能按值存在，只能以 `&[T]`（共享借用）或 `&mut [T]` 的形式出现。这个引用是胖指针——一个地址加一个长度，共两个机器字——所以传切片参数只复制这两个字，元素本身一个都不动，是 Rust 里最标准的零拷贝参数类型。`Vec<T>`、`[T; N]`、`String` 的内容都能借出切片：`&vec[..]`、`&arr[..]`、`s.as_bytes()`。

切片的绝大多数能力由 `[T]` 上的固有方法提供，比如 `len`、`is_empty`、`first`、`get`、`iter`、`sort`、`binary_search`、`contains`、`reverse`、`fill`、`rotate_left`。索引 `s[i]` 会做边界检查，越界直接 panic；不想 panic 就用 `get(i)`，返回 `Option<&T>`。子切片 `&s[1..3]` 同样只借用一个区间，不复制元素，这也是「把一段数据交给函数处理」的首选写法。

这个模块自己提供两类东西。第一类是**迭代器类型**：`Iter`、`IterMut`、`Windows`、`Chunks`、`ChunksMut`、`ChunksExact`、`Split`、`SplitN`、`RSplit` 等，它们通常只由某个方法创建（`iter()` 产出 `Iter`，`chunks(3)` 产出 `Chunks`），一般不需要手写类型名。第二类是**构造函数**：`slice::from_ref` / `from_mut` 把单值引用变成长度为 1 的切片，`slice::from_raw_parts` 从裸指针加长度重建切片（`unsafe`，写底层代码或 FFI 时才用）。

什么时候想到切片：函数只想读一段数据、不想接管所有权、也不想限定调用者用数组还是 `Vec` 时，参数写 `&[T]`；需要修改元素时写 `&mut [T]`。它和 [[str|std::str]] 的关系很紧密：`&str` 就是「保证是合法 UTF-8 的 `&[u8]`」，而 `s.as_bytes()` 得到的正是字节切片。

## 快速上手

```rust
fn sum(xs: &[i32]) -> i32 {
    xs.iter().sum()
}

fn main() {
    let v = vec![1, 2, 3, 4, 5, 6];

    // Vec 和数组都会自动退化为切片，函数只借用、不接管所有权
    assert_eq!(sum(&v), 21);
    assert_eq!(sum(&[1, 2, 3]), 6);

    // 切片是借用视图：子切片不复制元素
    let tail = &v[3..];
    assert_eq!(tail, &[4, 5, 6]);
    assert_eq!(tail.len(), 3);

    // 越界索引会 panic，get 则返回 Option
    assert_eq!(v.get(99), None);
    assert_eq!(v.get(0), Some(&1));

    // 分块：每 2 个一组
    let chunks: Vec<&[i32]> = v.chunks(2).collect();
    assert_eq!(chunks, vec![&[1, 2][..], &[3, 4][..], &[5, 6][..]]);

    // 滑窗：每次取连续 3 个，窗口之间有重叠
    let mut windows = v.windows(3);
    assert_eq!(windows.next(), Some(&[1, 2, 3][..]));
    assert_eq!(windows.next(), Some(&[2, 3, 4][..]));

    // 按谓词切分：元素是 3 的倍数处断开
    let parts: Vec<&[i32]> = v.split(|&x| x % 3 == 0).collect();
    assert_eq!(parts, vec![&[1, 2][..], &[4, 5][..], &[][..]]);

    // from_ref：把单个值的引用当作长度为 1 的切片，零拷贝
    let x = 9i32;
    let one: &[i32] = std::slice::from_ref(&x);
    assert_eq!(one, &[9]);

    // 可变切片：原地修改前两个元素
    let mut nums = [1, 2, 3, 4];
    for n in &mut nums[..2] {
        *n *= 10;
    }
    assert_eq!(nums, [10, 20, 3, 4]);

    // sort / reverse 这类方法直接作用在切片上
    let mut w = [3, 1, 2];
    w.sort();
    w.reverse();
    assert_eq!(w, [3, 2, 1]);

    println!("全部通过");
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[primitive.slice\|slice]] | 原始类型 `[T]`，切片本身的语义与方法页。 |
| `slice::from_ref` | 把 `&T` 转成长度为 1 的 `&[T]`，零拷贝。 |
| `slice::from_mut` | 把 `&mut T` 转成长度为 1 的 `&mut [T]`。 |
| `slice::from_raw_parts` | 由裸指针 + 长度构造 `&[T]`（`unsafe`）。 |
| `slice::from_raw_parts_mut` | 同上，返回 `&mut [T]`（`unsafe`）。 |
| `slice::Iter` | `iter()` 的返回类型，共享借用迭代器。 |
| `slice::IterMut` | `iter_mut()` 的返回类型，可变借用迭代器。 |
| `slice::Windows` | `windows(n)` 的返回类型，重叠滑窗迭代。 |
| `slice::Chunks` | `chunks(n)` 的返回类型，不重叠分块迭代。 |
| `slice::ChunksMut` | `chunks_mut(n)` 的返回类型，可修改分块。 |
| `slice::ChunksExact` | `chunks_exact(n)` 的返回类型，丢弃末尾不足一块。 |
| `slice::Split` | `split(pred)` 的返回类型，按谓词切分。 |
| `slice::SplitN` | `splitn(n, pred)` 的返回类型，限制切分次数。 |
| `slice::EscapeAscii` | `escape_ascii()` 的返回类型，转义 ASCII 字节。 |

## 注意事项

> [!warning] 切片不是容器，不能自己增长
> `&[T]` 只是借用的一段内存，没有容量、不能 `push`。要动态增删元素，用 [[vec|std::vec]] 的 `Vec<T>`：先 `push` 得到足够空间，再 `&mut v[..]` 借出切片交给函数。反过来，函数参数写 `&[T]` 比 `&Vec<T>` 更通用——数组、`Vec`、切片都能传进去。

> [!danger] 索引越界是 panic，不是返回错误
> `s[i]`、`&s[a..b]` 会做边界检查，越界（或 `a > b`）直接 panic。只在能证明安全的地方用索引，其余场景优先 `get`、`get_mut`、`first`、`split_at_checked` 这类返回 `Option` 的方法。切片范围还必须落在合法边界上，`&s[..]` 对 `str` 更是要求 UTF-8 字符边界。

> [!tip] 切片的运行时成本
> 切片索引有边界检查，但编译器常在循环里消除它；`windows` / `chunks` / `split` 都是惰性迭代器，`collect` 成 `Vec<&[T]>` 只复制「指针 + 长度」，不复制元素。需要原地改元素时传 `&mut [T]`，比返回新 `Vec` 省一次分配。

## 相关

- [[primitive.slice|slice]]：`[T]` 的全部方法（`len`、`get`、`sort`、`split_at` 等）。
- [[vec|std::vec]]：`Vec<T>`，可增长的连续容器，切片的主要来源。
- [[array|std::array]]：定长数组 `[T; N]` 与数组间的转换函数。
- [[str|std::str]]：`&str` 是合法的字节切片，字符串版的分割/切块。
- [[18-迭代器|迭代器]]：`windows`、`chunks`、`split` 这些迭代器怎么用。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 37 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`ArrayWindows`](https://doc.rust-lang.org/std/slice/struct.ArrayWindows.html)
- [`ChunkBy`](https://doc.rust-lang.org/std/slice/struct.ChunkBy.html)
- [`ChunkByMut`](https://doc.rust-lang.org/std/slice/struct.ChunkByMut.html)
- [`Chunks`](https://doc.rust-lang.org/std/slice/struct.Chunks.html)
- [`ChunksExact`](https://doc.rust-lang.org/std/slice/struct.ChunksExact.html)
- [`ChunksExactMut`](https://doc.rust-lang.org/std/slice/struct.ChunksExactMut.html)
- [`ChunksMut`](https://doc.rust-lang.org/std/slice/struct.ChunksMut.html)
- [`EscapeAscii`](https://doc.rust-lang.org/std/slice/struct.EscapeAscii.html)
- [`Iter`](https://doc.rust-lang.org/std/slice/struct.Iter.html)
- [`IterMut`](https://doc.rust-lang.org/std/slice/struct.IterMut.html)
- [`RChunks`](https://doc.rust-lang.org/std/slice/struct.RChunks.html)
- [`RChunksExact`](https://doc.rust-lang.org/std/slice/struct.RChunksExact.html)
- [`RChunksExactMut`](https://doc.rust-lang.org/std/slice/struct.RChunksExactMut.html)
- [`RChunksMut`](https://doc.rust-lang.org/std/slice/struct.RChunksMut.html)
- [`RSplit`](https://doc.rust-lang.org/std/slice/struct.RSplit.html)
- [`RSplitMut`](https://doc.rust-lang.org/std/slice/struct.RSplitMut.html)
- [`RSplitN`](https://doc.rust-lang.org/std/slice/struct.RSplitN.html)
- [`RSplitNMut`](https://doc.rust-lang.org/std/slice/struct.RSplitNMut.html)
- [`Split`](https://doc.rust-lang.org/std/slice/struct.Split.html)
- [`SplitInclusive`](https://doc.rust-lang.org/std/slice/struct.SplitInclusive.html)
- [`SplitInclusiveMut`](https://doc.rust-lang.org/std/slice/struct.SplitInclusiveMut.html)
- [`SplitMut`](https://doc.rust-lang.org/std/slice/struct.SplitMut.html)
- [`SplitN`](https://doc.rust-lang.org/std/slice/struct.SplitN.html)
- [`SplitNMut`](https://doc.rust-lang.org/std/slice/struct.SplitNMut.html)
- [`Windows`](https://doc.rust-lang.org/std/slice/struct.Windows.html)

### 枚举

- [`GetDisjointMutError`](https://doc.rust-lang.org/std/slice/enum.GetDisjointMutError.html)

### 特质

- [`SliceIndex`](https://doc.rust-lang.org/std/slice/trait.SliceIndex.html)
- [`Concat`](https://doc.rust-lang.org/std/slice/trait.Concat.html)
- [`Join`](https://doc.rust-lang.org/std/slice/trait.Join.html)

### 函数

- [`from_mut`](https://doc.rust-lang.org/std/slice/fn.from_mut.html)
- [`from_raw_parts`](https://doc.rust-lang.org/std/slice/fn.from_raw_parts.html)
- [`from_raw_parts_mut`](https://doc.rust-lang.org/std/slice/fn.from_raw_parts_mut.html)
- [`from_ref`](https://doc.rust-lang.org/std/slice/fn.from_ref.html)
- [`from_mut_ptr_range`](https://doc.rust-lang.org/std/slice/fn.from_mut_ptr_range.html)
- [`from_ptr_range`](https://doc.rust-lang.org/std/slice/fn.from_ptr_range.html)
- [`range`](https://doc.rust-lang.org/std/slice/fn.range.html)
- [`try_range`](https://doc.rust-lang.org/std/slice/fn.try_range.html)

<!-- END AUTO ITEMS -->
