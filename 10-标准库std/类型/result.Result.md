---
title: "std::result::Result"
type: std-条目
kind: 枚举
module: result
slug: result.Result
stable: "1.0.0"
tags:
  - std/类型
  - std/错误
aliases:
  - Result
一句话: 表示一次操作「成功 Ok」或「失败 Err」的枚举，是 Rust 错误处理的核心类型。
---

# `Result<T, E>`

> [!abstract] 一句话
> `Result<T, E>` 用两个变体区分结果：`Ok(T)` 带成功值，`Err(E)` 带错误值；凡是有可能失败的操作都返回它。

## 简介

`Result` 是 Rust 表达「可失败操作」的标准方式。它不是异常机制：失败是**返回值的一部分**，编译器会强制你在使用 `Ok` 里的值之前先处理 `Err` 分支。

- `Ok(T)`：操作成功，内含结果值 `T`。
- `Err(E)`：操作失败，内含错误值 `E`。

与 [[option.Option|Option]] 的区别：`Option` 只说「有没有」，`Result` 还能说「为什么没有」。所以「没找到」这类无原因的场景用 `Option`，「I/O 出错、解析失败」这类需要原因的场景用 `Result`。

`Result` 也有 `#[must_use]` 标记，忽略返回值时编译器会警告；这正是它比 C 的「返回 -1 表示出错」更安全的地方。错误类型可以是任何类型：字符串、枚举、实现了 [[error.Error|Error]] 的结构体，或者 `Box<dyn Error>`。

## 变体

| 变体 | 含义 |
| --- | --- |
| `Ok(T)` | 成功，内含结果值 `T`。 |
| `Err(E)` | 失败，内含错误值 `E`。 |

## 常用方法

### 判断与借用

| 方法 | 说明 |
| --- | --- |
| `is_ok()` | 判断是否为 `Ok`，不取出内部值。 |
| `is_ok_and(f)` | 判断是否为 `Ok` 且内部值满足谓词。 |
| `is_err()` | 判断是否为 `Err`，不取出内部值。 |
| `is_err_and(f)` | 判断是否为 `Err` 且错误值满足谓词。 |
| `ok()` | 丢弃错误，把 `Ok` 的值转为 `Option<T>`。 |
| `err()` | 丢弃成功值，把 `Err` 的值转为 `Option<E>`。 |
| `as_ref()` | 借用内部值，得到 `Result<&T, &E>`。 |
| `as_mut()` | 可变借用内部值，得到 `Result<&mut T, &mut E>`。 |
| `as_deref()` | 对内部值做一次 `Deref` 后再借用。 |
| `as_deref_mut()` | 对内部值做一次 `DerefMut` 后再可变借用。 |

### 映射与检查

| 方法 | 说明 |
| --- | --- |
| `map(op)` | 只在 `Ok` 时映射值，`Err` 原样保留。 |
| `map_or(default, f)` | `Ok` 时映射，`Err` 时返回给定默认值。 |
| `map_or_else(default, f)` | 用两个闭包分别处理 `Err` 与 `Ok`。 |
| `map_or_default(f)` | `Ok` 时映射，`Err` 时返回 `U::default()`。 |
| `map_err(op)` | 只在 `Err` 时映射错误，`Ok` 原样保留。 |
| `inspect(f)` | 在 `Ok` 时用引用调用闭包，值不变。 |
| `inspect_err(f)` | 在 `Err` 时用引用调用闭包，值不变。 |
| `copied()` | 复制引用中的值，得到 `Result<T, E>`。 |
| `cloned()` | 克隆引用中的值，得到 `Result<T, E>`。 |

### 取值与解包

| 方法 | 说明 |
| --- | --- |
| `expect(msg)` | 取出 `Ok` 值，`Err` 时 panic 并附消息。 |
| `unwrap()` | 取出 `Ok` 值，`Err` 时直接 panic。 |
| `unwrap_or(default)` | 取出 `Ok` 值，`Err` 时返回给定默认值。 |
| `unwrap_or_default()` | 取出 `Ok` 值，`Err` 时返回 `T::default()`。 |
| `unwrap_or_else(op)` | 取出 `Ok` 值，`Err` 时调用闭包计算。 |
| `expect_err(msg)` | 取出 `Err` 值，`Ok` 时 panic 并附消息。 |
| `unwrap_err()` | 取出 `Err` 值，`Ok` 时直接 panic。 |
| `unwrap_unchecked()` | 取出 `Ok` 值，跳过检查（`unsafe`）。 |
| `unwrap_err_unchecked()` | 取出 `Err` 值，跳过检查（`unsafe`）。 |

### 组合与结构变换

| 方法 | 说明 |
| --- | --- |
| `and(res)` | `Ok` 时返回 `res`，否则返回自身的 `Err`。 |
| `and_then(op)` | `Ok` 时调用闭包，继续返回一个 `Result`。 |
| `or(res)` | `Err` 时返回 `res`，否则返回自身的 `Ok`。 |
| `or_else(op)` | `Err` 时调用闭包，继续返回一个 `Result`。 |
| `iter()` | 迭代零个或一个 `Ok` 值的引用。 |
| `iter_mut()` | 可变迭代零个或一个 `Ok` 值。 |
| `transpose()` | 交换 `Result` 与 `Option` 的嵌套层级。 |
| `flatten()` | 把嵌套两层的 `Result` 压平成一层。 |

## 示例

```rust
use std::result::Result;

// 把字符串解析成正整数，失败时用 String 说明原因
fn parse_positive(text: &str) -> Result<u32, String> {
    match text.parse::<u32>() {
        Ok(n) if n > 0 => Ok(n),
        Ok(_) => Err(String::from("必须是正整数")),
        Err(_) => Err(format!("无法解析：{text}")),
    }
}

fn main() {
    // map 只变换成功值
    let doubled = parse_positive("21").map(|n| n * 2);
    assert_eq!(doubled, Ok(42));

    // map_err 只变换错误值
    let mapped = parse_positive("abc").map_err(|e| format!("解析失败：{e}"));
    assert_eq!(mapped, Err(String::from("解析失败：无法解析：abc")));

    // unwrap_or 与 unwrap_or_else 提供兜底值
    assert_eq!(parse_positive("0").unwrap_or(1), 1);
    assert_eq!(parse_positive("x").unwrap_or_else(|_| 99), 99);

    // and_then 串联两个都可能失败的步骤
    let total = parse_positive("8").and_then(|n| parse_positive(&(n * 10).to_string()));
    assert_eq!(total, Ok(80));

    // transpose 在 Result 与 Option 之间调换嵌套顺序
    let nested: Result<Option<u32>, String> = Ok(Some(5));
    assert_eq!(nested.transpose(), Some(Ok(5)));

    println!("全部断言通过");
}
```

## 常见陷阱

1. **对 `Err` 调用 `unwrap()` 会 panic**：调试可以，生产代码里应该用 `?`、`unwrap_or` 或 `match` 显式处理。对策：把 `unwrap()` 当作「这里不可能失败」的断言来用。
2. **`ok()` 会静默丢掉错误信息**：`result.ok()` 只留下成功值，出错原因就查不到了。对策：需要日志或诊断时改用 `map_err` 保留原因。
3. **用 `?` 的函数返回类型必须匹配**：`?` 要求当前函数的返回类型是 `Result`（或 `Option`），否则编译报错。对策：让函数返回 `Result<T, Box<dyn std::error::Error>>` 或自定义错误类型。
4. **`unwrap_err()` 要求 `T: Debug`**：成功值不可打印时无法编译。对策：改用 `match`，或用 `is_err()` 判断后手动取值。
5. **`Result` 不是异常**：不会跨栈自动传播，也不会被 `catch` 捕获 panic。对策：层层用 `?` 向上传递，最后在 `main` 或请求入口统一处理。

## 相关

- [[result|std::result 模块]]：`Result` 与 `Iter`、`IterMut` 等配套类型。
- [[option.Option|Option]]：只表示「有无」，不携带失败原因。
- [[error.Error|Error]]：自定义错误类型通常实现这个特质。
- [[11-错误处理|错误处理]]：`?`、错误转换与错误类型的实战讲法。
- [[convert.TryFrom|TryFrom]]：可失败转换返回的就是 `Result`。
