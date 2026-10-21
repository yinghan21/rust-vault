---
title: "std::simd"
type: std-模块
module: simd
stable: ""
unstable: true
tags:
  - std/模块
aliases:
  - simd
一句话: 可移植 SIMD：不绑定具体架构的向量类型 `Simd<T, N>`、掩码 `Mask` 与一组按长度取名的别名。
---

# std::simd

> [!warning] 实验性模块
> 该模块需要 nightly 工具链，并通过 `#![feature(...)]` 启用，API 可能随时变化，**不要用于生产代码**。

## 模块简介

`std::simd` 是可移植 SIMD（portable SIMD）模块：一套不绑定任何具体硬件架构的向量抽象，目标是「在任何目标上都快且可预测」。与 `std::arch` 里按目标架构提供的 SIMD 不同，这里的代码对每个 target 都能编译，写起来和普通 Rust 没什么区别。核心类型是 `Simd<T, N>`（形状为 `[T; N]`、运算按元素 `T` 进行）与掩码 `Mask`；「元素类型 × 长度」的各种组合以类型别名给出，例如 `f32x4`、`u8x16`、`mask32x8`。

## 主要条目（共 136 项，下列为代表项，完整列表见官方文档）
- `Simd`（结构体）：形状为 `[T; N]` 的 SIMD 向量。
- `Mask`（结构体）：`N` 个元素的 SIMD 掩码。
- `simd_swizzle`（宏）：按给定索引从若干向量中拷贝元素组成新向量。
- `SimdElement` / `MaskElement`（特质）：可作为向量元素 / 掩码元素的标记特质。
- `Select`（特质）：用掩码在两个向量间逐元素挑选。
- `Swizzle`（特质）：用另一个向量的元素构造向量。
- `ToBytes`（特质）：把 SIMD 向量转换成字节向量。
- `StdFloat`（特质）：浮点函数入口，缺硬件支持时可能退化为调用系统数学库。
- `f32x4`、`u8x16`、`mask32x8`（类型别名）：常见的固定长度向量与掩码别名。

## 相关

- [[模块索引]]
- [[arch|std::arch 模块]]：按目标架构划分的 SIMD，与这里的可移植版本相对。
- [[26-性能与优化|性能与优化]]：什么时候值得把标量循环改写成向量写法。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 136 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`Mask`](https://doc.rust-lang.org/std/simd/struct.Mask.html)
- [`Simd`](https://doc.rust-lang.org/std/simd/struct.Simd.html)

### 特质

- [`MaskElement`](https://doc.rust-lang.org/std/simd/trait.MaskElement.html)
- [`Select`](https://doc.rust-lang.org/std/simd/trait.Select.html)
- [`SimdCast`](https://doc.rust-lang.org/std/simd/trait.SimdCast.html)
- [`SimdElement`](https://doc.rust-lang.org/std/simd/trait.SimdElement.html)
- [`StdFloat`](https://doc.rust-lang.org/std/simd/trait.StdFloat.html)
- [`Swizzle`](https://doc.rust-lang.org/std/simd/trait.Swizzle.html)
- [`ToBytes`](https://doc.rust-lang.org/std/simd/trait.ToBytes.html)

### 类型别名

- [`f16x1`](https://doc.rust-lang.org/std/simd/type.f16x1.html)
- [`f16x2`](https://doc.rust-lang.org/std/simd/type.f16x2.html)
- [`f16x4`](https://doc.rust-lang.org/std/simd/type.f16x4.html)
- [`f16x8`](https://doc.rust-lang.org/std/simd/type.f16x8.html)
- [`f16x16`](https://doc.rust-lang.org/std/simd/type.f16x16.html)
- [`f16x32`](https://doc.rust-lang.org/std/simd/type.f16x32.html)
- [`f16x64`](https://doc.rust-lang.org/std/simd/type.f16x64.html)
- [`f32x1`](https://doc.rust-lang.org/std/simd/type.f32x1.html)
- [`f32x2`](https://doc.rust-lang.org/std/simd/type.f32x2.html)
- [`f32x4`](https://doc.rust-lang.org/std/simd/type.f32x4.html)
- [`f32x8`](https://doc.rust-lang.org/std/simd/type.f32x8.html)
- [`f32x16`](https://doc.rust-lang.org/std/simd/type.f32x16.html)
- [`f32x32`](https://doc.rust-lang.org/std/simd/type.f32x32.html)
- [`f32x64`](https://doc.rust-lang.org/std/simd/type.f32x64.html)
- [`f64x1`](https://doc.rust-lang.org/std/simd/type.f64x1.html)
- [`f64x2`](https://doc.rust-lang.org/std/simd/type.f64x2.html)
- [`f64x4`](https://doc.rust-lang.org/std/simd/type.f64x4.html)
- [`f64x8`](https://doc.rust-lang.org/std/simd/type.f64x8.html)
- [`f64x16`](https://doc.rust-lang.org/std/simd/type.f64x16.html)
- [`f64x32`](https://doc.rust-lang.org/std/simd/type.f64x32.html)
- [`f64x64`](https://doc.rust-lang.org/std/simd/type.f64x64.html)
- [`i8x1`](https://doc.rust-lang.org/std/simd/type.i8x1.html)
- [`i8x2`](https://doc.rust-lang.org/std/simd/type.i8x2.html)
- [`i8x4`](https://doc.rust-lang.org/std/simd/type.i8x4.html)
- [`i8x8`](https://doc.rust-lang.org/std/simd/type.i8x8.html)
- [`i8x16`](https://doc.rust-lang.org/std/simd/type.i8x16.html)
- [`i8x32`](https://doc.rust-lang.org/std/simd/type.i8x32.html)
- [`i8x64`](https://doc.rust-lang.org/std/simd/type.i8x64.html)
- [`i16x1`](https://doc.rust-lang.org/std/simd/type.i16x1.html)
- [`i16x2`](https://doc.rust-lang.org/std/simd/type.i16x2.html)
- [`i16x4`](https://doc.rust-lang.org/std/simd/type.i16x4.html)
- [`i16x8`](https://doc.rust-lang.org/std/simd/type.i16x8.html)
- [`i16x16`](https://doc.rust-lang.org/std/simd/type.i16x16.html)
- [`i16x32`](https://doc.rust-lang.org/std/simd/type.i16x32.html)
- [`i16x64`](https://doc.rust-lang.org/std/simd/type.i16x64.html)
- [`i32x1`](https://doc.rust-lang.org/std/simd/type.i32x1.html)
- [`i32x2`](https://doc.rust-lang.org/std/simd/type.i32x2.html)
- [`i32x4`](https://doc.rust-lang.org/std/simd/type.i32x4.html)
- [`i32x8`](https://doc.rust-lang.org/std/simd/type.i32x8.html)
- [`i32x16`](https://doc.rust-lang.org/std/simd/type.i32x16.html)
- [`i32x32`](https://doc.rust-lang.org/std/simd/type.i32x32.html)
- [`i32x64`](https://doc.rust-lang.org/std/simd/type.i32x64.html)
- [`i64x1`](https://doc.rust-lang.org/std/simd/type.i64x1.html)
- [`i64x2`](https://doc.rust-lang.org/std/simd/type.i64x2.html)
- [`i64x4`](https://doc.rust-lang.org/std/simd/type.i64x4.html)
- [`i64x8`](https://doc.rust-lang.org/std/simd/type.i64x8.html)
- [`i64x16`](https://doc.rust-lang.org/std/simd/type.i64x16.html)
- [`i64x32`](https://doc.rust-lang.org/std/simd/type.i64x32.html)
- [`i64x64`](https://doc.rust-lang.org/std/simd/type.i64x64.html)
- [`isizex1`](https://doc.rust-lang.org/std/simd/type.isizex1.html)
- [`isizex2`](https://doc.rust-lang.org/std/simd/type.isizex2.html)
- [`isizex4`](https://doc.rust-lang.org/std/simd/type.isizex4.html)
- [`isizex8`](https://doc.rust-lang.org/std/simd/type.isizex8.html)
- [`isizex16`](https://doc.rust-lang.org/std/simd/type.isizex16.html)
- [`isizex32`](https://doc.rust-lang.org/std/simd/type.isizex32.html)
- [`isizex64`](https://doc.rust-lang.org/std/simd/type.isizex64.html)
- [`mask8x1`](https://doc.rust-lang.org/std/simd/type.mask8x1.html)
- [`mask8x2`](https://doc.rust-lang.org/std/simd/type.mask8x2.html)
- [`mask8x4`](https://doc.rust-lang.org/std/simd/type.mask8x4.html)
- [`mask8x8`](https://doc.rust-lang.org/std/simd/type.mask8x8.html)
- [`mask8x16`](https://doc.rust-lang.org/std/simd/type.mask8x16.html)
- [`mask8x32`](https://doc.rust-lang.org/std/simd/type.mask8x32.html)
- [`mask8x64`](https://doc.rust-lang.org/std/simd/type.mask8x64.html)
- [`mask16x1`](https://doc.rust-lang.org/std/simd/type.mask16x1.html)
- [`mask16x2`](https://doc.rust-lang.org/std/simd/type.mask16x2.html)
- [`mask16x4`](https://doc.rust-lang.org/std/simd/type.mask16x4.html)
- [`mask16x8`](https://doc.rust-lang.org/std/simd/type.mask16x8.html)
- [`mask16x16`](https://doc.rust-lang.org/std/simd/type.mask16x16.html)
- [`mask16x32`](https://doc.rust-lang.org/std/simd/type.mask16x32.html)
- [`mask16x64`](https://doc.rust-lang.org/std/simd/type.mask16x64.html)
- [`mask32x1`](https://doc.rust-lang.org/std/simd/type.mask32x1.html)
- [`mask32x2`](https://doc.rust-lang.org/std/simd/type.mask32x2.html)
- [`mask32x4`](https://doc.rust-lang.org/std/simd/type.mask32x4.html)
- [`mask32x8`](https://doc.rust-lang.org/std/simd/type.mask32x8.html)
- [`mask32x16`](https://doc.rust-lang.org/std/simd/type.mask32x16.html)
- [`mask32x32`](https://doc.rust-lang.org/std/simd/type.mask32x32.html)
- [`mask32x64`](https://doc.rust-lang.org/std/simd/type.mask32x64.html)
- [`mask64x1`](https://doc.rust-lang.org/std/simd/type.mask64x1.html)
- [`mask64x2`](https://doc.rust-lang.org/std/simd/type.mask64x2.html)
- [`mask64x4`](https://doc.rust-lang.org/std/simd/type.mask64x4.html)
- [`mask64x8`](https://doc.rust-lang.org/std/simd/type.mask64x8.html)
- [`mask64x16`](https://doc.rust-lang.org/std/simd/type.mask64x16.html)
- [`mask64x32`](https://doc.rust-lang.org/std/simd/type.mask64x32.html)
- [`mask64x64`](https://doc.rust-lang.org/std/simd/type.mask64x64.html)
- [`masksizex1`](https://doc.rust-lang.org/std/simd/type.masksizex1.html)
- [`masksizex2`](https://doc.rust-lang.org/std/simd/type.masksizex2.html)
- [`masksizex4`](https://doc.rust-lang.org/std/simd/type.masksizex4.html)
- [`masksizex8`](https://doc.rust-lang.org/std/simd/type.masksizex8.html)
- [`masksizex16`](https://doc.rust-lang.org/std/simd/type.masksizex16.html)
- [`masksizex32`](https://doc.rust-lang.org/std/simd/type.masksizex32.html)
- [`masksizex64`](https://doc.rust-lang.org/std/simd/type.masksizex64.html)
- [`u8x1`](https://doc.rust-lang.org/std/simd/type.u8x1.html)
- [`u8x2`](https://doc.rust-lang.org/std/simd/type.u8x2.html)
- [`u8x4`](https://doc.rust-lang.org/std/simd/type.u8x4.html)
- [`u8x8`](https://doc.rust-lang.org/std/simd/type.u8x8.html)
- [`u8x16`](https://doc.rust-lang.org/std/simd/type.u8x16.html)
- [`u8x32`](https://doc.rust-lang.org/std/simd/type.u8x32.html)
- [`u8x64`](https://doc.rust-lang.org/std/simd/type.u8x64.html)
- [`u16x1`](https://doc.rust-lang.org/std/simd/type.u16x1.html)
- [`u16x2`](https://doc.rust-lang.org/std/simd/type.u16x2.html)
- [`u16x4`](https://doc.rust-lang.org/std/simd/type.u16x4.html)
- [`u16x8`](https://doc.rust-lang.org/std/simd/type.u16x8.html)
- [`u16x16`](https://doc.rust-lang.org/std/simd/type.u16x16.html)
- [`u16x32`](https://doc.rust-lang.org/std/simd/type.u16x32.html)
- [`u16x64`](https://doc.rust-lang.org/std/simd/type.u16x64.html)
- [`u32x1`](https://doc.rust-lang.org/std/simd/type.u32x1.html)
- [`u32x2`](https://doc.rust-lang.org/std/simd/type.u32x2.html)
- [`u32x4`](https://doc.rust-lang.org/std/simd/type.u32x4.html)
- [`u32x8`](https://doc.rust-lang.org/std/simd/type.u32x8.html)
- [`u32x16`](https://doc.rust-lang.org/std/simd/type.u32x16.html)
- [`u32x32`](https://doc.rust-lang.org/std/simd/type.u32x32.html)
- [`u32x64`](https://doc.rust-lang.org/std/simd/type.u32x64.html)
- [`u64x1`](https://doc.rust-lang.org/std/simd/type.u64x1.html)
- [`u64x2`](https://doc.rust-lang.org/std/simd/type.u64x2.html)
- [`u64x4`](https://doc.rust-lang.org/std/simd/type.u64x4.html)
- [`u64x8`](https://doc.rust-lang.org/std/simd/type.u64x8.html)
- [`u64x16`](https://doc.rust-lang.org/std/simd/type.u64x16.html)
- [`u64x32`](https://doc.rust-lang.org/std/simd/type.u64x32.html)
- [`u64x64`](https://doc.rust-lang.org/std/simd/type.u64x64.html)
- [`usizex1`](https://doc.rust-lang.org/std/simd/type.usizex1.html)
- [`usizex2`](https://doc.rust-lang.org/std/simd/type.usizex2.html)
- [`usizex4`](https://doc.rust-lang.org/std/simd/type.usizex4.html)
- [`usizex8`](https://doc.rust-lang.org/std/simd/type.usizex8.html)
- [`usizex16`](https://doc.rust-lang.org/std/simd/type.usizex16.html)
- [`usizex32`](https://doc.rust-lang.org/std/simd/type.usizex32.html)
- [`usizex64`](https://doc.rust-lang.org/std/simd/type.usizex64.html)

### 宏

- [`simd_swizzle`](https://doc.rust-lang.org/std/simd/macro.simd_swizzle.html)

<!-- END AUTO ITEMS -->
