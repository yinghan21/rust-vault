---
title: "std::async_iter"
type: std-模块
module: async_iter
stable: ""
unstable: true
tags:
  - std/模块
aliases:
  - async_iter
一句话: 组合式异步迭代：`AsyncIterator` 及把普通迭代器转成异步迭代器的配套工具。
---

# std::async_iter

> [!warning] 实验性模块
> 该模块需要 nightly 工具链，并通过 `#![feature(...)]` 启用，API 可能随时变化，**不要用于生产代码**。

## 模块简介

`std::async_iter` 是异步版的迭代器模块：当手上有一个「异步地逐个产出元素」的集合，又需要对其中元素做组合式处理时，就会用到异步迭代器，官方文档指出这类接口在惯用的异步 Rust 代码中使用很广。模块按类型组织：核心是 `AsyncIterator` trait，`IntoAsyncIterator` 负责把一个值转成异步迭代器，`FromIter` 与 `from_iter` 则把普通迭代器包装成异步迭代器。整块内容仍在 nightly，接口形状还可能调整。

## 主要条目
`FromIter`（结构体）、`AsyncIterator`（特质）、`IntoAsyncIterator`（特质）、`from_iter`（函数），共 4 项。

## 相关

- [[模块索引]]
- [[iter|std::iter 模块]]：同步版迭代器，两者的组合子设计一脉相承。
- [[future|std::future 模块]]：异步迭代器每次产出都要 `await`，与 `Future` 配合使用。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 4 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`FromIter`](https://doc.rust-lang.org/std/async_iter/struct.FromIter.html)

### 特质

- [`AsyncIterator`](https://doc.rust-lang.org/std/async_iter/trait.AsyncIterator.html)
- [`IntoAsyncIterator`](https://doc.rust-lang.org/std/async_iter/trait.IntoAsyncIterator.html)

### 函数

- [`from_iter`](https://doc.rust-lang.org/std/async_iter/fn.from_iter.html)

<!-- END AUTO ITEMS -->
