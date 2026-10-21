---
title: "std::primitive::bool"
type: std-条目
kind: 原始类型
module: bool
slug: primitive.bool
stable: "1.0.0"
tags:
  - std/类型
  - rust/基础
aliases:
  - bool
一句话: 只有 true 与 false 两个值的布尔类型，用于条件判断、逻辑运算和断言。
---

# `bool`

> [!abstract] 一句话
> `bool` 只有 `true` 和 `false` 两个值，固定占 1 字节；它**不能当整数用**，`if` 的条件也必须是 `bool`。

## 简介

`bool` 是语言内建的布尔类型，值域只有 `true` 与 `false`，`size_of::<bool>()` 为 1 字节。`if`、`while`、`match` 守卫和 [[macro.assert|assert!]] 都要求条件表达式是 `bool`，不存在 C 语言里「非零即真」的隐式转换。

- **不能当整数用**：`let x: i32 = true;` 和 `if 1 { }` 都编译失败。`bool` 转整数要显式写 `true as i32`（得到 1）或 `false as u8`（得到 0）；反方向没有 `as` 转换，只能写 `n != 0`。
- **逻辑运算分两种**：`&&`、`||`、`!` 是短路逻辑运算，右侧不一定会求值；`&`、`|`、`^` 走 `BitAnd` / `BitOr` / `BitXor`，两侧都会求值。
- **比较产生 `bool`**：`==`、`!=`、`<`、`>` 以及 `Option::is_some()` 这类判断方法都返回 `bool`，可以直接喂给 `if`。
- **只占 1 字节但不会打包**：`bool` 是 1 字节而不是 1 bit，`Vec<bool>` 也不做位压缩。
- 4 个稳定方法都用来把「条件」转成 [[option.Option|Option]] 或 [[result.Result|Result]]，适合在链式调用里替代 `if`。

## 常用方法

共 4 个稳定方法。

| 方法 | 说明 |
| --- | --- |
| `then_some(t)` | `true` 时返回 `Some(t)`，否则 `None`。 |
| `then(f)` | `true` 时调用 `f` 并返回 `Some(f())`。 |
| `ok_or(err)` | `true` 时返回 `Ok(())`，否则 `Err(err)`。 |
| `ok_or_else(f)` | `true` 时返回 `Ok(())`，否则 `Err(f())`。 |

> [!tip] `then_some` 与 `then` 的求值时机不同
> `then_some(t)` 的实参在调用前就已求值，`then(f)` 只在 `true` 时才调用 `f`。构造代价高或带副作用时选 `then`；`ok_or` 与 `ok_or_else` 同理。

## 示例

### 条件与短路

```rust
fn main() {
    let enabled = true;

    // 把条件转成 Option：then_some 立即求值，then 惰性求值
    assert_eq!(enabled.then_some(42), Some(42));
    assert_eq!(false.then(|| 42), None);

    // && 短路：右侧的自增不会执行
    let mut hits = 0;
    let short = false && {
        hits += 1;
        true
    };
    assert!(!short);
    assert_eq!(hits, 0);

    // & 不短路：两侧都会求值
    let non_short = false & {
        hits += 1;
        true
    };
    assert!(!non_short);
    assert_eq!(hits, 1);

    // 转整数必须显式 as，反向只能比较
    assert_eq!(true as u8, 1);
    assert_eq!(false as u8, 0);
    assert!(1 != 0);
}
```

### 条件转 `Result`

```rust
fn main() {
    let passed = true;

    // ok_or 直接给出错误值
    let checked: Result<(), &str> = passed.ok_or("未通过");
    assert!(checked.is_ok());

    // ok_or_else 在失败时才构造错误值
    let missing: Result<(), String> = false.ok_or_else(|| String::from("未通过"));
    assert_eq!(missing.unwrap_err(), "未通过");
}
```

### 模式匹配布尔值

```rust
fn main() {
    let flag = true;

    // match 可以直接匹配 true / false，但简单分支写成 if 更直观
    match flag {
        true => assert_eq!(flag as i32, 1),
        false => assert_eq!(flag as i32, 0),
    }
}
```

## 常见陷阱

1. **不能隐式当整数**：`if 1 { }`、`let x: i32 = true;`、`assert_eq!(true, 1)` 都编译失败；整数转 `bool` 只能写 `n != 0`。
2. **`&&` 与 `&` 混用**：`&&` 短路，`&` 两侧都求值。右侧有副作用、可能 panic 或开销大时用 `&&`，否则可能白算一次。
3. **`then_some` 不会延迟求值**：`false.then_some(heavy())` 依然会调用 `heavy()`；要惰性求值用 `then`。
4. **`Vec<bool>` 不省内存**：每个 `bool` 仍是 1 字节，不做位压缩；需要位图请改用 `u8` 数组。
5. **`ok_or` 立即构造错误值**：错误值昂贵时用 `ok_or_else`，避免成功路径也付出构造开销。

## 相关

- [[option.Option|Option]]：`then`、`then_some` 的返回类型。
- [[result.Result|Result]]：`ok_or`、`ok_or_else` 的返回类型。
- [[primitive.char|Type char]]：另一个最常用的原始类型。
- [[primitive|std::primitive]]：`bool` 所属的原始类型模块。
- [[08-枚举与模式匹配|模式匹配]]：`match` 可直接匹配 `true` / `false`。
- [[03-变量与数据类型|变量与数据类型]]：布尔值、整数与类型转换的基础。
