---
title: "std::usize"
type: std-模块
module: usize
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - usize
一句话: 指针宽度无符号整数的冗余常量模块，只剩待弃用的 MIN / MAX，新代码写 usize::MIN。
---

# std::usize

> [!abstract] 一句话
> `std::usize` 是「指针宽度无符号整数」的「常量模块」：只有 `MIN`、`MAX` 两个常量，官方已建议改用原始类型上的关联常量。

## 模块简介

`std::usize` 是个**冗余模块**：它不定义类型，只把 `usize` 的取值边界挂成模块路径 `std::usize::MIN` / `std::usize::MAX`。这两个常量已被标注「未来版本弃用」，现在引用只报 `deprecated` 警告，将来会变成硬错误；新代码直接写 `usize::MIN` / `usize::MAX`。

**整数的方法不在这个模块里。** 溢出检查、进制解析、位运算、字节序转换全部定义在原始类型 `usize` 上，属于[[primitive.整数类型|整数类型]]页面的内容 —— 例如 `usize::checked_sub`、`usize::div_ceil`、`usize::from_str_radix`、`usize::to_be_bytes`。位宽 `BITS` 也只在原始类型上有。所以本页只讲那两个常量，其余请移步该页。

`usize` 的宽度跟着**目标平台的指针宽度**走：64 位平台是 64 位（最大值 `18446744073709551615`），32 位平台是 32 位（最大值 `4294967295`）。它承担所有「内存尺寸相关」的数字：`len()`、`capacity()`、切片下标、`std::mem::size_of` 的返回值、指针偏移。换句话说，`usize` 是「能索引到本进程任意一个字节」的无符号类型 —— 也正因为它随平台变宽，**不适合**做需要落盘或上线的固定宽度整数。

## 快速上手

```rust
fn main() {
    #[allow(deprecated)]
    let legacy_max = std::usize::MAX;
    assert_eq!(legacy_max, usize::MAX);

    assert_eq!(usize::MIN, 0);
    assert_eq!(usize::BITS as usize, std::mem::size_of::<usize>() * 8);
    assert!(usize::BITS == 32 || usize::BITS == 64);

    // 长度、下标、容量都是 usize
    let v = vec!["a", "b", "c"];
    let n: usize = v.len();
    assert_eq!(n, 3);
    assert_eq!(v[n - 1], "c");

    // usize 随平台变宽：要跨平台落盘就转成固定宽度的 u64
    let count = 1_000_000usize;
    assert_eq!(u64::try_from(count).unwrap(), 1_000_000u64);

    // 减法容易下溢：先比较，或用 checked_sub
    let (a, b) = (2usize, 5usize);
    assert_eq!(a.checked_sub(b), None);
    assert_eq!(b.checked_sub(a), Some(3));
    assert_eq!(b - a, 3);

    println!("usize 位宽 = {}，最大值 = {}", usize::BITS, usize::MAX);
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| `std::usize::MIN` | 最小值 `0`，模块路径已标记为待弃用。 |
| `std::usize::MAX` | 最大值随平台：32 位 `2³²-1`，64 位 `2⁶⁴-1`。 |
| `usize::MIN` / `usize::MAX` | 推荐写法：原始类型上的取值边界。 |
| `usize::BITS` | 位宽，等于指针宽度（`32` 或 `64`）。 |
| `v.len()` | 长度与容量都是 `usize`，切片下标也要求 `usize`。 |
| `usize::from(u16)` | 无符号加宽，任何平台都不会失败。 |
| `usize::try_from(u64)` | 32 位平台上收窄，越界返回 `Err`。 |
| `usize::checked_sub` / `checked_add` | 长度计算的安全加减，避免下溢。 |
| `usize::saturating_sub` | 下溢钳制到 `0`，比 `Option` 少一层处理。 |
| `usize::wrapping_sub` | 下溢回绕，环形缓冲里常用。 |
| `usize::div_ceil` | 向上取整除法，算块数 / 页数常用。 |
| `usize::next_power_of_two` | 向上取到 2 的幂，扩容策略常用。 |
| `usize::count_ones` / `leading_zeros` | 位计数，可用来算有效位宽。 |
| `usize::to_be_bytes` | 转成与平台宽度等长的字节数组。 |

## 注意事项

> [!danger] 平台差异：本地能跑，32 位崩
> `usize` 的宽度不是常量。`let n = 4_294_967_296usize;` 在 32 位目标上直接编译失败（字面量越界），`n as u32` 或 `n as usize` 在别处也会截断。跨平台数据（文件头、协议字段、序列化结果）一律用固定宽度的 `u32` / `u64`，进内存时再 `try_from` 成 `usize`。

> [!warning] 长度减法下溢
> `v.len() - 1` 在空 `Vec` 上 debug 会 panic、release 会回绕成一个巨大的数，随后下标越界 —— 报错位置离真正的原因很远。用 `checked_sub`、`saturating_sub`，或者先 `if v.is_empty()` 判断。

> [!tip] `usize` 不是通用无符号整数
> Rust 没有隐式整数提升，`u32` 的下标要显式 `as usize` 才能索引切片 —— 这是故意逼你在可能截断的地方做决定。约定是：`usize` 只管长度、容量、下标；其余场景该用 `u32` / `u64` 就用它们，别为了「省一次转换」把业务值塞进 `usize`。

## 相关

- [[primitive.整数类型|整数类型]]：`usize` 的全部方法、位运算与转换规则都在这里。
- [[u32|std::u32]]：固定 32 位，适合协议字段与位标志。
- [[u64|std::u64]]：固定 64 位，适合时间戳与哈希。
- [[vec|std::vec 模块]]：`Vec` 的长度、容量、下标全部是 `usize`。
- [[mem|std::mem 模块]]：`size_of` / `align_of` 的返回值就是 `usize`。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 2 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 常量

- [`MAX`](https://doc.rust-lang.org/std/usize/constant.MAX.html)
- [`MIN`](https://doc.rust-lang.org/std/usize/constant.MIN.html)

<!-- END AUTO ITEMS -->
