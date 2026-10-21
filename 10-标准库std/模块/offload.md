---
title: "std::offload"
type: std-模块
module: offload
stable: ""
unstable: true
tags:
  - std/模块
aliases:
  - offload
一句话: 把 kernel 卸载到 GPU 一类设备上执行的实验性支持，由 `offload!` 与 `#[offload_kernel]` 两个宏组成。
---

# std::offload

> [!warning] 实验性模块
> 该模块需要 nightly 工具链，并通过 `#![feature(...)]` 启用，API 可能随时变化，**不要用于生产代码**。

## 模块简介

`std::offload` 提供把计算卸载到 GPU 一类设备上的支持：`#[offload_kernel]` 属性宏作用于一个函数，为它生成宿主侧负责分发的包装函数和设备侧的 kernel 两份定义；`offload!` 宏负责发起一次 kernel 启动，可以指定目标 kernel、workgroup 与线程维度，以及要转发到设备的参数。底层对应的内建函数是 `intrinsics::offload`，它生成包装函数的 LLVM 代码，精确语义见两个宏各自的文档。

## 主要条目
`offload`（宏）、`offload_kernel`（属性宏），共 2 项。

## 相关

- [[模块索引]]
- [[intrinsics|std::intrinsics 模块]]：`intrinsics::offload` 是这套宏的底层入口。
- [[autodiff|std::autodiff 模块]]：同样靠属性宏在编译期生成代码的实验性能力。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 2 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 宏

- [`offload`](https://doc.rust-lang.org/std/offload/macro.offload.html)

### 其他

- [`offload_kernel`](https://doc.rust-lang.org/std/offload/attr.offload_kernel.html)

<!-- END AUTO ITEMS -->
