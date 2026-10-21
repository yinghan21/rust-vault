---
title: "std::vec::Vec"
type: std-条目
kind: 结构体
module: vec
slug: vec.Vec
stable: "1.0.0"
tags:
  - std/类型
  - std/集合
aliases:
  - Vec
一句话: 连续、可增长的堆分配数组类型，是 Rust 中最常用的动态序列容器。
---

# `Vec<T>`

> [!abstract] 一句话
> `Vec<T>` 是**连续、可增长**的堆上数组：元素紧挨着排列，长度可以随时变化，扩容时会把元素搬到更大的缓冲区。

## 简介

`Vec<T>` 把「长度 `len`」和「容量 `capacity`」分开管理：`len` 是实际有多少个元素，`capacity` 是在**不重新分配**的前提下最多能放多少个。`push` 时如果 `len == capacity`，就会重新申请一块更大的内存（通常是翻倍），把旧元素搬过去，再释放旧内存——所以「预留容量」是提升性能最直接的手段。

它和相邻类型的分工是：

- `Vec<T>`：拥有元素、可变长，用 `&Vec<T>` 或 `&[T]` 借用；大多数「一组同类型数据」的场景都用它。
- [[primitive.slice|Type slice]]（`[T]`）：一段**已知长度**的视图，不拥有数据；`Vec<T>` 通过 `Deref` 得到 `[T]`，所以切片的所有方法都能直接在 `Vec` 上调用。
- [[collections.VecDeque|VecDeque]]：两端增删都是 O(1)，但元素不保证连续，不能直接当切片用。
- [[string.String|String]]：本质上是保证 UTF-8 合法的字节 `Vec`。

用下标 `v[i]` 访问越界会 **panic**；不确定时用 `get` / `get_mut` 拿到 `Option`。`Vec` 的元素在内存中连续，因此对缓存友好，也能零成本地传给需要切片的函数（`&v` 会自动解引用成 `&[T]`）。

```rust
fn main() {
    let mut v: Vec<i32> = Vec::new();
    v.push(1);
    v.push(2);
    assert_eq!(v.len(), 2);
    assert_eq!(v[0], 1);
    // 超出 len 但仍在 capacity 内不算合法元素
    assert!(v.capacity() >= 2);
}
```

## 常用方法

> [!tip] 表的边界
> 前四组是 `Vec<T>` 自身的固有方法；「切片视图」及之后的分组来自 `Deref<Target = [T]>`，在 `Vec` 上同样可以直接调用。签名以官方 rustdoc 为准，方法名后括号内为参数。

### 创建

| 方法 | 说明 |
| --- | --- |
| `new()` | 创建空的 `Vec`，不分配内存。 |
| `with_capacity(capacity)` | 创建空 `Vec` 并预先分配至少 `capacity` 容量。 |
| `from_raw_parts(ptr, length, capacity)` | 由裸指针、长度、容量直接构造，`unsafe`。 |
| `from_parts(ptr, length, capacity)` | 由 `NonNull` 指针、长度、容量直接构造，`unsafe`。 |
| `into_raw_parts()` | 拆解为 `(裸指针, 长度, 容量)` 三元组。 |
| `into_parts()` | 拆解为 `(NonNull 指针, 长度, 容量)` 三元组。 |

### 容量

| 方法 | 说明 |
| --- | --- |
| `capacity()` | 返回不重新分配即可容纳的元素个数。 |
| `reserve(additional)` | 预留至少 `additional` 个元素容量，可能多分配。 |
| `reserve_exact(additional)` | 预留恰好够用的容量，不做投机性多分配。 |
| `try_reserve(additional)` | 可失败的预留，失败返回 `TryReserveError`。 |
| `try_reserve_exact(additional)` | 可失败的最小预留，失败返回 `TryReserveError`。 |
| `shrink_to_fit()` | 把容量收缩到与长度相同。 |
| `shrink_to(min_capacity)` | 收缩容量，但不低于 `min_capacity`。 |
| `spare_capacity_mut()` | 以 `MaybeUninit` 切片返回剩余空闲容量。 |
| `set_len(new_len)` | 直接设置长度、不析构被截断元素，`unsafe`。 |
| `leak()` | 泄漏内存，返回 `&'a mut [T]` 且不释放缓冲区。 |

### 增删

| 方法 | 说明 |
| --- | --- |
| `push(value)` | 在末尾追加一个元素。 |
| `push_mut(value)` | 在末尾追加元素并返回其可变引用。 |
| `pop()` | 移除并返回最后一个元素，空时返回 `None`。 |
| `pop_if(predicate)` | 谓词为真时移除并返回末尾元素。 |
| `insert(index, element)` | 在 `index` 处插入元素，其后元素整体右移。 |
| `insert_mut(index, element)` | 在 `index` 处插入并返回新元素的可变引用。 |
| `remove(index)` | 移除并返回 `index` 处元素，其后元素左移。 |
| `swap_remove(index)` | 用末尾元素填坑后移除 `index`，不保序。 |
| `truncate(len)` | 保留前 `len` 个元素，其余丢弃并析构。 |
| `resize(new_len, value)` | 调整长度，新增位置克隆 `value`。 |
| `resize_with(new_len, f)` | 调整长度，新增位置由闭包生成。 |
| `extend_from_slice(other)` | 克隆切片全部元素并追加到末尾。 |
| `extend_from_within(src)` | 克隆自身某范围的元素并追加到末尾。 |
| `append(other)` | 把 `other` 全部元素移入 `self`，`other` 变空。 |
| `drain(range)` | 删除范围元素并返回其双端迭代器。 |
| `splice(range, replace_with)` | 用迭代器替换范围元素，返回被删元素迭代器。 |
| `extract_if(range, filter)` | 返回按谓词删除范围内元素的迭代器。 |
| `retain(f)` | 仅保留谓词为真的元素。 |
| `retain_mut(f)` | 同上，但向谓词传入可变引用。 |
| `dedup()` | 按 `PartialEq` 删除连续重复元素。 |
| `dedup_by(same_bucket)` | 用自定义判等函数删除连续重复元素。 |
| `dedup_by_key(key)` | 按键删除连续重复元素，保留第一个。 |
| `clear()` | 清空所有元素，保留容量。 |
| `split_off(at)` | 在 `at` 处拆分，返回后半部分作为新 `Vec`。 |

### 访问（`Vec` 自身）

| 方法 | 说明 |
| --- | --- |
| `len()` | 返回元素个数。 |
| `is_empty()` | 判断元素个数是否为 0。 |
| `as_slice()` | 返回覆盖整个向量的不可变切片。 |
| `as_mut_slice()` | 返回覆盖整个向量的可变切片。 |
| `as_ptr()` | 返回缓冲区裸指针，未分配时返回悬垂指针。 |
| `as_mut_ptr()` | 返回缓冲区可变裸指针。 |

### 切片视图（经 `Deref` 到 `[T]`）

| 方法 | 说明 |
| --- | --- |
| `len()` | 切片版：返回元素个数。 |
| `is_empty()` | 切片版：判断长度是否为 0。 |
| `as_ptr()` | 切片版：返回缓冲区裸指针。 |
| `as_mut_ptr()` | 切片版：返回缓冲区可变裸指针。 |
| `first()` | 返回第一个元素引用，空切片返回 `None`。 |
| `first_mut()` | 返回第一个元素的可变引用。 |
| `last()` | 返回最后一个元素引用，空切片返回 `None`。 |
| `last_mut()` | 返回最后一个元素的可变引用。 |
| `get(index)` | 按下标取元素或子切片，越界返回 `None`。 |
| `get_mut(index)` | `get` 的可变版本，越界返回 `None`。 |
| `get_unchecked(index)` | 不做越界检查地取元素引用，`unsafe`。 |
| `get_unchecked_mut(index)` | 不做越界检查取可变引用，`unsafe`。 |
| `as_ptr_range()` | 返回覆盖整个切片的两个裸指针区间。 |
| `as_mut_ptr_range()` | 返回覆盖整个切片的两可变裸指针区间。 |
| `as_array()` | 长度恰为 `N` 时返回底层数组引用。 |
| `as_mut_array()` | 长度恰为 `N` 时返回底层数组可变引用。 |
| `first_chunk()` | 返回前 `N` 个元素组成的数组引用。 |
| `first_chunk_mut()` | 返回前 `N` 个元素的可变数组引用。 |
| `last_chunk()` | 返回后 `N` 个元素组成的数组引用。 |
| `last_chunk_mut()` | 返回后 `N` 个元素的可变数组引用。 |
| `split_first()` | 返回首元素引用与其余部分。 |
| `split_first_mut()` | 返回首元素可变引用与其余可变部分。 |
| `split_last()` | 返回末元素引用与其余部分。 |
| `split_last_mut()` | 返回末元素可变引用与其余可变部分。 |
| `split_first_chunk()` | 返回前 `N` 元素数组引用与剩余切片。 |
| `split_first_chunk_mut()` | 返回前 `N` 元素可变数组与剩余可变切片。 |
| `split_last_chunk()` | 返回剩余切片与末尾 `N` 元素数组引用。 |
| `split_last_chunk_mut()` | 返回剩余可变切片与末尾 `N` 元素可变数组。 |
| `split_at(mid)` | 在 `mid` 处把切片切成两个 `&[T]`。 |
| `split_at_mut(mid)` | 在 `mid` 处切成两个 `&mut [T]`。 |
| `split_at_unchecked(mid)` | 不检查 `mid` 越界地切分，`unsafe`。 |
| `split_at_mut_unchecked(mid)` | 不检查越界的可变切分，`unsafe`。 |
| `split_at_checked(mid)` | 切分，`mid` 超过长度时返回 `None`。 |
| `split_at_mut_checked(mid)` | 可变切分，`mid` 超过长度时返回 `None`。 |
| `get_disjoint_mut(indices)` | 一次取多个互不重叠下标处的可变引用。 |
| `get_disjoint_unchecked_mut(indices)` | 不检查越界地取多个可变引用，`unsafe`。 |
| `split_off(range)` | 切片版：移除范围子切片并返回其引用。 |
| `split_off_mut(range)` | 切片版：移除范围子切片并返回可变引用。 |
| `split_off_first()` | 从 `&mut &[T]` 头部摘下一个元素引用。 |
| `split_off_first_mut()` | 从 `&mut &mut [T]` 头部摘下可变元素引用。 |
| `split_off_last()` | 从 `&mut &[T]` 尾部摘下一个元素引用。 |
| `split_off_last_mut()` | 从 `&mut &mut [T]` 尾部摘下可变元素引用。 |
| `element_offset(element)` | 返回元素引用所指向的下标。 |
| `subslice_range(subslice)` | 返回子切片对应的下标区间。 |

### 迭代与分块

| 方法 | 说明 |
| --- | --- |
| `iter()` | 返回遍历切片的不可变迭代器。 |
| `iter_mut()` | 返回可修改每个元素的迭代器。 |
| `windows(size)` | 返回所有长度为 `size` 的重叠窗口。 |
| `array_windows()` | 返回 `N` 个元素的重叠窗口，产出数组引用。 |
| `chunks(chunk_size)` | 从头开始按 `chunk_size` 切块迭代。 |
| `chunks_mut(chunk_size)` | 可变的从头切块迭代。 |
| `chunks_exact(chunk_size)` | 从头切等长块，丢弃末尾不足一块。 |
| `chunks_exact_mut(chunk_size)` | 可变的等长块切分。 |
| `rchunks(chunk_size)` | 从尾部开始按 `chunk_size` 切块迭代。 |
| `rchunks_mut(chunk_size)` | 可变的从尾切块迭代。 |
| `rchunks_exact(chunk_size)` | 从尾切等长块，丢弃开头不足一块。 |
| `rchunks_exact_mut(chunk_size)` | 可变的从尾等长块切分。 |
| `as_chunks()` | 切成 `[T; N]` 数组切片与剩余尾巴。 |
| `as_chunks_mut()` | 可变的 `[T; N]` 切分，返回剩余尾巴。 |
| `as_rchunks()` | 从尾切成 `[T; N]` 数组切片与剩余头部。 |
| `as_rchunks_mut()` | 可变的从尾 `[T; N]` 切分。 |
| `as_chunks_unchecked()` | 假定没有剩余地切成数组切片，`unsafe`。 |
| `as_chunks_unchecked_mut()` | 同上且返回可变引用，`unsafe`。 |
| `chunk_by(pred)` | 按相邻元素谓词生成不重叠的连续块。 |
| `chunk_by_mut(pred)` | 同上，产出可变块。 |
| `split(pred)` | 按匹配元素切分，匹配元素不保留。 |
| `split_mut(pred)` | `split` 的可变版本。 |
| `split_inclusive(pred)` | 按匹配元素切分，匹配元素留在前段末尾。 |
| `split_inclusive_mut(pred)` | `split_inclusive` 的可变版本。 |
| `rsplit(pred)` | 从尾向头按匹配元素切分。 |
| `rsplit_mut(pred)` | `rsplit` 的可变版本。 |
| `splitn(n, pred)` | 同 `split`，但最多产出 `n` 段。 |
| `splitn_mut(n, pred)` | `splitn` 的可变版本。 |
| `rsplitn(n, pred)` | 从尾切分，最多产出 `n` 段。 |
| `rsplitn_mut(n, pred)` | `rsplitn` 的可变版本。 |

### 查找与排序

| 方法 | 说明 |
| --- | --- |
| `contains(x)` | 判断切片是否含有等于 `x` 的元素。 |
| `starts_with(needle)` | 判断 `needle` 是否为切片的前缀。 |
| `ends_with(needle)` | 判断 `needle` 是否为切片的后缀。 |
| `strip_prefix(prefix)` | 去掉前缀并返回剩余子切片。 |
| `strip_suffix(suffix)` | 去掉后缀并返回剩余子切片。 |
| `strip_circumfix(prefix, suffix)` | 同时去掉前缀与后缀并返回中间子切片。 |
| `binary_search(x)` | 在有序切片中二分查找，返回命中或插入点。 |
| `binary_search_by(f)` | 用比较函数做二分查找。 |
| `binary_search_by_key(b, f)` | 用键提取函数做二分查找。 |
| `is_sorted()` | 判断元素是否按升序排列。 |
| `is_sorted_by(compare)` | 用比较函数判断是否有序。 |
| `is_sorted_by_key(f)` | 用键提取函数判断是否有序。 |
| `partition_point(pred)` | 返回第一个谓词为假的元素下标。 |
| `sort()` | 升序稳定排序，相等元素保持原有顺序。 |
| `sort_by(compare)` | 用比较函数做稳定排序。 |
| `sort_by_key(f)` | 用键提取函数做稳定排序。 |
| `sort_by_cached_key(f)` | 键只计算一次的稳定排序。 |
| `sort_unstable()` | 升序不稳定排序，不保证相等元素顺序。 |
| `sort_unstable_by(compare)` | 用比较函数做不稳定排序。 |
| `sort_unstable_by_key(f)` | 用键提取函数做不稳定排序。 |
| `select_nth_unstable(index)` | 重排使 `index` 处元素就位，两侧不排序。 |
| `select_nth_unstable_by(index, compare)` | 用比较函数做第 n 元素选择。 |
| `select_nth_unstable_by_key(index, f)` | 用键提取函数做第 n 元素选择。 |
| `rotate_left(mid)` | 原地左旋，前 `mid` 个元素移到末尾。 |
| `rotate_right(k)` | 原地右旋，后 `k` 个元素移到开头。 |

### 转换与整段复制

| 方法 | 说明 |
| --- | --- |
| `into_boxed_slice()` | 转为 `Box<[T]>`，多余容量被丢弃。 |
| `into_flattened()` | 把 `Vec<[T; N]>` 展平成 `Vec<T>`。 |
| `to_vec()` | 克隆整个切片生成新的 `Vec`。 |
| `repeat(n)` | 复制切片 `n` 次生成新 `Vec`。 |
| `concat()` | 把切片元素拼成一个值，如拼接字符串。 |
| `join(sep)` | 用分隔符把切片元素拼成一个值。 |
| `swap(a, b)` | 交换下标 `a` 与 `b` 处的元素。 |
| `reverse()` | 原地反转元素顺序。 |
| `fill(value)` | 用克隆的 `value` 填满整个切片。 |
| `fill_with(f)` | 用闭包依次产生的值填满整个切片。 |
| `clone_from_slice(src)` | 用 `src` 逐元素克隆覆盖自身。 |
| `copy_from_slice(src)` | 用 `src` 做 memcpy 覆盖自身。 |
| `copy_within(src, dest)` | 把自身某范围的元素 memmove 到另一位置。 |
| `swap_with_slice(other)` | 与另一等长切片整体交换元素。 |
| `align_to()` | 按对齐要求把切片重解释为 `&[U]`，`unsafe`。 |
| `align_to_mut()` | 同上，返回可变引用，`unsafe`。 |

## 示例

基础增删查改：

```rust
fn main() {
    let mut v: Vec<i32> = Vec::with_capacity(4);
    assert_eq!(v.len(), 0);
    assert!(v.is_empty());

    v.push(3);
    v.push(1);
    v.extend([2, 4]);
    v.insert(0, 0);
    assert_eq!(v, [0, 3, 1, 2, 4]);
    assert!(v.contains(&3));

    v.retain(|x| *x % 2 == 0);
    assert_eq!(v, [0, 2, 4]);

    v.sort();
    assert_eq!(v, [0, 2, 4]);
    assert_eq!(v.get(10), None); // 越界用 get 不会 panic

    let removed = v.swap_remove(0);
    assert_eq!(removed, 0);
    assert_eq!(v, [4, 2]);
}
```

借出切片、按切片 API 处理并回收所有权：

```rust
// 参数是切片，传 &Vec<i32> 会自动解引用
fn sum_all(data: &[i32]) -> i32 {
    data.iter().sum()
}

fn main() {
    let mut v = vec![5, 1, 5, 3, 1];
    assert_eq!(sum_all(&v), 15);

    // sort_unstable 与 dedup 都是 Vec 的方法
    v.sort_unstable();
    v.dedup();
    assert_eq!(v, [1, 3, 5]);

    // 下标加范围得到 &mut [i32]，就地反转后半段
    v[1..].reverse();
    assert_eq!(v, [1, 5, 3]);

    // drain 拿走一段元素，向量本身保留
    let taken: Vec<i32> = v.drain(1..).collect();
    assert_eq!(taken, [5, 3]);
    assert_eq!(v, [1]);

    // 只读借用期间不能修改向量
    let first = v.first().copied();
    assert_eq!(first, Some(1));

    // into_boxed_slice 丢弃多余容量
    let boxed = v.into_boxed_slice();
    assert_eq!(&*boxed, &[1]);
}
```

## 常见陷阱

1. **`len` 与 `capacity` 混淆**：`with_capacity(n)` 后 `len()` 仍是 0，往里写只能通过 `push`，否则 `v[0]` 直接 panic。
2. **下标越界 panic**：`v[i]` 会做边界检查并可能 panic；来自外部的下标应改用 `get` / `get_mut` 并处理 `None`。
3. **循环 `push` 不预留容量**：反复扩容会带来多次搬移与分配，已知规模时先 `reserve` / `with_capacity`。
4. **`swap_remove` 不保序**：它把最后一个元素挪到空缺处，需要保持顺序时用 `remove`（代价是 O(n) 搬移）。
5. **`drain` 必须被消费**：`Drain` 是迭代器，若不迭代、不 `collect` 也不 `drop`，元素不会被真正移除，可先 `drop(v.drain(..))`。

## 相关

- [[vec|std::vec 模块]]：本条目所属模块，含 `vec!` 宏与相关类型。
- [[primitive.slice|Type slice]]：`Vec` 解引用得到的切片类型，方法表后四组都来自它。
- [[macro.vec|vec! 宏]]：用字面量快速创建 `Vec`。
- [[collections.VecDeque|VecDeque]]：需要两端高效增删时的替代方案。
- [[12-集合类型|集合类型]]：`Vec`、`HashMap`、`VecDeque` 的选型对比。
