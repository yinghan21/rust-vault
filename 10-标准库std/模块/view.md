---
title: "std::view"
type: std-模块
module: view
stable: ""
unstable: true
tags:
  - std/模块
aliases:
  - view
一句话: 导出 `view_type` 宏的辅助模块，宏的作用是创建一个 view type。
---

# std::view

> [!warning] 实验性模块
> 该模块需要 nightly 工具链，并通过 `#![feature(...)]` 启用，API 可能随时变化，**不要用于生产代码**。

## 模块简介

`std::view` 与 `std::pat` 属于同一类东西：一个用于导出宏的辅助模块，作用是把 `view_type` 宏暴露到 `std::` 下，官方原话是「Helper module for exporting the `view_types` macro」。宏本身只有一句说明——创建一个 view type；view type 用来做什么、与字段反射或模式类型之间是什么关系，模块页都没有展开，只能等这项特性稳定后再补充。

## 主要条目
`view_type`（宏），共 1 项。

## 相关

- [[模块索引]]
- [[pat|std::pat 模块]]：只导出单个宏的同类辅助模块，可对照着看。
- [[field|std::field 模块]]：另一个在类型层面描述结构体内某一部分的实验性模块。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 1 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 宏

- [`view_type`](https://doc.rust-lang.org/std/view/macro.view_type.html)

<!-- END AUTO ITEMS -->
