---
title: "std::default::Default"
type: std-条目
kind: 特质
module: default
slug: default.Default
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - Default
一句话: 无参构造的通用入口，为类型提供一个合理起点，被 unwrap_or_default、or_default、mem::take 等广泛依赖。
---

# Default

> [!abstract] 一句话
> `Default` 规定「不给任何输入时该怎么造一个值」：`T::default()` 是标准库统一的无参构造入口，`unwrap_or_default`、`or_default`、`mem::take`、结构体更新语法都靠它。

## 简介

`Default` 只定义一件事：`fn default() -> Self`。它描述的是**一个合理的起点**，而不是「空值」或「缺失」——一个 `i32` 的默认值是 `0`，一个 `Config` 的默认值是一组可用的配置，两者都是完整的、立即可用的值。

它的核心价值在于「泛型代码需要一个类型能自己构造自己」。下面这些标准库 API 都以 `T: Default` 为约束，写代码时会不期而遇：

- `Option::unwrap_or_default`、`Result::unwrap_or_default`：拿不到值时退回默认值。
- `Entry::or_default`：`HashMap`/`BTreeMap` 的入口，键不存在时插入默认值。
- `std::mem::take`：用一个默认值换走原值，把「移动」变成「先占位再拿走」。
- 结构体更新语法 `Foo { a: 1, ..Default::default() }`：只覆盖关心的字段。
- `#[derive(Default)]`：逐字段调用 `Field::default()`。

设计上要注意区分：`Default` 表示「有意义的缺省」，`Option` 表示「可能没有」。凡是「没有」也是一种合法状态的地方，应该用 `Option<T>` 而不是让 `Default` 兼任。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `default()` | 返回该类型的默认值。 |

签名是 `fn default() -> Self`。它不接收任何参数，也不该有副作用之外的惊喜：同一个类型反复调用 `default()` 应该得到等价的值。

## 与相邻 trait 的关系

| 维度 | `Default` | `Clone` |
| --- | --- | --- |
| 输入 | 不需要任何东西 | 需要一份已有的值 |
| 语义 | 造一个通用起点 | 复制一份特定内容 |
| 典型用途 | 泛型代码要「能空构造」 | 泛型代码要「能复制」 |
| 关系 | 与 `Clone` 无继承关系 | 与 `Default` 无继承关系 |

`Default` 与 `From<()>` 表达相近的「无参构造」，但标准库只为 `Default` 提供统一入口和上述一整套便利 API，所以习惯上应实现 `Default`。另外 `Default` 常与 [[mem.take|take]] 搭配：`take` 要求 `T: Default`，它先把 `*dest` 换成默认值，再把原值返回，从而实现「借用中取走所有权」。

## 示例

### derive 得到逐字段默认值

```rust
#[derive(Default, Debug, PartialEq)]
struct Config {
    retries: u32,
    verbose: bool,
    name: String,
}

fn main() {
    let cfg = Config::default();

    // 每个字段各自取自己的默认值：0、false、空字符串
    assert_eq!(cfg.retries, 0);
    assert!(!cfg.verbose);
    assert!(cfg.name.is_empty());
    assert_eq!(cfg, Config { retries: 0, verbose: false, name: String::new() });
    println!("{cfg:?}");
}
```

### 手写 `Default` 配合结构体更新语法

```rust
#[derive(Debug, Clone)]
struct Window {
    width: u32,
    height: u32,
    title: String,
}

impl Default for Window {
    fn default() -> Self {
        Window {
            width: 800,
            height: 600,
            title: String::from("未命名"),
        }
    }
}

fn main() {
    // 只覆盖关心的字段，其余走默认值
    let big = Window { width: 1920, ..Default::default() };
    assert_eq!(big.width, 1920);
    assert_eq!(big.height, 600);
    assert_eq!(big.title, "未命名");

    // 基本类型也实现了 Default
    assert_eq!(u8::default(), 0u8);
    assert_eq!(f64::default(), 0.0);
}
```

### 枚举用 `#[default]` 指定默认变体

```rust
#[derive(Default, Debug, PartialEq)]
enum Mode {
    Fast,
    #[default]
    Balanced,
    Precise,
}

fn main() {
    // 枚举必须显式标注哪个单位变体是默认值
    assert_eq!(Mode::default(), Mode::Balanced);
}
```

### 与标准库 API 配合

```rust
use std::collections::BTreeMap;

fn main() {
    // 解析失败时退回 i32 的默认值 0
    let n: i32 = "abc".parse().unwrap_or_default();
    assert_eq!(n, 0);

    // 键不存在时插入 u32::default() 再累加
    let mut counts: BTreeMap<&str, u32> = BTreeMap::new();
    for word in ["a", "b", "a"] {
        *counts.entry(word).or_default() += 1;
    }
    assert_eq!(counts["a"], 2);

    // mem::take 用默认值换走原值
    let mut name = String::from("hello");
    let taken = std::mem::take(&mut name);
    assert_eq!(taken, "hello");
    assert!(name.is_empty());
}
```

## 常见陷阱

1. **`#[derive(Default)]` 直接用在枚举上**：编译器不知道选哪个变体，报错；必须给某个单位变体标 `#[default]`（Rust 1.62 起支持）。
2. **把 `Default` 当作「空值」**：`0`、`false`、空串往往也是合法数据，无法区分「没设置」。需要「没有」时用 [[option.Option|Option]]。
3. **默认值里做重活**：`Vec::default()`、`String::default()` 都不分配内存，若自定义 `Default` 里塞了 `vec![0; 1 << 20]`，每次空构造都要付这笔代价。
4. **结构体更新语法位置写错**：`..Default::default()` 必须放在最后，写在字段中间会解析失败。
5. **泛型结构体 derive 出的约束过强**：`#[derive(Default)]` 会生成 `impl<T: Default> Default for Wrapper<T>`；如果字段是 `Option<T>`，手写 `impl<T> Default for Wrapper<T>` 才能对任意 `T` 成立。

## 相关

- [[default|std::default 模块]]：`Default` 所属模块。
- [[clone.Clone|Clone]]：另一个「从已有值造新值」的特质。
- [[mem.take|take]]：要求 `T: Default` 的所有权搬移工具。
- [[mem.replace|replace]]：与 `take` 同族的替换函数。
- [[option.Option|Option]]：表示「缺失」的正规手段，别用 `Default` 顶替。
- [[14-泛型|泛型]]：`T: Default` 这类约束的用法。
