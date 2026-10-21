---
title: "std::env::var"
type: std-条目
kind: 函数
module: env
slug: env.var
stable: "1.0.0"
tags:
  - std/IO
aliases:
  - var
一句话: 按名字读取一个环境变量，返回 Result<String, VarError>，区分「不存在」与「不是 Unicode」。
---

# `var`

> [!abstract] 一句话
> `std::env::var(key)` 按名字取一个环境变量，成功得到 `String`；失败时用 `VarError` 区分「没这个变量」和「值不是合法 Unicode」。

## 简介

环境变量是进程启动时继承的一份字符串表，常用来放配置：日志级别、数据库地址、运行模式。`env::var` 就是这张表的读取入口，接受任何 `AsRef<OsStr>` 作为键，返回 `Result<String, VarError>`。

两个失败分支含义完全不同。`VarError::NotPresent` 表示键不存在——对可选配置这是正常情况，用 `unwrap_or` / `unwrap_or_default` 给默认值即可。`VarError::NotUnicode` 表示变量存在但值不是合法 UTF-8：在 Windows 上很常见，此时应该用 `env::var_os` 拿到原始 `OsString`，而不是把它当「没设置」。

注意区分**编译期**和**运行时**：`env!` 宏在编译时把值嵌进二进制（值变了要重新编译），`option_env!` 是它的可空版本，而 `env::var` 是运行时读取。想支持「改环境变量重启即生效」，就必须用 `env::var`。

## 签名与参数

```text
pub fn var<K: AsRef<OsStr>>(key: K) -> Result<String, VarError>
```

| 参数 | 说明 |
| --- | --- |
| `key` | 变量名，`&str` 或 `OsStr` 均可。 |
| 返回 `Ok(String)` | 变量的值，合法 UTF-8。 |
| 返回 `Err(NotPresent)` | 没有这个变量。 |
| 返回 `Err(NotUnicode)` | 变量存在，但值不是合法 UTF-8。 |

- 键区分大小写的行为随平台：Unix 区分，Windows 不区分，跨平台配置名建议统一大写。
- 值不会自动 `trim`、不会自动 `parse`，需要自己做。
- 想拿原始字节用 `env::var_os`，想一次读全部用 `env::vars`。

## 示例

```rust
use std::env;

fn main() {
    // 三种结果都处理：存在、不存在、值非法
    match env::var("RUST_VAULT_DEMO") {
        Ok(value) => println!("RUST_VAULT_DEMO = {value}"),
        Err(env::VarError::NotPresent) => println!("RUST_VAULT_DEMO 未设置"),
        Err(env::VarError::NotUnicode(os)) => println!("值不是合法 Unicode: {os:?}"),
    }

    // 可选配置：给默认值
    let level = env::var("RUST_LOG").unwrap_or_else(|_| String::from("info"));
    println!("日志级别: {level}");

    println!("是否设置了 RUST_LOG: {}", env::var("RUST_LOG").is_ok());
}
```

读取并解析成具体类型：

```rust
use std::env;

fn main() {
    let workers: usize = env::var("WORKERS")
        .ok()
        .and_then(|v| v.trim().parse().ok())
        .unwrap_or(4);

    assert!(workers >= 1);
    println!("工作线程数: {workers}");

    // 需要原始字节时用 var_os，避免 Unicode 限制
    if let Some(path) = env::var_os("PATH") {
        println!("PATH 长度: {}", path.len());
    }
}
```

## 常见陷阱

1. **对可选变量直接 `unwrap`**：`NotPresent` 是常态，`unwrap` 会让程序在没有配置时崩掉，对策是用 `unwrap_or` 给默认值。
2. **把 `NotUnicode` 当「未设置」**：变量其实存在，只是字节不合法，对策是改用 `var_os` 处理。
3. **值带空白或空串**：`"1 "` 直接 `parse` 会失败、空串不等于未设置，对策是先 `trim` 并自己判断空值。
4. **在运行中反复修改再读**：`set_var` / `remove_var` 在多线程下并不安全（新版本已标记为 `unsafe`），对策是启动早期把配置读进结构体。
5. **用 `env!` 期望运行时生效**：宏是编译期求值，改了环境变量必须重新编译，对策是改用 `env::var`。

## 相关

- [[env|std::env 模块]]：`args`、`vars`、`var_os` 与当前工作目录都在这。
- [[env.args|env::args]]：命令行参数，常与环境变量一起构成配置来源。
- [[ffi.OsString|OsString]]：`var_os` 的返回类型，能装非 UTF-8 值。
- [[result.Result|Result]]：`var` 的返回类型，`?` 可直接传播 `VarError`。
- [[11-错误处理|错误处理]]：区分错误分支与默认值处理的通用思路。
