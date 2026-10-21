---
title: "std::from"
type: std-模块
module: from
stable: ""
unstable: true
tags:
  - std/模块
aliases:
  - from
一句话: 承载实验性 `#[derive(From)]` 派生宏的模块，目前只能用在单字段结构体上。
---

# std::from

> [!warning] 实验性模块
> 该模块需要 nightly 工具链，并通过 `#![feature(...)]` 启用，API 可能随时变化，**不要用于生产代码**。

## 模块简介

`std::from` 是一个不稳定模块，唯一用途是承载同样不稳定的 `From` derive 宏：它生成 `From` trait 的实现，按官方说明目前只能用于单字段结构体（newtype 形式）。稳定版里，`From` 仍要靠手写 `impl From<A> for B` 或调用 `From::from` 完成转换；派生版本的入口与可用范围都还在调整，写代码时不要依赖它。

## 主要条目
`From`（派生宏），共 1 项。

## 相关

- [[模块索引]]
- [[convert|std::convert 模块]]：`From` / `Into` / `TryFrom` 这些转换 trait 的家。
- [[convert.From|From]]：稳定的转换 trait 本身，日常写法以它为准。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 1 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 其他

- [`From`](https://doc.rust-lang.org/std/from/derive.From.html)

<!-- END AUTO ITEMS -->
