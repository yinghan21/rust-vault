---
title: "std::bstr"
type: std-模块
module: bstr
stable: ""
unstable: true
tags:
  - std/模块
aliases:
  - bstr
一句话: `ByteStr` 与 `ByteString`：把「可能、但不保证是 UTF-8」的字节序列当作字符串处理。
---

# std::bstr

> [!warning] 实验性模块
> 该模块需要 nightly 工具链，并通过 `#![feature(...)]` 启用，API 可能随时变化，**不要用于生产代码**。

## 模块简介

`std::bstr` 提供两个类型：`ByteStr` 包装 `&[u8]`，`ByteString` 包装 `Vec<u8>`，二者都表示「人类可读、习惯上但不总是 UTF-8」的字符串。处理来自文件、网络或外部系统的字节时，往往无法先验地保证编码是 UTF-8，这两个类型让这类数据仍能按字符串的方式对待。官方模块页只有一句说明，具体方法与 trait 实现都在两个类型各自的文档里。

## 主要条目
`ByteStr`（结构体）、`ByteString`（结构体），共 2 项。

## 相关

- [[模块索引]]
- [[str|std::str 模块]]：要求合法 UTF-8 的字符串切片。
- [[string|std::string 模块]]：可增长的 UTF-8 字符串。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 2 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`ByteStr`](https://doc.rust-lang.org/std/bstr/struct.ByteStr.html)
- [`ByteString`](https://doc.rust-lang.org/std/bstr/struct.ByteString.html)

<!-- END AUTO ITEMS -->
