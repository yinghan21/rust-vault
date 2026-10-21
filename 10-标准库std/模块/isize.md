---
title: "std::isize"
type: std-模块
module: isize
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - isize
一句话: 指针宽度有符号整数的常量模块，只剩已弃用的 MIN / MAX，新代码用 isize::MIN 这类关联常量。
---

# std::isize

> [!abstract] 一句话
> `std::isize` 是指针宽度有符号整数类型的「常量模块」：只有 `MIN`、`MAX` 两个已弃用的常量。

## 模块简介

`std::isize` 是个**冗余模块**，只把 `isize` 的边界 `MIN` / `MAX` 以模块路径导出，供旧代码写 `std::isize::MAX`。这两个常量现已标记 `deprecated`，官方建议改用原始类型上的关联常量 `isize::MIN` / `isize::MAX` / `isize::BITS`。

**整数类型的方法不在本模块里。** 溢出检查、解析、转换等能力都定义在原始类型 `isize` 上，见[[primitive.整数类型|整数类型]]页面：`isize::checked_add`、`isize::from_str_radix`、`isize::abs` 等等。本页只说明模块里的两个常量。

`isize` 的宽度**随平台变化**：32 位平台是 32 位，64 位平台是 64 位，与指针宽度一致。它是「长度、索引、偏移量」的有符号对应物（无符号版是 `usize`），常用于计算两个索引之差、`slice::binary_search` 返回的位置、以及需要表示负偏移的指针运算。最大值等于 `isize::MAX`，因此标准库中任何小于 `isize::MAX` 字节的分配都是合法的。

## 快速上手

```rust
fn main() {
    // 模块常量：已弃用的旧路径
    #[allow(deprecated)]
    let old_min = std::isize::MIN;
    assert_eq!(old_min, isize::MIN);

    // 推荐写法：原始类型上的关联常量
    assert_eq!(isize::BITS as usize, std::mem::size_of::<isize>() * 8);
    assert_eq!(isize::MAX.checked_add(1), None);

    // isize 的宽度随平台变化：32 位平台 32 位，64 位平台 64 位
    let data = [10, 20, 30];
    let last = data.len() as isize - 1;
    assert_eq!(data[last as usize], 30);

    assert_eq!(isize::MAX as u64 + 1, 1u64 << (isize::BITS - 1));
    println!("isize 宽度 = {} 位", isize::BITS);
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| `std::isize::MIN` | 最小值，宽度随平台（32/64 位），已弃用。 |
| `std::isize::MAX` | 最大值，宽度随平台，已弃用。 |
| `isize::MIN` / `isize::MAX` | 推荐写法：原始类型上的取值边界。 |
| `isize::BITS` | 位宽，等于 `usize::BITS`。 |
| `isize::abs` / `unsigned_abs` | 取绝对值；后者返回 `usize`。 |
| `isize::checked_sub` | 计算索引差值时防溢出。 |
| `isize::try_from` | 从 `usize` 或更宽整数安全转换。 |
| `isize::from_str_radix` | 按指定进制解析。 |
| `isize::signum` | 返回 `-1` / `0` / `1`。 |
| `isize::saturating_add` | 溢出时钳制到边界。 |
| `isize::wrapping_neg` | 回绕取负，对 `MIN` 不 panic。 |
| `isize::to_le_bytes` | 转成平台无关的固定长度字节数组。 |
| `isize::MAX` | 也是标准库允许的最大对象字节数上限。 |

## 注意事项

> [!warning] 模块常量已弃用且宽度不定
> `std::isize::MIN` 会触发 `deprecated` 警告，改用 `isize::MIN`。更要紧的是：**不要**把 `isize::MAX` 的数值硬编码成 `9223372036854775807`，32 位平台上它是 `2147483647`；需要常量时用 `isize::MAX` 本身，需要固定宽度时用 `i64`。

> [!danger] `usize` 与 `isize` 互转要检查
> `x as isize` 在值超过 `isize::MAX` 时会变成负数，`(-1isize) as usize` 会变成 `usize::MAX`，直接拿去索引就是越界 panic。用 `isize::try_from(u)?.try_into()?` 或先比较范围再转换；数组索引虽然接受 `usize`，但先用 `isize` 算差再转回时要保证非负。

> [!tip] 什么时候用它
> 索引和长度用 `usize`；需要「可能为负的偏移或差值」时才用 `isize`，例如 `data.len() as isize - i as isize`。跨平台固定格式（文件头、网络协议）一律用 `i32` / `i64`，不要用 `isize`，否则在不同架构上读出的字节数都不一样。

## 相关

- [[primitive.整数类型|整数类型]]：`isize` 的全部方法与转换规则。
- [[usize|std::usize]]：无符号的指针宽度类型，索引专用。
- [[i64|std::i64]]：需要固定 64 位时的替代品。
- [[primitive.slice|slice]]：`isize` 常见的偏移计算场景。
- [[03-变量与数据类型|变量与数据类型]]：平台相关整数类型的定位。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 2 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 常量

- [`MAX`](https://doc.rust-lang.org/std/isize/constant.MAX.html)
- [`MIN`](https://doc.rust-lang.org/std/isize/constant.MIN.html)

<!-- END AUTO ITEMS -->
