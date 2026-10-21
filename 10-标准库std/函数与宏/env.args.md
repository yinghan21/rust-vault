---
title: "std::env::args"
type: std-条目
kind: 函数
module: env
slug: env.args
stable: "1.0.0"
tags:
  - std/IO
aliases:
  - args
一句话: 返回程序启动时的命令行参数迭代器，第一项通常是可执行文件路径。
---

# `args`

> [!abstract] 一句话
> `std::env::args()` 给你一个 `String` 迭代器，按顺序吐出 `argv`：第一项通常是可执行文件路径，其余是用户输入的参数。每次调用都从头开始。

## 简介

命令行程序的第一件事往往是读参数。`env::args()` 返回一个 `Args`，它实现了 [[iter.Iterator|Iterator]]，`Item = String`，所以 `collect::<Vec<String>>()`、`for` 循环、`skip(1)` 都能直接用。

第一项**通常**是可执行文件的路径，但这一项可以被调用方任意伪造（甚至为空或不存在），所以不要拿它做权限判断。真正的校验应该基于「当前进程确实加载了什么」，而不是 `argv[0]`。

`args()` 只接受合法的 UTF-8。参数里混入非 UTF-8 字节（Windows 上完全可能）时它会 panic；需要原样拿到字节序列，请用 `env::args_os()`，它返回 `OsString`。

## 签名与参数

```text
pub fn args() -> Args
```

| 项目 | 说明 |
| --- | --- |
| 参数 | 无。 |
| 返回 `Args` | 迭代器，`Item = String`。 |

- `Args` 通过 `next()` 逐个产出 `String`，没有长度方法，需要长度就先 `collect`。
- 每次调用 `args()` 都产生新的迭代器，从头开始，不是全局游标。
- 对非 UTF-8 的参数会 panic；要容错请用 `args_os()`。
- 必须 `use std::env;` 或写全路径 `std::env::args()`。

## 示例

```rust
use std::env;

fn main() {
    let mut args = env::args();
    let program = args.next().unwrap_or_else(|| String::from("<未知>"));

    println!("程序: {program}");
    for (i, arg) in args.enumerate() {
        println!("参数 {i}: {arg}");
    }

    // 也可以一次性收集，至少会包含程序名这一项
    let all: Vec<String> = env::args().collect();
    assert!(!all.is_empty());
    println!("参数总个数: {}", all.len());
}
```

一个极简的「两参数」解析：

```rust
use std::env;

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();

    match args.as_slice() {
        [cmd, path] => println!("命令 {cmd}，目标 {path}"),
        [] => println!("没有参数，打印用法"),
        _ => println!("参数过多: {} 个", args.len()),
    }
}
```

## 常见陷阱

1. **依赖 `argv[0]` 做安全检查**：它由调用方决定、可以伪造或缺失，对策是只把它当展示信息。
2. **非 UTF-8 参数触发 panic**：`args()` 会直接崩，对策是换成 `args_os()` 再按需转换。
3. **以为参数只有用户输入**：第一项是程序名，忘了 `skip(1)` 会把它当业务参数。
4. **重复调用 `args()` 做多次解析**：每次都重新构造迭代器，逻辑容易乱，对策是一开始就 `collect` 到 `Vec`。
5. **指望 shell 帮你展开通配符**：Unix 的 shell 会展开，Windows 不会，对策是在程序里自己处理或要求用户加引号。

## 相关

- [[env|std::env 模块]]：环境变量与命令行参数的入口。
- [[env.var|env::var]]：读取单个环境变量，常与参数配合做配置。
- [[iter.Iterator|Iterator]]：`args()` 返回值的用法都来自这个特质。
- [[ffi.OsString|OsString]]：`args_os()` 的元素类型，用于非 UTF-8 参数。
- [[01-命令行工具|命令行工具]]：参数解析的完整实战。
