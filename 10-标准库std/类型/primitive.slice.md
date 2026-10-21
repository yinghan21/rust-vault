---
title: "slice（[T]）"
type: std-条目
kind: 原始类型
module: primitive
slug: primitive.slice
stable: "1.0.0"
tags:
  - std/类型
aliases:
  - slice
  - 切片
一句话: "指向一段连续同类型元素的视图，由指针与长度两字组成，本身不拥有数据、不能按值创建。"
---

# [T]

> [!abstract] 一句话
> `[T]` 是一段**已知长度**的连续内存视图：内部是「指针 + 长度」的胖指针，可以指向数组、`Vec` 的缓冲区或任意一段同类型元素；它不拥有数据，也不能按值创建。

## 简介

`[T]` 是**动态大小类型**（unsized），编译器在编译期不知道它有多长，所以 `[T]` 不能直接作为变量类型、不能放到栈上、也不能按值创建——你只会见到 `&[T]`、`&mut [T]`、`Box<[T]>`、`Arc<[T]>` 这些形式。一个 `&[T]` 占**两个机器字**：一个指向首元素的指针，一个元素个数 `len`（按元素计数，不是字节数），这就是「胖指针」。`&str` 是同样的结构，所以字符串切片的规则可以类比过来。

它和相邻类型的分工是：

- `[T; N]`：长度写进类型里的**定长数组**，元素直接内联在所属对象里；`&arr` 会**自动强制转换**成 `&[T]`，函数参数写 `&[T]` 就能同时接收数组和 `Vec`。
- [[vec.Vec|Vec]]：拥有堆上缓冲区的**可增长序列**，通过 `Deref` 借出 `&[T]`，所以切片的方法可以直接在 `Vec` 上调用。
- [[primitive.str|Type str]]：保证 UTF-8 合法的字节切片，`&str` 与 `&[u8]` 的边界规则不同，见「常见陷阱」。
- [[primitive.array|Type array]]：`[T; N]` 的原始类型页，讲定长数组的构造与转换。

切片本身**不带容量**、不负责释放内存，因此复制一个 `&[T]` 只是复制指针与长度，开销极小；这也是「参数尽量写 `&[T]` 而不是 `&Vec<T>`」的原因——前者不绑定具体容器，调用方传数组、`Vec` 还是别的缓冲区都行。

```rust
fn main() {
    let arr = [1, 2, 3, 4];
    let v = vec![5, 6, 7];

    // 数组与 Vec 都能借出切片
    let a: &[i32] = &arr;
    let b: &[i32] = &v;
    assert_eq!(a.len(), 4);
    assert_eq!(b.len(), 3);

    // 一个 &[i32] 就是「指针 + 长度」
    let ptr_size = std::mem::size_of::<&[i32]>();
    assert_eq!(ptr_size, 2 * std::mem::size_of::<usize>());
}
```

## 常用方法

> [!tip] 表的边界
> 下表覆盖本页 135 个稳定方法，括号内为参数；标 `unsafe` 的必须在 `unsafe` 块中调用。`new_uninit_slice` 这类关联函数通过 `[T]::new_uninit_slice(n)` 调用，其余都是方法。

### 长度与首尾

| 方法 | 说明 |
| --- | --- |
| `len()` | 返回切片中的元素个数。 |
| `is_empty()` | 判断切片长度是否为 0。 |
| `first()` | 返回首元素引用，空切片返回 `None`。 |
| `first_mut()` | 返回首元素的可变引用。 |
| `last()` | 返回末元素引用，空切片返回 `None`。 |
| `last_mut()` | 返回末元素的可变引用。 |
| `split_first()` | 返回首元素与其后全部元素，空时 `None`。 |
| `split_first_mut()` | 返回首元素可变引用与其余可变切片。 |
| `split_last()` | 返回末元素与其前全部元素，空时 `None`。 |
| `split_last_mut()` | 返回末元素可变引用与其余可变切片。 |
| `first_chunk()` | 返回前 `N` 个元素组成的数组引用。 |
| `first_chunk_mut()` | 返回前 `N` 个元素的可变数组引用。 |
| `last_chunk()` | 返回后 `N` 个元素组成的数组引用。 |
| `last_chunk_mut()` | 返回后 `N` 个元素的可变数组引用。 |
| `split_first_chunk()` | 返回前 `N` 元素数组与剩余切片。 |
| `split_first_chunk_mut()` | 返回前 `N` 元素可变数组与剩余切片。 |
| `split_last_chunk()` | 返回剩余切片与末尾 `N` 元素数组。 |
| `split_last_chunk_mut()` | 返回剩余切片与末尾 `N` 元素可变数组。 |

### 索引与指针

| 方法 | 说明 |
| --- | --- |
| `get(index)` | 按下标取元素或子切片，越界返回 `None`。 |
| `get_mut(index)` | 取元素或子切片可变引用，越界返回 `None`。 |
| `get_unchecked(index)` | 不检查越界地取元素或子切片引用，`unsafe`。 |
| `get_unchecked_mut(index)` | 不检查越界地取可变引用，`unsafe`。 |
| `get_disjoint_mut(indices)` | 取多个互不重叠位置的可变引用。 |
| `get_disjoint_unchecked_mut(indices)` | 不检查重叠与越界地取多个可变引用，`unsafe`。 |
| `as_ptr()` | 返回指向切片缓冲区的裸指针。 |
| `as_mut_ptr()` | 返回指向缓冲区的可变裸指针。 |
| `as_ptr_range()` | 返回覆盖整个切片的首尾裸指针区间。 |
| `as_mut_ptr_range()` | 返回覆盖整个切片的首尾可变裸指针区间。 |
| `as_array()` | 返回底层数组引用，长度不是 `N` 时返回 `None`。 |
| `as_mut_array()` | 返回底层数组可变引用，长度不是 `N` 时返回 `None`。 |
| `element_offset(element)` | 返回元素引用所指向的下标。 |
| `subslice_range(subslice)` | 返回子切片对应的下标区间。 |

### 切分

| 方法 | 说明 |
| --- | --- |
| `split_at(mid)` | 在 `mid` 处切成两个 `&[T]`。 |
| `split_at_mut(mid)` | 在 `mid` 处切成两个 `&mut [T]`。 |
| `split_at_unchecked(mid)` | 不检查 `mid` 越界地切分，`unsafe`。 |
| `split_at_mut_unchecked(mid)` | 不检查越界地切成两个可变切片，`unsafe`。 |
| `split_at_checked(mid)` | 切分，`mid` 超过长度时返回 `None`。 |
| `split_at_mut_checked(mid)` | 可变切分，`mid` 超过长度时返回 `None`。 |
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
| `split_off(range)` | 从 `&mut &[T]` 摘出范围子切片并返回引用。 |
| `split_off_mut(range)` | 从 `&mut &mut [T]` 摘出范围子切片可变引用。 |
| `split_off_first()` | 从 `&mut &[T]` 头部摘下一个元素引用。 |
| `split_off_first_mut()` | 从 `&mut &mut [T]` 头部摘下可变元素引用。 |
| `split_off_last()` | 从 `&mut &[T]` 尾部摘下一个元素引用。 |
| `split_off_last_mut()` | 从 `&mut &mut [T]` 尾部摘下可变元素引用。 |

### 查找、比较与 ASCII

| 方法 | 说明 |
| --- | --- |
| `contains(x)` | 判断切片是否含有等于 `x` 的元素。 |
| `starts_with(needle)` | 判断 `needle` 是否为切片的前缀。 |
| `ends_with(needle)` | 判断 `needle` 是否为切片的后缀。 |
| `strip_prefix(prefix)` | 去掉前缀并返回剩余子切片。 |
| `strip_suffix(suffix)` | 去掉后缀并返回剩余子切片。 |
| `strip_circumfix(prefix, suffix)` | 同时去掉前后缀并返回中间子切片。 |
| `binary_search(x)` | 在有序切片中二分查找，返回命中或插入点。 |
| `binary_search_by(f)` | 用比较函数在有序切片中二分查找。 |
| `binary_search_by_key(b, f)` | 用键提取函数在有序切片中二分查找。 |
| `is_sorted()` | 判断元素是否按升序排列。 |
| `is_sorted_by(compare)` | 用比较函数判断元素是否有序。 |
| `is_sorted_by_key(f)` | 用键提取函数判断元素是否有序。 |
| `partition_point(pred)` | 返回第一个谓词为假的元素下标。 |
| `is_ascii()` | 判断所有字节是否都落在 ASCII 范围内。 |
| `eq_ignore_ascii_case(other)` | 忽略 ASCII 大小写地比较两个字节切片。 |
| `make_ascii_uppercase()` | 就地把 ASCII 小写字母改成大写。 |
| `make_ascii_lowercase()` | 就地把 ASCII 大写字母改成小写。 |
| `escape_ascii()` | 返回把字节按 ASCII 规则转义的迭代器。 |
| `trim_ascii_start()` | 返回去掉前导 ASCII 空白后的字节切片。 |
| `trim_ascii_end()` | 返回去掉尾部 ASCII 空白后的字节切片。 |
| `trim_ascii()` | 返回去掉首尾 ASCII 空白后的字节切片。 |
| `to_ascii_uppercase()` | 返回全部转成 ASCII 大写的新字节向量。 |
| `to_ascii_lowercase()` | 返回全部转成 ASCII 小写的新字节向量。 |
| `utf8_chunks()` | 返回合法 UTF-8 片段与非法字节交错的迭代器。 |

### 排序与重排

| 方法 | 说明 |
| --- | --- |
| `sort()` | 升序稳定排序，相等元素保持原有顺序。 |
| `sort_by(compare)` | 用比较函数做稳定排序。 |
| `sort_by_key(f)` | 用键提取函数做稳定排序。 |
| `sort_by_cached_key(f)` | 键只计算一次的稳定排序。 |
| `sort_unstable()` | 升序不稳定排序，不保证相等元素顺序。 |
| `sort_unstable_by(compare)` | 用比较函数做不稳定排序。 |
| `sort_unstable_by_key(f)` | 用键提取函数做不稳定排序。 |
| `select_nth_unstable(index)` | 重排使 `index` 处元素就位，两侧不保证有序。 |
| `select_nth_unstable_by(index, compare)` | 用比较函数做第 n 元素选择。 |
| `select_nth_unstable_by_key(index, f)` | 用键提取函数做第 n 元素选择。 |
| `reverse()` | 原地反转元素顺序。 |
| `rotate_left(mid)` | 原地左旋，前 `mid` 个元素移到末尾。 |
| `rotate_right(k)` | 原地右旋，后 `k` 个元素移到开头。 |
| `swap(a, b)` | 交换下标 `a` 与 `b` 处的元素。 |

### 修改与填充

| 方法 | 说明 |
| --- | --- |
| `fill(value)` | 用克隆的 `value` 填满整个切片。 |
| `fill_with(f)` | 用闭包依次产生的值填满整个切片。 |
| `clone_from_slice(src)` | 用 `src` 逐元素克隆覆盖自身。 |
| `copy_from_slice(src)` | 用 `src` 做 memcpy 覆盖自身。 |
| `copy_within(src, dest)` | 把自身某范围的元素 memmove 到另一位置。 |
| `swap_with_slice(other)` | 整体交换两个等长切片的全部元素。 |
| `write_copy_of_slice(src)` | 把 `Copy` 元素拷入未初始化切片并返回引用。 |
| `write_clone_of_slice(src)` | 把 `Clone` 元素克隆进未初始化切片并返回引用。 |
| `align_to()` | 按对齐要求把切片重解释为 `&[U]`，`unsafe`。 |
| `align_to_mut()` | 同上，返回可变切片，`unsafe`。 |

### 迭代与分块

| 方法 | 说明 |
| --- | --- |
| `iter()` | 返回遍历切片的不可变迭代器。 |
| `iter_mut()` | 返回可修改每个元素的迭代器。 |
| `windows(size)` | 返回所有长度为 `size` 的重叠窗口。 |
| `array_windows()` | 返回 `N` 个元素的重叠窗口，产出数组引用。 |
| `chunks(chunk_size)` | 从头按 `chunk_size` 切块迭代。 |
| `chunks_mut(chunk_size)` | 可变的从头切块迭代。 |
| `chunks_exact(chunk_size)` | 从头切等长块，丢弃末尾不足一块。 |
| `chunks_exact_mut(chunk_size)` | 可变的等长块切分。 |
| `rchunks(chunk_size)` | 从尾部按 `chunk_size` 切块迭代。 |
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

### 构造与转换

| 方法 | 说明 |
| --- | --- |
| `new_uninit_slice(len)` | 创建指定长度、内容未初始化的装箱切片。 |
| `new_zeroed_slice(len)` | 创建指定长度、字节全零的装箱切片。 |
| `assume_init()` | 把未初始化装箱切片转成 `Box<[T]>`，`unsafe`。 |
| `assume_init_drop()` | 就地把装箱切片中的值析构，`unsafe`。 |
| `assume_init_ref()` | 取未初始化装箱切片的共享引用，`unsafe`。 |
| `assume_init_mut()` | 取未初始化装箱切片的可变引用，`unsafe`。 |
| `to_vec()` | 克隆整个切片生成新的 `Vec`。 |
| `into_vec()` | 把 `Box<[T]>` 无拷贝地转成 `Vec<T>`。 |
| `repeat(n)` | 复制切片 `n` 次生成新 `Vec`。 |
| `concat()` | 把切片元素拼成一个值，如拼接字符串。 |
| `join(sep)` | 用分隔符把切片元素拼成一个值。 |
| `as_flattened()` | 把 `&[[T; N]]` 展平成 `&[T]`。 |
| `as_flattened_mut()` | 把 `&mut [[T; N]]` 展平成 `&mut [T]`。 |

## 示例

切分、查找与二分：

```rust
fn main() {
    let data = vec![5, 3, 8, 1, 9, 2];

    // &Vec<i32> 自动解引用成 &[i32]
    let all: &[i32] = &data;
    assert_eq!(all.len(), 6);

    // split_at 要求 mid <= len，否则 panic
    let (left, right) = all.split_at(3);
    assert_eq!(left, &[5, 3, 8]);
    assert_eq!(right, &[1, 9, 2]);

    // get 越界返回 None，不会 panic
    assert_eq!(all.get(6), None);
    assert_eq!(all.first(), Some(&5));
    assert!(all.contains(&8));
    assert_eq!(all.strip_prefix(&[5, 3]), Some(&[8, 1, 9, 2][..]));

    // 二分查找要求切片已升序
    let mut sorted = all.to_vec();
    sorted.sort();
    assert_eq!(sorted.binary_search(&5), Ok(3));
    assert_eq!(sorted.binary_search(&4), Err(3));
}
```

原地修改与分块迭代：

```rust
fn main() {
    let mut buf = [0u8; 8];
    let s: &mut [u8] = &mut buf[..];

    // fill 用克隆值填满，copy_from_slice 要求两边等长
    s.fill(7);
    assert!(s.iter().all(|&b| b == 7));
    s.copy_from_slice(&[1, 2, 3, 4, 5, 6, 7, 8]);
    assert_eq!(s.to_vec(), vec![1, 2, 3, 4, 5, 6, 7, 8]);

    // chunks_exact 每 3 个一组，末尾不足 3 个的部分被丢弃
    let total: u32 = s
        .chunks_exact(3)
        .map(|c| c.iter().map(|&b| b as u32).sum::<u32>())
        .sum();
    assert_eq!(total, 1 + 2 + 3 + 4 + 5 + 6);

    // windows 给出重叠窗口，可以逐对比较相邻元素
    let mut rises = 0;
    for w in s.windows(2) {
        if w[1] > w[0] {
            rises += 1;
        }
    }
    assert_eq!(rises, 7);

    // iter_mut 就地翻倍
    for b in s.iter_mut() {
        *b *= 2;
    }
    assert_eq!(s.to_vec(), vec![2, 4, 6, 8, 10, 12, 14, 16]);
}
```

## 常见陷阱

1. **下标越界直接 panic**：`s[i]` 会做边界检查，`i >= s.len()` 时 panic；来自外部输入的下标改用 `get` / `get_mut` 并处理 `None`。
2. **切片边界按元素还是按字节**：对 `[T]` 的下标按**元素**计数；而 `&str` 的 `&s[a..b]` 按**字节**偏移，落在 UTF-8 字符中间会 panic，先用 `char_indices` 或 `is_char_boundary` 校验。
3. **`split_at` 越界 panic**：`mid > len` 会 panic，只有 `mid == len` 才允许（返回空的后半段）；输入不可信时用 `split_at_checked`。
4. **`sort` 要求 `Ord`**：`f64` 只实现 `PartialOrd`，直接 `sort()` 编译不过，要用 `sort_by(|a, b| a.partial_cmp(b).unwrap())`，否则得先排除 `NaN`。
5. **`binary_search` 要求有序**：切片未排序时返回值没有意义，且不会报错；调用前用 `is_sorted` 断言，或干脆先 `sort`。
6. **`fill` / `copy_from_slice` 的长度约束**：`copy_from_slice` 要求两边长度相同，否则 panic；`fill` 需要 `T: Clone`，对非 `Copy` 类型是逐元素克隆。

## 相关

- [[slice|std::slice 模块]]：本条目所属模块，含 `Iter`、`Chunks`、`Windows` 等迭代器类型。
- [[primitive|std::primitive 模块]]：`[T]` 作为原始类型的入口页。
- [[vec.Vec|Vec]]：最常用的切片来源，`Deref` 到 `[T]`。
- [[primitive.str|Type str]]：UTF-8 字符串切片，边界规则与字节切片不同。
- [[primitive.array|Type array]]：定长数组 `[T; N]`，可无损强制转换成切片。
- [[macro.vec|vec! 宏]]：快速造出 `Vec`，再借成切片。
- [[12-集合类型|集合类型]]：`Vec`、切片与其它容器的选型对比。
