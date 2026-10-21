---
title: "std::num::NonZeroU32"
type: std-条目
kind: 类型别名
module: num
slug: num.NonZeroU32
stable: "1.28.0"
tags:
  - std/类型
  - rust/进阶
aliases:
  - NonZeroU32
一句话: 保证不为 0 的 u32，让「非零」成为类型级不变量，并使 Option<NonZeroU32> 与 u32 同大小。
---

# `NonZeroU32`

> [!abstract] 一句话
> `NonZeroU32` 是「已知不为 0 的 `u32`」：底层就是 32 位整数，但 `0` 不是合法取值。这既能把不变量写进类型，也能让 `Option<NonZeroU32>` 借助空指针优化与 `u32` 一样大。

## 简介

`NonZeroU32` 是类型别名，底层指向 `core::num` 里的非零整数包装类型。它保证与 `u32` **布局和位合法性一致**，唯一区别是 `0` 不是合法实例；因此 `NonZeroU32` 与 `u32` 在 FFI 边界上可以互换。

为什么要专门造一个类型，而不是到处写 `if x != 0`？

- **类型级不变量**：函数签名写 `fn parse(s: &str) -> Option<NonZeroU32>`，调用方看到类型就知道「拿到的值一定非零」，不必再查文档或加断言。
- **零开销的可选值**：因为 `0` 这个位模式被空出来了，`Option<NonZeroU32>` 用 `0` 表示 `None`，于是它与 `u32` **同大小同对齐**，并且 ABI 兼容 `u32`——空指针优化（null pointer optimization）的典型受益者。
- **常见用途**：缓存容量、非零句柄/文件描述符、序列号、`NonZeroUsize` 形式的「非零长度」、以及需要省掉 `Option` 标签字节的热点结构体。

同类还有 `NonZeroU8`、`NonZeroU16`、`NonZeroU64`、`NonZeroU128`、`NonZeroUsize`，以及有符号版本 `NonZeroI8` … `NonZeroIsize`，它们都在 [[num|std::num]] 模块下。

## 常见构造方式

- `NonZeroU32::new(v)`：最常用的入口，返回 `Option<NonZeroU32>`，`v == 0` 时得到 `None`。
- `v.try_into()`：`u32` → `NonZeroU32` 走 `TryFrom`，失败返回 `Err`，适合配合 `?` 写错误处理。
- `nz.get()`：取回内部的 `u32`；反向的 `u32::from(nz)` 是无损转换。
- 有符号/无符号之间的转换请显式写出目标类型，别依赖隐式推断，否则 `try_into()` 的 `Err` 类型会让人看不明白。

> [!note] 没有 `From<u32>`
> 因为 `0` 非法，`u32` 到 `NonZeroU32` 只能走可失败的 `TryFrom`；反过来 `NonZeroU32` 到 `u32` 是 `From`，永远不会失败。

## 示例

```rust
use std::mem::{align_of, size_of};
use std::num::NonZeroU32;

fn main() {
    // 与 u32 完全同布局
    assert_eq!(size_of::<NonZeroU32>(), size_of::<u32>());

    // 空指针优化：Option 不额外占空间
    assert_eq!(size_of::<Option<NonZeroU32>>(), size_of::<u32>());
    assert_eq!(align_of::<Option<NonZeroU32>>(), align_of::<u32>());

    // 0 不是合法值，所以构造是可失败的
    let n = NonZeroU32::new(7).unwrap();
    assert_eq!(n.get(), 7);
    assert_eq!(NonZeroU32::new(0), None);

    // 走 TryFrom：失败可以用 ? 传播，成功后再取回 u32
    let ok: NonZeroU32 = 5u32.try_into().unwrap();
    assert_eq!(u32::from(ok), 5);

    let zero: Result<NonZeroU32, _> = 0u32.try_into();
    assert!(zero.is_err());
}
```

## 常见陷阱

1. **以为 `new(0)` 会 panic**：它返回 `None`，不会崩；但随后 `.unwrap()` 就会崩，所以外部输入要走 `ok_or` + `?` 或 `match`。
2. **想用 `NonZeroU32::from(0)`**：`From<u32>` 没有实现，因为 `0` 非法；只能用 `new` 或 `TryFrom`。
3. **布局优化只发生在 `Option` 这一层**：`Option<NonZeroU32>` 才与 `u32` 同大小；再套一层 `Option`、或塞进 `Box`、或与别的字段组合，都不再有这个保证，别把「同大小」当通用结论。
4. **在 FFI 里混用 `Option<u32>`**：`Option<NonZeroU32>` 与 `u32` ABI 兼容，`Option<u32>` 不是，两者在 `extern "C"` 边界上不能互换。
5. **用非零类型做算术时忽略结果可能为 0**：相减、取余都可能越界或得到 `0`，这类情况要么用带检查的运算，要么提前判空，不要假设结果自动合法。

## 相关

- [[num|std::num 模块]]：`NonZeroU8` 到 `NonZeroUsize`、`NonZeroI*` 与 `NonZero` 泛型包装都在这里。
- [[option.Option|Option]]：空指针优化让 `Option<NonZeroU32>` 与 `u32` 同大小。
- [[cmp.Ord|Ord]]：非零整数同样实现了完整的大小比较与排序。
- [[24-unsafe 与 FFI|unsafe 与 FFI]]：ABI 兼容性在跨语言边界上尤其重要。
