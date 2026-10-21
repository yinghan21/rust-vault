---
title: "std::autodiff"
type: std-模块
module: autodiff
stable: ""
unstable: true
tags:
  - std/模块
aliases:
  - autodiff
一句话: 自动微分：用 `#[autodiff_forward]` / `#[autodiff_reverse]` 属性宏为函数生成求导版本。
---

# std::autodiff

> [!warning] 实验性模块
> 该模块需要 nightly 工具链，并通过 `#![feature(...)]` 启用，API 可能随时变化，**不要用于生产代码**。

## 模块简介

`std::autodiff` 提供自动微分（automatic differentiation）支持，由两个属性宏组成：`autodiff_forward` 使用前向模式，`autodiff_reverse` 使用反向模式，都作用在函数定义上并生成一个新的求导函数。官方说明提到：宏几乎可以作用于所有函数定义，参数可以是结构体、数组、切片、`Vec`、元组等；同一个函数可以叠加多个宏，以便分别对 `x` 和 `y` 求偏导；带泛型参数的函数同样支持。它最终落到编译器的 LLVM 层，对应的内建函数是 `intrinsics::autodiff`。

## 主要条目
`autodiff_forward`（属性宏）、`autodiff_reverse`（属性宏），共 2 项。

## 相关

- [[模块索引]]
- [[intrinsics|std::intrinsics 模块]]：`intrinsics::autodiff` 是这两个宏的底层入口。
- [[offload|std::offload 模块]]：同样靠属性宏生成编译器侧代码的实验性能力。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 2 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 其他

- [`autodiff_forward`](https://doc.rust-lang.org/std/autodiff/attr.autodiff_forward.html)
- [`autodiff_reverse`](https://doc.rust-lang.org/std/autodiff/attr.autodiff_reverse.html)

<!-- END AUTO ITEMS -->
