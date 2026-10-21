---
title: "std::field"
type: std-模块
module: field
stable: ""
unstable: true
tags:
  - std/模块
aliases:
  - field
一句话: 字段反射：用 `Field` 与 `field_of!` 在类型层面表示结构体、联合体、枚举变体或元组中的某个字段。
---

# std::field

> [!warning] 实验性模块
> 该模块需要 nightly 工具链，并通过 `#![feature(...)]` 启用，API 可能随时变化，**不要用于生产代码**。

## 模块简介

`std::field` 做的是字段层面的反射（Field Reflection）：`Field` trait 的类型代表 `struct`、`union`、枚举变体或元组里的一个字段，`FieldRepresentingType` 是与它配套的「字段表示类型」结构体，`field_of!` 宏展开后得到给定字段对应的表示类型。拿到表示类型之后，字段偏移量与字段名等信息由 `std::intrinsics` 中的 `field_offset`、`field_representing_type_name` 等内建函数提供。普通业务代码一般用不到这一层，它主要服务于标准库自身与需要按字段做泛型操作的场景。

## 主要条目
`field_of`（宏）、`FieldRepresentingType`（结构体）、`Field`（特质），共 3 项。

## 相关

- [[模块索引]]
- [[intrinsics|std::intrinsics 模块]]：字段偏移与字段名等内建函数都在这里。
- [[any|std::any 模块]]：`TypeId` 与运行时类型识别，字段反射的另一半基础。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 3 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`FieldRepresentingType`](https://doc.rust-lang.org/std/field/struct.FieldRepresentingType.html)

### 特质

- [`Field`](https://doc.rust-lang.org/std/field/trait.Field.html)

### 宏

- [`field_of`](https://doc.rust-lang.org/std/field/macro.field_of.html)

<!-- END AUTO ITEMS -->
