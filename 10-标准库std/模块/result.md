---
title: "std::result"
type: std-模块
module: result
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - result
一句话: "可恢复错误的载体 Result<T, E>：Ok 带成功值、Err 带错误值，配合 ? 传播。"
---

# std::result

> [!abstract] 一句话
> `std::result` 定义 [[result.Result|Result]]——`Ok(T)` 表示成功、`Err(E)` 表示失败——它是 Rust 全部可恢复错误处理的入口。

## 模块简介

`Result<T, E>` 是一个只有两个变体的枚举：`Ok(T)` 包住成功时产出的值，`Err(E)` 包住失败时的错误值。函数**预期可能失败且失败可恢复**时，返回 `Result` 而不是直接 panic；真正无法继续的逻辑错误才用 `panic!` / `assert!`。标准库里最典型的用法是 I/O：`fs::read_to_string`、`TcpStream::connect` 都返回 `io::Result<T>`，也就是 `Result<T, std::io::Error>`。

把错误建模成普通值，好处是编译器知道「这里可能没结果」，调用者必须显式处理——漏掉 `Err` 分支就是编译错误，而不是线上的空指针。`Result` 的 `E` 是任意类型：解析用 `ParseIntError`，I/O 用 `io::Error`，自定义函数可以返回自己的错误枚举。想让错误类型「什么都能装」，用 `Box<dyn std::error::Error>` 或 `String`。

`?` 运算符是这套设计的核心：`expr?` 在 `Ok` 时取出内部值继续往下走，在 `Err` 时立刻 `return Err(...)`，并通过 `From` 自动把底层错误转换成函数声明的错误类型。于是一串「打开文件 → 读文本 → 解析数字 → 计算」可以写成一条直线，不用一层层 `match` 嵌套。约束是：`?` 只能出现在返回 `Result`（或 `Option`）的函数里。

这个模块本身很小：枚举 `Result`、三个迭代器（`Iter`、`IterMut`、`IntoIter`，分别由 `iter`、`iter_mut`、`into_iter` 得到）。绝大多数能力挂在 [[result.Result|Result]] 自己的方法上：`map` / `map_err` 变换两侧，`and_then` / `or_else` 串联，`unwrap` / `expect` / `unwrap_or` 取值，`ok` / `err` 转成 [[option|std::option]]。与 `Option` 的分工是：**没有值但不需要理由用 `Option`，失败了要说明原因用 `Result`**。

## 快速上手

```rust
use std::fmt;
use std::num::ParseIntError;

// 返回 Result 的函数：? 直接把解析错误抛给调用者
fn parse_and_double(text: &str) -> Result<i32, ParseIntError> {
    let n: i32 = text.trim().parse()?;
    Ok(n * 2)
}

// 自定义错误类型：实现 Display 就能装进 Box<dyn Error>
#[derive(Debug, PartialEq)]
struct TooBig(u32);

impl fmt::Display for TooBig {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "数值 {} 太大", self.0)
    }
}

fn check(n: u32) -> Result<u32, TooBig> {
    if n > 100 { Err(TooBig(n)) } else { Ok(n) }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    assert_eq!(parse_and_double(" 21 "), Ok(42));
    assert!(parse_and_double("四十二").is_err());

    // Ok / Err 就是普通枚举，模式匹配是基本功
    match check(50) {
        Ok(v) => assert_eq!(v, 50),
        Err(e) => println!("出错了：{e}"),
    }

    // map 处理成功值，map_err 转换错误，unwrap_or 提供兜底
    assert_eq!(check(50).map(|v| v + 1), Ok(51));
    assert_eq!(check(500).map(|v| v + 1), Err(TooBig(500)));
    assert_eq!(check(500).unwrap_or(0), 0);
    assert!(check(500).is_err());

    // and_then 串联多个可能失败的操作，任一步 Err 就短路
    assert_eq!(check(50).and_then(|v| check(v * 2)), Ok(100));
    assert!(check(60).and_then(|v| check(v * 2)).is_err());

    // 只收集 Ok 的值
    let results: [Result<i32, &str>; 3] = [Ok(1), Err("坏"), Ok(3)];
    let values: Vec<i32> = results.iter().filter_map(|r| r.as_ref().ok().copied()).collect();
    assert_eq!(values, [1, 3]);

    // ? 也能直接在 main 里传播，错误统一装进 Box<dyn Error>
    let parsed: i32 = "7".parse()?;
    assert_eq!(parsed, 7);

    println!("全部通过");
    Ok(())
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[result.Result\|Result]] | `Ok(T)` / `Err(E)` 两个变体的枚举。 |
| `result::Iter` | 遍历 `&Result` 中 `Ok` 值的迭代器。 |
| `result::IterMut` | 遍历 `&mut Result` 中 `Ok` 值的可变迭代器。 |
| `result::IntoIter` | 按值遍历 `Result`，交出 `Ok` 里的值。 |
| `Result::is_ok` / `is_err` | 判断成功 / 失败，不消耗值。 |
| `Result::map` / `map_err` | 变换成功值 / 变换错误值。 |
| `Result::and_then` / `or_else` | 串联成功分支 / 失败分支，可短路。 |
| `Result::unwrap` / `expect` | 取值，`Err` 时 panic（`expect` 带自定义信息）。 |
| `Result::unwrap_or` / `unwrap_or_else` | 取值，`Err` 时返回默认值 / 调用闭包。 |
| `Result::ok` / `err` | 丢弃一半，转换成 `Option`。 |
| `Result::as_ref` / `as_mut` | 借出内部值，保留原 `Result`。 |

## 注意事项

> [!warning] `?` 的适用范围
> `?` 只能用在返回 `Result`（或 `Option`）的函数里。在 `main` 里用它，`main` 的签名要写成 `fn main() -> Result<(), Box<dyn std::error::Error>>`。错误类型不匹配时，编译器要求存在 `From` 转换，否则得手动 `map_err`。

> [!danger] 生产代码里少用 `unwrap` / `expect`
> 它们把可恢复错误变成了 panic：只要 `Err` 就立刻 unwind，整个线程结束。原型和测试里用很方便，但库代码或服务里应改用 `?`、`unwrap_or_else`、`match`。工具类场景至少写 `expect("……时的上下文")`，别留下裸 `unwrap`。

> [!tip] 错误类型怎么选
> 只关心「成不成功」、不需要原因时用 [[option|std::option]] 的 `Option`；库内部用具体的错误枚举（可 `match` 区分分支）；应用层懒得定义枚举时用 `Box<dyn std::error::Error>` 或 [[string.String|String]]。错误类型转换一律走 [[convert.From|From]]，这样 `?` 才能自动接上。

## 相关

- [[result.Result|Result]]：全部方法、变体与组合子都在这一页。
- [[option|std::option]]：`Option<T>`，与 `Result` 互为补充。
- [[error|std::error]]：[[error.Error|Error]] 特质，错误类型的统一接口。
- [[11-错误处理|错误处理]]：`?`、自定义错误、错误链的完整讲法。
- [[panic|std::panic]]：不可恢复错误与 `catch_unwind`。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 4 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`IntoIter`](https://doc.rust-lang.org/std/result/struct.IntoIter.html)
- [`Iter`](https://doc.rust-lang.org/std/result/struct.Iter.html)
- [`IterMut`](https://doc.rust-lang.org/std/result/struct.IterMut.html)

### 枚举

- [[result.Result|`Result`]]

<!-- END AUTO ITEMS -->
