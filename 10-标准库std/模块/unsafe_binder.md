---
title: "std::unsafe_binder"
type: std-模块
module: unsafe_binder
stable: ""
unstable: true
tags:
  - std/模块
aliases:
  - unsafe_binder
一句话: 把类型包装成 unsafe binder 再拆开的运算符：`wrap_binder!` 与 `unwrap_binder!`。
---

# std::unsafe_binder

> [!warning] 实验性模块
> 该模块需要 nightly 工具链，并通过 `#![feature(...)]` 启用，API 可能随时变化，**不要用于生产代码**。

## 模块简介

`std::unsafe_binder` 定义一组「运算符」，用来把类型变成 unsafe binder、再从 binder 变回原类型：`wrap_binder!` 负责包装，`unwrap_binder!` 负责拆开还原。官方模块页目前只有这一句概括，binder 在类型系统里确切表示什么、会出现在哪些接口中，都没有更细的说明；模块仍停留在 nightly，整体设计还有可能重做。

## 主要条目
`wrap_binder`（宏）、`unwrap_binder`（宏），共 2 项。

## 相关

- [[模块索引]]
- [[24-unsafe 与 FFI|unsafe 与 FFI]]：`unsafe` 契约与前置条件的基本概念。
- [[ptr|std::ptr 模块]]：另一类「安全性由调用者保证」的底层接口。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 2 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 宏

- [`unwrap_binder`](https://doc.rust-lang.org/std/unsafe_binder/macro.unwrap_binder.html)
- [`wrap_binder`](https://doc.rust-lang.org/std/unsafe_binder/macro.wrap_binder.html)

<!-- END AUTO ITEMS -->
