---
title: "std::random"
type: std-模块
module: random
stable: ""
unstable: true
tags:
  - std/模块
aliases:
  - random
一句话: 随机值生成：`Rng` 随机源、`SystemRng` 系统发生器与 `Distribution` 分布接口。
---

# std::random

> [!warning] 实验性模块
> 该模块需要 nightly 工具链，并通过 `#![feature(...)]` 启用，API 可能随时变化，**不要用于生产代码**。

## 模块简介

`std::random` 负责随机值生成，目前提供两个底层接口：`Rng` 表示一个随机源，`SystemRng` 是系统随机数发生器；`Distribution` trait 描述某个类型的随机值分布，函数 `random` 则用默认随机源按给定分布产出一个值。官方说明提到，将来可能再补一层高层接口（例如分布采样）；在那之前，用 `fill_bytes` 填好字节再构造其它类型时，要自己避免采样偏差——把无约束的随机数直接取模压进某个区间就是典型的不当做法。

## 主要条目
`SystemRng`（结构体）、`Rng`（特质）、`Distribution`（特质）、`random`（函数），共 4 项。

## 相关

- [[模块索引]]
- [[num|std::num 模块]]：随机整数常与这些数值类型、非零类型一起用。
- [[hash|std::hash 模块]]：同样围绕「难以预测的数值」做文章的哈希器。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 4 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`SystemRng`](https://doc.rust-lang.org/std/random/struct.SystemRng.html)

### 特质

- [`Distribution`](https://doc.rust-lang.org/std/random/trait.Distribution.html)
- [`Rng`](https://doc.rust-lang.org/std/random/trait.Rng.html)

### 函数

- [`random`](https://doc.rust-lang.org/std/random/fn.random.html)

<!-- END AUTO ITEMS -->
