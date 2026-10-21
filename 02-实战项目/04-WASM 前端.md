---
title: "项目：wasm-bindgen + wasm-pack 的浏览器计算模块"
type: 实战项目
difficulty: 中等
stack:
  - wasm-bindgen 0.2
  - wasm-pack
  - wasm-bindgen-test
  - console_error_panic_hook
tags:
  - rust/实战
aliases:
  - 项目-WASM 前端
  - wasm-demo
一句话: 用 wasm-bindgen 把斐波那契和字符串处理导出成 JS 函数，wasm-pack 打成 ES 模块，再在浏览器页面里调用。
---

# 项目：WASM 前端 wasm-demo

## 目标

把一段 Rust 计算逻辑搬进浏览器：导出 `fib`（数值计算）和 `reverse_text` / `char_count` / `to_slug`（字符串处理）四个函数，用 `wasm-pack` 构建成一个 ES 模块，在纯 HTML 页面里 `import` 调用。重点是把三件事走通：`#[wasm_bindgen]` 的类型映射、`cdylib` 产物结构、以及必须用 HTTP 打开页面这条硬规则。

## 技术栈

| 用途 | crate / 工具 |
| --- | --- |
| 导出函数与类型转换 | `wasm-bindgen` 0.2 |
| 构建、`wasm-opt` 压缩、生成 `.d.ts` | `wasm-pack` |
| panic 信息转到浏览器控制台 | `console_error_panic_hook` |
| 在浏览器里跑单元测试 | `wasm-bindgen-test` + `wasm-pack test` |

## 第 1 步：初始化项目

```bash
cargo install wasm-pack --locked
cargo new --lib wasm-demo
cd wasm-demo
cargo add wasm-bindgen
cargo add console_error_panic_hook
cargo add --dev wasm-bindgen-test
```

`Cargo.toml` 的完整内容（`crate-type` 是重点：`cdylib` 产出 `.wasm`，`rlib` 保留普通 Rust 库，测试才编得过）：

```toml
[package]
name = "wasm-demo"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib", "rlib"]

[dependencies]
wasm-bindgen = "0.2"
console_error_panic_hook = "0.1"

[dev-dependencies]
wasm-bindgen-test = "0.3"

[profile.release]
opt-level = "s"
lto = true
```

`opt-level = "s"` 让编译器偏向体积而不是速度，`.wasm` 通常能小一半；`lto = true` 需要和 `wasm-opt` 一起看，`wasm-pack` 默认会调后者。

## 第 2 步：导出斐波那契

```rust
use wasm_bindgen::prelude::*;

/// 迭代版斐波那契，O(n)，从 fib(0) = 0 开始
/// u64 在 JS 侧是 BigInt，n 超过 93 会溢出
#[wasm_bindgen]
pub fn fib(n: u32) -> u64 {
    let (mut a, mut b) = (0u64, 1u64);
    for _ in 0..n {
        let next = a.checked_add(b).expect("fib 超出 u64，n 必须 ≤ 93");
        a = b;
        b = next;
    }
    a
}
```

递归版 `fib` 在 `n = 40` 就要几秒，浏览器直接卡住；迭代版是线性的。这里故意用 `checked_add` 而不是 `+`：release 模式下 `+` 会静默回绕，返回一个错得离谱的数字，而 `expect` 会 panic，再由第 4 步的钩子把信息打到控制台。返回值选 `u64` 是为了不丢精度，代价是 JS 侧拿到的是 `BigInt`（`55n` 而不是 `55`）。

## 第 3 步：导出字符串处理

```rust
/// 按 Unicode 标量反转：中文不会被切成半个字
#[wasm_bindgen]
pub fn reverse_text(s: &str) -> String {
    s.chars().rev().collect()
}

/// 统计字符数（不是字节数），中文一个字算一个
#[wasm_bindgen]
pub fn char_count(s: &str) -> usize {
    s.chars().count()
}

/// 转 URL slug：小写、把连续的非字母数字压成一个连字符
#[wasm_bindgen]
pub fn to_slug(s: &str) -> String {
    let mut out = String::with_capacity(s.len());
    let mut pending_dash = false;
    for c in s.chars().flat_map(char::to_lowercase) {
        if c.is_alphanumeric() {
            out.push(c);
            pending_dash = false;
        } else if !out.is_empty() && !pending_dash {
            out.push('-');
            pending_dash = true;
        }
    }
    out.trim_end_matches('-').to_string()
}
```

`&str` 参数由 wasm-bindgen 自动从 JS 字符串转过来，`String` 返回值自动转回 JS 字符串，中间不需要手写 `TextEncoder`。`chars()` 是必须的：按 `&s[..]` 切字节会 panic 在中文中间。`is_alphanumeric()` 对中文返回 `true`，所以 `to_slug("Hello 世界")` 保留中文，只想保留 ASCII 就换成 `is_ascii_alphanumeric()`。

## 第 4 步：初始化与 panic 钩子

```rust
/// 模块加载时自动执行一次，把 panic 变成 console.error
#[wasm_bindgen(start)]
pub fn start() {
    console_error_panic_hook::set_once();
}
```

没有这行钩子，Rust 侧 panic 在浏览器里只显示 `unreachable executed`，栈里一个字都看不懂；装好之后能看到 `panicked at src/lib.rs:9: fib 超出 u64...`。`#[wasm_bindgen(start)]` 的函数由生成的 JS 在实例化后自动调用，不需要在页面里额外写。

## 第 5 步：构建与在 JS 里调用

```bash
wasm-pack build --target web --release
ls pkg   # wasm_demo.js、wasm_demo_bg.wasm、wasm_demo.d.ts、package.json
```

`--target web` 生成浏览器原生的 ES 模块；给 webpack/Vite 用就换 `--target bundler`，给 Node 用换 `--target nodejs`。产物名取自 `package.name`，连字符会变成下划线，所以是 `wasm_demo.js`。

页面和脚本放在 `www/`，把 `pkg/` 整个复制进去：

```javascript
// www/main.js
import init, { fib, reverse_text, char_count, to_slug } from './pkg/wasm_demo.js';

await init();                                  // 下载并实例化 wasm_demo_bg.wasm

console.log(fib(10).toString());               // "55"，u64 是 BigInt
console.log(reverse_text('Rust 很香'));         // "香很 tsuR"
console.log(char_count('Rust 很香'));           // 7
console.log(to_slug('Hello WASM 世界'));        // "hello-wasm-世界"
document.body.textContent = `fib(50) = ${fib(50)}`;
```

`www/index.html` 里只写一行：`<script type="module" src="./main.js"></script>`。

## 运行与验证

```bash
cd www && python -m http.server 8080   # 必须走 HTTP，file:// 打不开
# 浏览器访问 http://localhost:8080 ，打开控制台看四行输出
```

双击 `index.html` 用 `file://` 打开一定失败：ES 模块的 `import` 和 `init()` 里对 `.wasm` 的请求都属于跨源限制，直接在本地文件协议下被拦。四个输出对得上，说明类型映射（数字、字符串、BigInt）都通了。

再补一个浏览器内测试，`wasm_bindgen_test` 在真实 JS 环境里跑 Rust 断言：

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use wasm_bindgen_test::wasm_bindgen_test;

    #[wasm_bindgen_test]
    fn slug_去重连字符() {
        assert_eq!(to_slug("Hello   WASM !!"), "hello-wasm");
        assert_eq!(reverse_text("abc"), "cba");
        assert_eq!(char_count("中文"), 2);
    }
}
```

跑测试用 `wasm-pack test --headless --chrome`，需要本机装有 Chrome 和匹配版本的 chromedriver。

## 扩展方向

1. 导出 `#[wasm_bindgen] pub struct` 做一个有状态的解析器，JS 侧 `new` 出来当普通对象用。
2. 用 `js-sys` / `web-sys` 操作 DOM、`performance.now()`，把计算型函数换成真正的前端组件。
3. 用 `wasm-bindgen-futures` 导出 `async fn`，在 JS 里 `await`，配合 `fetch` 做流式解析。
4. 加 `wasm-opt -Oz` 与 `wasm-pack build --release --no-typescript` 对比体积；对二进制体积敏感时看 [[26-性能与优化|性能与优化]]。

## 相关

- [[13-字符串|字符串]]：`String` 与 `str` 的区别、`chars()` 为什么比按字节切安全。
- [[primitive.str|str]]：`&str` 作为参数时借用与 UTF-8 边界规则。
- [[24-unsafe 与 FFI|unsafe 与 FFI]]：wasm-bindgen 生成的胶水代码同样靠 FFI 边界传数据。
- [[25-测试与文档|测试与文档]]：`#[cfg(test)]` 与 `wasm-bindgen-test` 的分工。
- [[02-Cargo 与项目结构|Cargo]]：`[lib] crate-type`、`[profile.release]` 这些平时不碰的配置。
- [[03-并发爬虫|并发爬虫]]：上一个项目，服务端并发与前端 WASM 正好两头。

下一个项目：[[05-嵌入式入门|嵌入式入门]]。
