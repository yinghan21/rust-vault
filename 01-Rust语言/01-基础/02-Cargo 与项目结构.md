---
title: Cargo 与项目结构
type: 学习笔记
stage: 入门
order: 2
tags:
  - rust/入门
aliases:
  - Cargo
  - 清单
一句话: 把 Cargo.toml 的每个字段、依赖版本、feature、workspace 与 profile 一次讲清，让项目从「能跑」变成「可维护、可发布」。
updated: 2025-06-01
---

# Cargo 与项目结构

> [!abstract] 一句话
> `Cargo.toml` 是项目的唯一真相来源：包信息、依赖、条件编译开关、构建配置全在这里，理解它就理解了 Rust 项目的骨架。

## 为什么需要它

C++ 项目的构建配置散在 CMakeLists、Makefile、各平台的 IDE 工程里；Python 用 `requirements.txt` 或 `pyproject.toml` 管依赖，却没有统一的构建流程；Node 把依赖塞进 `node_modules` 并靠 `package.json` 的字符串拼版本号。Cargo 把「拉依赖、编译、测试、生成文档、发布」压进同一个清单文件，且**语义化版本与锁定文件是内建语义**，不是社区约定。

代价是 Cargo 规定了一些目录布局。好在规定得很小：`src/main.rs` 是二进制入口，`src/lib.rs` 是库入口，其余自由。

## 核心规则

### Cargo.toml 的最小骨架

```toml
[package]
name = "hello"          # 包名，发布后成为 crate 名
version = "0.1.0"       # 语义化版本
edition = "2021"        # 语言版本，不是编译器版本
rust-version = "1.75"   # 最低支持的 Rust 版本（MSRV）

[dependencies]
```

几个容易忽略的字段：`edition` 决定语言行为（例如 `2021` 下数组的 `into_iter` 按值迭代），**新建项目不要手写旧 edition**；`rust-version` 只是声明，不会阻止你用新语法，但 CI 应该用这个版本实测；`name` 里允许 `-`，代码里 `use` 时要写成 `_`。

### 目录约定与两种 crate

| 路径 | 含义 |
| --- | --- |
| `src/main.rs` | 二进制 crate 的入口，产出可执行文件 |
| `src/lib.rs` | 库 crate 的入口，被别的 crate 引用 |
| `src/bin/名字.rs` | 额外的二进制目标，一个文件一个可执行文件 |
| `tests/名字.rs` | 集成测试，每个文件单独编译 |
| `benches/`、`examples/` | 基准测试、示例程序 |
| `build.rs` | 构建脚本，编译前运行 |

`src/main.rs` 和 `src/lib.rs` 同时存在是**推荐做法**：逻辑写进库，`main.rs` 只做参数解析和调用，这样集成测试和文档示例都能引用到同一份逻辑。

### 依赖与语义化版本

```toml
[dependencies]
# 省略版本写法等于 ^：允许 1.x，不允许 2.0
serde = "1"
# 精确锁定，一般只在排查问题时用
# serde = "=1.0.190"
# 允许补丁级更新，不允许次版本更新
# serde = "~1.0.190"
# 区间写法
# serde = ">=1.0, <1.2"
```

版本号 `1.2.3` 读作「主.次.补丁」。Cargo 默认按**插入符语义**解释：`"1.2.3"` 等价于 `^1.2.3`，即允许 `1.x.y` 中最高的兼容版本。`0.x` 是特例，`"0.2.1"` 只允许 `0.2.*`，因为 `0.x` 被视为不稳定。

`Cargo.lock` 记录**这次实际用到的精确版本 + 校验和**。规则是：

- 二进制项目（有 `main.rs` 的）**必须提交** `Cargo.lock`，保证线上构建可复现。
- 库项目**通常不提交**，让下游自己解析版本。

`cargo update` 会忽略 `Cargo.lock` 重新解析，`cargo update -p serde` 只升一个包。

### features：条件编译开关

`features` 让你在**编译期**选择性地打开代码，不用的部分根本不参与编译：

```toml
[features]
default = ["std"]
std = []
# feature 可以依赖别的 feature
full = ["std", "json"]

[dependencies]
serde = { version = "1", optional = true }  # optional 会自动生成同名 feature
```

代码里用 `#[cfg(feature = "json")]` 判断，构建时 `cargo build --features json` 打开、`--no-default-features` 关掉默认组。

两个原则：**feature 必须是可加的**（打开任意组合都不该编译失败），否则下游只要有一个 crate 打开它，全图都得跟着开；**不要用 feature 表达互斥的两种实现**，那应该拆成两个 crate。

### workspace：一个仓库多个 crate

```toml
[workspace]
members = ["core", "cli", "server"]
# 所有成员共享的依赖版本，成员里写 { workspace = true } 引用
[workspace.dependencies]
serde = "1"
```

workspace 的价值是**共享一份 `Cargo.lock` 和一个 `target/`**：依赖只编译一次，`cargo build -p cli` 只编某个成员。多成员项目里公共依赖统一在 `[workspace.dependencies]` 声明，成员写 `serde = { workspace = true }`，升级时只改一处。

### profile：构建配置

```toml
[profile.dev]
opt-level = 0          # 默认，编译最快

[profile.release]
opt-level = 3          # 优化级别
lto = "thin"           # 链接时优化，thin 是性价比最高的挡位
codegen-units = 1      # 单单元生成，优化更狠但编译更慢
panic = "abort"        # 去掉展开逻辑，体积更小
strip = true           # 去掉符号表
```

调优顺序建议：先看 `cargo build --release` 的实际耗时，再动 `lto`，最后才考虑 `codegen-units = 1`——它会让编译时间成倍增长。性能调优的系统方法见 [[26-性能与优化|性能与优化]]。

### 发布到 crates.io

```bash
cargo login                  # 粘贴 crates.io 的 API token
cargo publish --dry-run      # 本地打包校验，不上传
cargo package --list         # 看清哪些文件会被打包
cargo publish                # 真正上传
```

清单里要有 `description`、`license`（或 `license-file`），否则会被拒。版本一旦发布就**不能覆盖**，只能发新版本，所以 `--dry-run` 值得每次都跑。

## 代码示例

`#[cfg]` 是纯编译期机制，直接交给 `rustc` 也能验证——下面这段在 debug 构建下打印 debug：

```rust
fn main() {
    // debug 构建时 debug_assertions 为真，release 构建时为假
    #[cfg(debug_assertions)]
    let mode = "debug";

    #[cfg(not(debug_assertions))]
    let mode = "release";

    println!("当前构建模式：{}", mode);
}
```

feature 没打开时，被 `#[cfg(feature = "...")]` 标记的代码会被整段移除，因此**不存在的依赖不会导致编译失败**：

```rust
// 未启用 serde feature 时，这个函数连同标记一起消失
#[cfg(feature = "serde")]
fn to_json() -> String {
    String::from("{}")
}

fn main() {
    #[cfg(feature = "serde")]
    println!("序列化结果：{}", to_json());

    #[cfg(not(feature = "serde"))]
    println!("未启用 serde feature，序列化代码未参与编译");
}
```

## 常见错误与解决

| 错误 / 现象 | 原因 | 解决 |
| --- | --- | --- |
| `failed to select a version for ...` | 依赖区间无解，通常是两个 crate 要求不兼容的主版本 | 用 `cargo tree -i 包名` 找出谁在要求旧版 |
| `no matching package named ...` | 包名拼错，或忘了先 `cargo add` | 检查 `name`；确认源可达 |
| `error: the lock file needs to be updated` | `Cargo.toml` 改了依赖但没同步锁文件 | `cargo build` 会自动更新，或手动 `cargo update` |
| `failed to parse manifest` | TOML 语法错，常见于用了旧写法 | 看报错行号；`[]` 段名与 `key = value` 别混行 |
| `error: edition 2024 is unstable` | edition 写成了当前工具链未稳定的值 | 改为 `2021`，或升级工具链 |
| `cargo publish` 提示缺字段 | 少了 `description` 或 `license` | 补齐清单字段后重试 |

## 练习

1. 给一个项目加上 `[features]` 里的 `json` 开关，让某个函数只在开启时编译，用 `cargo build` 与 `cargo build --features json` 各验证一次。
2. 建一个含 `core` 与 `cli` 两个成员的 workspace，把 `serde` 提到根级 `[workspace.dependencies]`，确认 `cargo build -p cli` 只编译该成员。
3. 对比 `[profile.release]` 中 `lto = "thin"` 与 `lto = "fat"` 的编译时间和运行时间，写下结论。

## 相关

- [[01-安装与工具链|安装与工具链]]：`cargo` 命令背后的工具链切换机制。
- [[10-模块与可见性|模块与可见性]]：`src/` 下的文件如何变成模块树。
- [[25-测试与文档|测试与文档]]：`tests/` 与 `#[test]` 怎么和 cargo 配合。
- [[Cargo 速查|Cargo 速查]]：清单字段与命令的速查表。
- [[27-常用 crate 与生态|常用 crate 与生态]]：依赖该选哪些库。
