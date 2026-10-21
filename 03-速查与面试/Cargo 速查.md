---
title: "Cargo 速查"
type: 速查
tags:
  - 速查
aliases:
  - Cargo 速查
  - cargo 命令
一句话: 一页查完 cargo 常用命令、Cargo.toml 字段、features、workspace、profile 与国内镜像配置。
updated: 2025-06-01
---

# Cargo 速查

> [!abstract] 一句话
> 命令、清单字段、profile、镜像四块并排放在一起；概念解释见 [[02-Cargo 与项目结构|Cargo 与项目结构]]。

## 常用命令

| 条目 | 说明 |
| --- | --- |
| `cargo new demo` | 新建二进制项目，加 `--lib` 建库。 |
| `cargo init` | 在现有目录里补出 Cargo 项目骨架。 |
| `cargo build` | 编译 debug 版，产物在 `target/debug/`。 |
| `cargo build --release` | 编译优化版，产物在 `target/release/`。 |
| `cargo check` | 只做类型检查，不出二进制，速度最快。 |
| `cargo run -- arg1` | 编译并运行，`--` 后是程序参数。 |
| `cargo test` | 跑单测、集成测试与文档测试。 |
| `cargo test name` | 只跑名字含 `name` 的测试。 |
| `cargo bench` | 跑基准测试，一般需要 nightly 或 criterion。 |
| `cargo doc --open` | 生成文档并在浏览器打开。 |
| `cargo clean` | 删除整个 `target/`。 |
| `cargo fmt` | 按 rustfmt 格式化，`--check` 只检查。 |
| `cargo clippy -- -D warnings` | 跑静态检查，把警告升级为错误。 |
| `cargo add serde --features derive` | 添加依赖并写好版本与 features。 |
| `cargo remove serde` | 移除依赖。 |
| `cargo update` | 更新 `Cargo.lock` 里的次要版本，`-p name` 只更一个。 |
| `cargo tree` | 打印依赖树，查版本冲突与重复依赖。 |
| `cargo tree -d` | 只看同一 crate 的多个版本。 |
| `cargo metadata` | 输出项目结构 JSON，给工具链用。 |
| `cargo package` | 打包成 `.crate`，发布前本地自检。 |
| `cargo publish` | 发布到 crates.io，先 `cargo login`。 |
| `cargo install ripgrep` | 从源码安装可执行文件到 `~/.cargo/bin`。 |
| `cargo vendor` | 把依赖源码拷进项目，用于离线构建。 |
| `cargo fix --edition` | 自动迁移到新 edition。 |
| `cargo build -Z unstable-options` | 使用 nightly 的实验特性。 |

## 项目结构

```text
demo/
├── Cargo.toml
├── Cargo.lock          # 二进制项目要提交，库项目通常不提交
├── build.rs            # 可选，构建脚本
├── src/
│   ├── main.rs         # 二进制入口
│   ├── lib.rs          # 库入口（可同时存在）
│   ├── bin/other.rs    # 额外二进制，名字为 other
│   └── modname.rs      # 子模块
├── tests/integration.rs # 集成测试，只能调 pub API
├── benches/bench.rs     # 基准测试
└── examples/demo.rs     # 示例，cargo run --example demo
```

## `Cargo.toml` 字段

### `[package]`

| 字段 | 说明 |
| --- | --- |
| `name` | crate 名，发布后不可改。 |
| `version` | 语义化版本，`cargo publish` 的版本号。 |
| `edition` | 语言版本，写 `"2021"` 或 `"2024"`。 |
| `rust-version` | 支持的最低 Rust 版本（MSRV）。 |
| `authors` | 作者列表，可省略。 |
| `description` | 一句话简介，发布 crates.io 必填。 |
| `license` | SPDX 标识，如 `"MIT OR Apache-2.0"`。 |
| `repository` / `homepage` | 源码仓库 / 主页链接。 |
| `readme` | README 路径，默认 `README.md`。 |
| `keywords` / `categories` | 搜索关键词与分类，最多 5 个关键词。 |
| `build` | 构建脚本路径，默认 `build.rs`。 |
| `links` | 声明本 crate 链接的原生库名。 |
| `publish` | `false` 禁止发布，或指定允许发布的 registry。 |
| `default-run` | 有多个二进制目标时指定 `cargo run` 的默认目标。 |
| `resolver` | 依赖解析器版本，edition 2021 默认 `"2"`。 |

### 目标与依赖

| 条目 | 说明 |
| --- | --- |
| `[lib]` | 库目标，`crate-type` 可设 `rlib`/`cdylib`/`staticlib`。 |
| 额外二进制目标 | 用双中括号数组表声明，写 `name` 与 `path`。 |
| `[dependencies]` | 运行时依赖，`serde = "1"` 表示 `^1`。 |
| `[dev-dependencies]` | 仅测试/示例/基准可见的依赖。 |
| `[build-dependencies]` | 仅 `build.rs` 可用的依赖。 |
| `[target.'cfg(unix)'.dependencies]` | 按平台条件引入依赖。 |
| `[patch.crates-io]` | 用本地路径或 git 覆盖某个依赖。 |
| `[replace]` | 旧式依赖替换，新项目用 `[patch]`。 |
| `git = "https://..."` | 从 git 引入，`rev`/`tag`/`branch` 三选一。 |
| `path = "../mylib"` | 从本地路径引入，改代码即生效。 |
| `default-features = false` | 关掉默认特性，按需打开。 |
| `optional = true` | 标记可选依赖，由同名 feature 开启。 |

```toml
[dependencies]
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tokio = { version = "1", features = ["rt-multi-thread", "macros"], optional = true }

[dev-dependencies]
tempfile = "3"

[target.'cfg(windows)'.dependencies]
winapi = "0.3"
```

## features

| 条目 | 说明 |
| --- | --- |
| `[features]` | 声明特性开关，编译期按需裁剪代码。 |
| `default = ["std"]` | 默认特性列表，`default-features = false` 可关闭。 |
| `feat = ["dep:serde"]` | `dep:` 让可选依赖只在开启时启用。 |
| `full = ["a", "b"]` | 特性可以组合其他特性。 |
| `#[cfg(feature = "feat")]` | 按特性条件编译代码。 |
| `cargo build --features feat` | 打开单个特性。 |
| `cargo build --all-features` | 打开全部特性，CI 常用。 |
| `cargo build --no-default-features` | 关闭默认特性，做最小构建。 |
| `cargo tree -e features` | 查看特性被谁打开。 |

```toml
[features]
default = ["std"]
std = []
extra = ["dep:serde", "dep:serde_json"]

[dependencies]
serde = { version = "1", optional = true, features = ["derive"] }
serde_json = { version = "1", optional = true }
```

## workspace

| 条目 | 说明 |
| --- | --- |
| `[workspace]` | 在根 `Cargo.toml` 里声明工作区。 |
| `members = ["crates/*"]` | 成员清单，支持 glob。 |
| `exclude = ["docs"]` | 明确排除的目录。 |
| `resolver = "2"` | 工作区统一解析器版本，写根清单里。 |
| `[workspace.dependencies]` | 集中写版本，成员用 `x.workspace = true` 继承。 |
| `[workspace.package]` | 集中写 `version`/`edition`/`license` 等元数据。 |
| `cargo build -p crate_a` | 只构建某个成员。 |
| `cargo test --workspace` | 对所有成员跑测试。 |
| 根目录 `Cargo.lock` | 工作区共用一个锁文件，成员目录下不再有。 |

```toml
[workspace]
members = ["crates/*"]
exclude = ["benchmarks"]
resolver = "2"

[workspace.package]
version = "0.1.0"
edition = "2021"
license = "MIT OR Apache-2.0"

[workspace.dependencies]
serde = { version = "1", features = ["derive"] }
```

成员里继承：

```toml
[package]
name = "crate-a"
version.workspace = true
edition.workspace = true

[dependencies]
serde.workspace = true
```

## profile

| 条目 | 说明 |
| --- | --- |
| `[profile.dev]` | 默认调试档，`cargo build`。 |
| `[profile.release]` | 发布档，开启优化。 |
| `[profile.test]` / `[profile.bench]` | 测试档 / 基准档，默认继承各自基础档。 |
| `opt-level` | 优化等级 `0`~`3`，`s`/`z` 优化体积。 |
| `debug` | 调试符号 `true`/`false`/`"line-tables-only"`。 |
| `lto` | 链接时优化，`"thin"` 平衡编译时间与体积。 |
| `codegen-units = 1` | 减少并行单元，换取更好优化。 |
| `panic = "abort"` | 出错直接中止，省掉展开表的体积。 |
| `strip` | 剥离符号，二进制更小。 |
| `incremental` | 增量编译，release 下通常关掉。 |
| `overflow-checks` | 整数溢出检查，release 默认 `false`。 |
| `[profile.release.package."*"]` | 只对依赖生效的 profile 覆盖。 |

```toml
[profile.release]
lto = "thin"
codegen-units = 1
strip = true
panic = "abort"

[profile.dev]
opt-level = 0
debug = true

[profile.dev.package."*"]
opt-level = 2
```

## 国内镜像配置

写进 `~/.cargo/config.toml`（Windows 为 `%USERPROFILE%\.cargo\config.toml`），只影响本机，不要提交进仓库。

```toml
[source.crates-io]
replace-with = "ustc"

[source.ustc]
registry = "sparse+https://mirrors.ustc.edu.cn/crates.io-index/"

[net]
git-fetch-with-cli = true

[build]
jobs = 8
```

| 镜像 | 索引地址 |
| --- | --- |
| 中科大 USTC | `sparse+https://mirrors.ustc.edu.cn/crates.io-index/` |
| 字节 RSProxy | `sparse+https://rsproxy.cn/index/` |
| 清华 TUNA | `sparse+https://mirrors.tuna.tsinghua.edu.cn/crates.io-index/` |
| 上海交大 SJTUG | `sparse+https://mirrors.sjtug.sjtu.edu.cn/crates.io-index/` |

RSProxy 还提供二进制分发：

```toml
[source.crates-io]
replace-with = "rsproxy-sparse"

[source.rsproxy-sparse]
registry = "sparse+https://rsproxy.cn/index/"

[source.rsproxy]
registry = "https://rsproxy.cn/crates.io-index"

[registries.rsproxy]
index = "https://rsproxy.cn/crates.io-index"
```

> [!warning] 换镜像后的常见症状
> 提示 `registry index was not found` 或校验失败时，先删 `~/.cargo/registry/index` 缓存再 `cargo update`；公司网络锁 git 协议时，`git-fetch-with-cli = true` 能让 cargo 走系统 git 代理。

## 环境变量

| 条目 | 说明 |
| --- | --- |
| `CARGO_HOME` | cargo 数据目录，默认 `~/.cargo`。 |
| `CARGO_TARGET_DIR` | 覆盖 `target/` 位置，CI 里共享缓存。 |
| `RUSTFLAGS` | 追加给 rustc 的参数，如 `-C target-cpu=native`。 |
| `RUST_BACKTRACE=1` | panic 时打印回溯，`full` 更详细。 |
| `RUST_LOG` | 日志过滤，配合 `env_logger`/`tracing` 使用。 |
| `CARGO_BUILD_JOBS` | 并行编译任务数。 |
| `RUSTUP_TOOLCHAIN` | 临时指定工具链，如 `nightly`。 |

## 相关

- [[02-Cargo 与项目结构|Cargo 与项目结构]]、[[01-安装与工具链|工具链]]
- [[27-常用 crate 与生态|常用 crate 与生态]]、[[25-测试与文档|测试与文档]]
- [[标准库速查]]、[[编译错误手册]]
