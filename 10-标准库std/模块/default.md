---
title: "std::default"
type: std-模块
module: default
stable: "1.0.0"
unstable: false
tags:
  - std/模块
  - std/特质
aliases:
  - default
  - 默认值
一句话: `Default` 特质：为类型定义一个合理的默认值，并可用派生宏自动生成。
---

# std::default

> [!abstract] 一句话
> `std::default` 只有两件事：`Default` 特质和 `#[derive(Default)]` 派生宏，用于获取类型的默认值。

## 模块简介

`Default` 回答的是「这个类型最合理的初始值是什么」。它由类型作者定义，不是内存零值：`Vec` 的默认值是空向量，`String` 是空字符串，`bool` 是 `false`，数值类型是 `0`，`Option` 是 `None`。

最常见的用法是派生加结构体更新语法：只设置关心的字段，其余字段用 `..Default::default()` 补齐。这在配置结构体、builder 模式、测试夹具里非常省事，也让结构体新增字段时不必改遍所有构造点。

另一类用法是泛型约束。容器与集合的构造、`mem::take`、`Option::unwrap_or_default` 都依赖 `T: Default`；写泛型代码时加上这个约束，调用方就能用标准库类型直接实例化。

`Default` 在 prelude 中，不需要 `use`。派生的规则是按字段类型逐个调用 `default()`，字段顺序无关；枚举派生时需要标出 `#[default]` 的那个变体。

## 快速上手

```rust
#[derive(Debug, Default, PartialEq)]
struct Config {
    retries: u32,
    verbose: bool,
    name: String,
}

fn main() {
    // 所有字段取各自的默认值
    let c = Config::default();
    assert_eq!(
        c,
        Config {
            retries: 0,
            verbose: false,
            name: String::new(),
        }
    );

    // 只覆盖关心的字段，其余用默认值补齐
    let custom = Config {
        retries: 3,
        ..Default::default()
    };
    assert_eq!(custom.retries, 3);
    assert!(!custom.verbose);

    // 标准库类型都实现了 Default
    let v: Vec<i32> = Default::default();
    assert!(v.is_empty());
    let opt: Option<i32> = Default::default();
    assert_eq!(opt, None);

    // 泛型函数可以要求 T: Default
    fn make<T: Default>() -> T {
        T::default()
    }
    assert_eq!(make::<u8>(), 0);
    assert_eq!(make::<String>(), "");
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[default.Default|Default]] | 提供默认值的特质，核心方法是 `default`。 |
| `Default::default` | 返回该类型的默认值。 |
| `#[derive(Default)]` | 为结构体或枚举逐字段生成默认实现。 |
| `..Default::default()` | 结构体更新语法，只覆盖部分字段。 |
| `Option::default` | 默认值是 `None`。 |
| `Vec::default` / `String::default` | 默认值是空的容器。 |
| `HashMap::default` | 空映射，等价于 `HashMap::new()`。 |
| `bool::default` | 默认值是 `false`。 |
| `u32::default` | 数值类型的默认值是 `0`。 |
| `#[default]` 变体标记 | 枚举派生 `Default` 时指定默认变体。 |
| `T: Default` 约束 | 泛型代码要求类型可构造默认值。 |

## 注意事项

> [!warning] 默认值不等于零值
> `Default` 由实现者决定语义，标准库类型也各有含义（`Option` 是 `None`、`Vec` 是空）。给自定义类型手写实现时，选一个对调用方真正有用的初始状态。

> [!danger] 枚举派生需要 `#[default]`
> 枚举不能像结构体那样自动选择默认变体，必须在某个单元变体上标 `#[default]`，否则派生会编译失败；带字段的变体不能这样标记。

> [!tip] 与结构体更新语法搭配
> `..Default::default()` 让「只改几个字段」的构造保持可读；给结构体加字段时，旧的构造点通常不用改。

## 相关

- [[default.Default|Default]]：本模块的核心特质。
- [[clone|std::clone 模块]]：`Clone` 与 `Default` 常一起派生。
- [[option|std::option 模块]]：`unwrap_or_default` 依赖 `Default`。
- [[07-结构体|结构体]]：结构体更新语法与字段默认值。
- [[15-trait 基础|trait 基础]]：为自己类型实现 `Default`。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 2 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 特质

- [[default.Default|`Default`]]

### 其他

- [[default.Default|`Default`]]

<!-- END AUTO ITEMS -->
