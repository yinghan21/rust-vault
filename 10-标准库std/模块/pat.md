---
title: "std::pat"
type: std-模块
module: pat
stable: ""
unstable: true
tags:
  - std/模块
aliases:
  - pat
一句话: 导出 `pattern_type` 宏的辅助模块，宏的作用是创建一个 pattern type。
---

# std::pat

> [!warning] 实验性模块
> 该模块需要 nightly 工具链，并通过 `#![feature(...)]` 启用，API 可能随时变化，**不要用于生产代码**。

## 模块简介

`std::pat` 是一个很小的辅助模块，官方模块页只有一句「Helper module for exporting the `pattern_type` macro」——它存在的意义就是把 `pattern_type` 宏重新导出到 `std::` 命名空间下。宏本身的功能同样只有一句说明：创建一个 pattern type；至于 pattern type 在类型系统里承担什么角色、能用在哪些位置，模块页并没有展开，实际形状要等这项特性成型后才清楚。

## 主要条目
`pattern_type`（宏），共 1 项。

## 相关

- [[模块索引]]
- [[view|std::view 模块]]：另一个只导出一个宏的同类辅助模块。
- [[from|std::from 模块]]：同样以承载单个实验性宏为目的。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 1 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 宏

- [`pattern_type`](https://doc.rust-lang.org/std/pat/macro.pattern_type.html)

<!-- END AUTO ITEMS -->
