---
title: "常用 crate 与生态"
type: 学习笔记
stage: 进阶
order: 27
tags:
  - rust/进阶
aliases:
  - 常用 crate 与生态
  - crate 生态
  - 依赖选型
一句话: 标准库只管语言必需的零件，序列化、参数、随机、正则、错误、日志、异步网络这七件事交给生态里的事实标准。
updated: 2026-10-22
---

# 常用 crate 与生态

> [!abstract] 一句话
> 标准库刻意留白：`serde`、`clap`、`rand`、`regex`、`anyhow`/`thiserror`、`tracing`、`tokio`/`reqwest` 拼起来，才是一个真实项目的默认底座。

## 为什么需要它

标准库的原则是「稳定到永不删改」，所以只收语言与运行时必需的部分：能打印、能开线程、能读文件，但没有 JSON、没有正则、没有异步执行器。别的语言把这些塞进标准库（Python 的 `json`、`re`、`asyncio`），代价是标准库一动就难改；Rust 选择交给 crate，用语义化版本各自演进——代价是你要会挑，选错了编译时间、二进制体积、维护成本一起涨。下面所有示例共用这份依赖，配好就能 `cargo run`（带外部 crate 的代码单文件 `rustc` 编译不了）：

```toml
[dependencies]
serde = { version = "1", features = ["derive"] }   # 另加 serde_json = "1"
clap = { version = "4", features = ["derive"] }
rand = "0.9"
regex = "1"
anyhow = "1"                                       # 库层错误换 thiserror = "2"
tracing = "0.1"                                    # 配 tracing-subscriber = "0.3"
tokio = { version = "1", features = ["macros", "rt-multi-thread"] } # 配 reqwest = "0.12"
```

## serde：序列化的事实标准

```text
use serde::{Deserialize, Serialize};
#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")] // JSON 里写成 userName
struct User { id: u32, name: String }
fn main() {
    let u: User = serde_json::from_str(r#"{"id":1,"name":"Ada"}"#).unwrap();
    assert_eq!(serde_json::to_string(&u).unwrap(), r#"{"id":1,"name":"Ada"}"#);
}
```

`serde` 负责「结构体 ↔ 数据模型」，具体格式由 `serde_json` 提供；可选字段加 `#[serde(default)]`，省略空 `Option` 用 `skip_serializing_if = "Option::is_none"`，结构不固定就用 `serde_json::Value`。

## clap：用 derive 描述命令行

```text
use clap::Parser;
#[derive(Parser, Debug)]
#[command(version, about = "统计文件行数")] // --help、--version 自动生成
struct Cli {
    file: String, // help 文案取字段上方的文档注释
    #[arg(short, long, default_value_t = 100)] // 生成 -l 与 --limit
    limit: usize,
}
fn main() { let c = Cli::parse_from(["wc", "a.txt"]); println!("{:?}", c.file); }
```

参数声明成结构体字段，`#[arg]` 控制短选项、默认值与帮助文案；`parse_from` 让测试不依赖真 argv，完整项目见 [[01-命令行工具|命令行工具]]。

## rand 与 regex：一个生成，一个匹配

```text
use rand::Rng;
fn main() {
    let mut rng = rand::rng(); // rand 0.9；0.8 里是 thread_rng()，密钥场景换 OsRng
    let dice: u32 = rng.random_range(1..=6); // 0.8 里是 gen_range()
    let re = regex::Regex::new(r"\d+").unwrap(); // 编译一次，别放进循环
    assert!(re.is_match(&dice.to_string())); // regex 线性时间、无回溯
}
```

## anyhow 与 thiserror：应用层与库层分开

```text
use anyhow::{Context, Result};
use thiserror::Error;
#[derive(Debug, Error)] // 库层：给调用方一个可以 match 的枚举
pub enum LoadError { #[error("读取失败：{0}")] Io(#[from] std::io::Error) }
fn read_port(path: &str) -> Result<u16> { // 应用层：一个 Result 抹平所有错误
    let s = std::fs::read_to_string(path).with_context(|| format!("读 {path} 失败"))?;
    s.trim().parse().context("端口不是数字")
}
```

判断标准很直接：**给别人用的库暴露 `thiserror` 枚举，自己的 `main`/handler 用 `anyhow`**。库的公开签名写 `anyhow::Error` 会让调用方无法按变体分支，见 [[11-错误处理|错误处理]]。

## tracing 与 tokio：可观测性与运行时

```text
use tracing::{info, instrument};
use tracing_subscriber::EnvFilter;
#[instrument(skip_all, fields(user = id))] // 自动为这次调用建 span
fn handle(id: u32) { info!("开始处理"); }
fn main() {
    tracing_subscriber::fmt().with_env_filter(EnvFilter::from_default_env()).init();
    handle(7); // RUST_LOG=info cargo run 控制级别
}
```

```text
#[tokio::main]
async fn main() -> Result<(), reqwest::Error> {
    let body = reqwest::get("https://example.com").await?.text().await?;
    println!("{} 字节", body.len());
    Ok(())
}
```

`tracing` 记的是带字段的事件与 span，不是拼好的字符串：同一个 `info!` 能打到终端、能输出 JSON、能按环境变量过滤，库作者不必关心日志最终去哪。标准库到 [[future.Future|Future]] 与 `Waker` 就停了，tokio 补上执行器；features 按需开 `net`、`time`、`fs`、`sync`，全开 `full` 会明显拖长编译，`reqwest` 阻塞场景用 `reqwest::blocking`，异步模型见 [[22-异步编程|异步编程]]。

## 怎么判断一个 crate 值不值得用

| 维度 | 看什么 |
| --- | --- |
| 使用面与维护 | 下载趋势、谁在依赖它；最近发布时间、issue 响应、维护者是否只有一个人 |
| 安全 | `unsafe` 的密度与用途、RUSTSEC 有无公告、`cargo audit` 是否干净 |
| 兼容 | MSRV（`rust-version` 字段）、edition、是否支持 `no_std` 与你的平台 |
| 替代 | 标准库是否已覆盖：`LazyLock` 取代 `lazy_static`，`mpsc` 顶掉一部分 `crossbeam` |

## Cargo 依赖管理建议

- 版本写 `"1"` 或 `"1.2"`（即 `^1.2`），别写 `"*"`；只有需要锁死破坏性场景才用 `=1.2.3`，见 [[02-Cargo 与项目结构|Cargo 与项目结构]]。
- 关掉多余特性：`serde = { version = "1", default-features = false, features = ["derive"] }`；`cargo tree -e features` 看得出谁把特性合并开了。
- 二进制项目提交 `Cargo.lock` 保证可复现构建；工作区用 `[workspace.dependencies]` 统一版本，并定期跑 `cargo update`、`cargo tree -d`、`cargo outdated`、`cargo audit`（速查见 [[Cargo 速查|Cargo 速查]]）。

## 常见错误与解决

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| `cannot find derive macro Serialize` | 没开 `serde` 的 `derive` 特性 | `features = ["derive"]` |
| 库的公开签名用了 `anyhow::Error` | 应用层接口漏进库 | 换成 `thiserror` 枚举 |
| 升级后方法改名（`gen_range` → `random_range`） | 主版本升级 | 读 CHANGELOG，或暂时 `cargo add rand@0.8` |

## 练习

1. 给 `struct Config { port: u16, name: String }` 加 `Serialize`/`Deserialize`，序列化再读回并断言相等。
2. 用 clap derive 写 `--input` 与 `-n`，再用 `parse_from` 写一个不依赖 argv 的测试。
3. 用 `thiserror` 定义库错误、用 `anyhow` 在 `main` 里加 `with_context`，打印完整错误链。

## 相关

- [[02-Cargo 与项目结构|Cargo 与项目结构]]、[[Cargo 速查|Cargo 速查]]：依赖、特性与 profile 的写法；[[11-错误处理|错误处理]] 讲 `Error` trait 与 `?` 转换。
- [[22-异步编程|异步编程]]、[[future.Future|Future]]：tokio 补上了标准库的哪一环；后续再读 [[26-性能与优化|性能与优化]] 与 [[01-命令行工具|命令行工具]]。
