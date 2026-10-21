---
title: "std::arch"
type: std-模块
module: arch
stable: "1.27.0"
unstable: false
tags:
  - std/模块
aliases:
  - arch
一句话: 架构相关的内建函数入口：按目标架构划分的 SIMD 指令封装，以及 CPU 特性的运行时检测宏。
---

# std::arch

> [!abstract] 一句话
> `std::arch` 是「贴着硬件写」的入口：下面按架构分子模块（`x86_64`、`aarch64` 等），提供对应 CPU 指令的封装，以及判断当前机器到底支持哪些特性的检测宏。

## 模块简介

`std::arch` 本身不是一个可以用 `use` 展开的普通模块，而是一层**按目标架构分流**的命名空间。Rust 能编译到的每个架构在这里都可能有同名子模块，比如 `i686-pc-windows-msvc` 上是 `std::arch::x86`，`x86_64-pc-windows-msvc` 上是 `std::arch::x86_64`。这些子模块只在对应架构上存在，所以**引用它们必须用 `#[cfg(target_arch = "...")]` 包起来**，否则换平台就编译不过。

子模块里的内容是 vendor intrinsics——通常一条机器指令对应一个函数，比如 SSE、AVX、NEON。它们不是可移植抽象：同一种架构的不同机器，可能有一台支持 AVX2 而另一台不支持。所以真正可用的写法是两步：先用本模块的 `is_x86_feature_detected!` 之类宏在运行时探测，再进到 `unsafe` 的 `#[target_feature(enable = "...")]` 函数里执行。

绝大多数项目不会直接写下层 intrinsic，而是用标准库之上的安全封装或者成熟的第三方库。只有在热点循环里想榨掉最后一截性能，或者要精确复刻某条指令语义时，才值得下沉到这一层。学习顺序上，建议先理解 [[24-unsafe 与 FFI|unsafe 与 FFI]]，再回来看这里的检测宏。

## 快速上手

```rust
fn main() {
    // 宏的名字带架构前缀，且只在对应目标上存在，因此要先按 cfg 过滤
    #[cfg(any(target_arch = "x86", target_arch = "x86_64"))]
    {
        let has_sse2 = std::arch::is_x86_feature_detected!("sse2");
        println!("SSE2 支持：{has_sse2}");

        if std::arch::is_x86_feature_detected!("avx2") {
            println!("支持 AVX2，可以走更快的分支");
        } else {
            println!("不支持 AVX2，使用通用实现");
        }
    }

    #[cfg(target_arch = "aarch64")]
    {
        println!("NEON 支持：{}", std::arch::is_aarch64_feature_detected!("neon"));
    }

    #[cfg(not(any(
        target_arch = "x86",
        target_arch = "x86_64",
        target_arch = "aarch64"
    )))]
    {
        println!("当前架构没有对应的运行时特性检测宏");
    }
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| `is_x86_feature_detected!` | 运行时检测 x86 / x86_64 的 CPU 特性，如 `sse2`、`avx2`。 |
| `is_aarch64_feature_detected!` | 运行时检测 AArch64 的特性，如 `neon`。 |
| `is_arm_feature_detected!` | 运行时检测 32 位 ARM 的特性。 |
| `is_riscv_feature_detected!` | 运行时检测 RISC-V 的特性。 |
| `is_loongarch_feature_detected!` | 运行时检测 LoongArch 的特性。 |
| `is_powerpc_feature_detected!` | 运行时检测 32 位 PowerPC 的特性。 |
| `is_powerpc64_feature_detected!` | 运行时检测 64 位 PowerPC 的特性。 |
| `is_mips_feature_detected!` | 运行时检测 MIPS 的特性。 |
| `is_mips64_feature_detected!` | 运行时检测 64 位 MIPS 的特性。 |
| `is_s390x_feature_detected!` | 运行时检测 s390x 的特性。 |

## 注意事项

> [!warning] 完全不可移植
> 每个检测宏只在对应架构上存在，架构子模块也一样。跨平台代码必须用 `#[cfg(target_arch = "...")]` 把引用包住，并用 `cfg(not(any(...)))` 给其他平台留一条通用分支。

> [!danger] 检测到特性也不等于可以随便调用
> 调用 `#[target_feature(enable = "...")]` 标注的函数是 `unsafe` 的，调用者必须自己保证该特性在当前机器上可用。在没有该特性的机器上执行对应指令，会直接收到非法指令信号并崩溃，编译器不会拦截。

> [!tip] 先用高层封装，实在不够再下沉
> 手写 intrinsic 既要处理目标特性、又要处理跨平台分支，出错代价高。优先使用标准库的安全封装或成熟第三方库，只在确实测量出热点之后才考虑 `std::arch`。

## 相关

- [[模块索引]]
- [[24-unsafe 与 FFI|unsafe 与 FFI]]：`target_feature` 函数与 unsafe 契约。
- [[26-性能与优化|性能与优化]]：什么时候值得下沉到指令级。
- [[hint|std::hint 模块]]：给编译器的其他低层提示。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 10 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 宏

- [`is_aarch64_feature_detected`](https://doc.rust-lang.org/std/arch/macro.is_aarch64_feature_detected.html)
- [`is_loongarch_feature_detected`](https://doc.rust-lang.org/std/arch/macro.is_loongarch_feature_detected.html)
- [`is_riscv_feature_detected`](https://doc.rust-lang.org/std/arch/macro.is_riscv_feature_detected.html)
- [`is_s390x_feature_detected`](https://doc.rust-lang.org/std/arch/macro.is_s390x_feature_detected.html)
- [`is_x86_feature_detected`](https://doc.rust-lang.org/std/arch/macro.is_x86_feature_detected.html)
- [`is_arm_feature_detected`](https://doc.rust-lang.org/std/arch/macro.is_arm_feature_detected.html)
- [`is_mips64_feature_detected`](https://doc.rust-lang.org/std/arch/macro.is_mips64_feature_detected.html)
- [`is_mips_feature_detected`](https://doc.rust-lang.org/std/arch/macro.is_mips_feature_detected.html)
- [`is_powerpc64_feature_detected`](https://doc.rust-lang.org/std/arch/macro.is_powerpc64_feature_detected.html)
- [`is_powerpc_feature_detected`](https://doc.rust-lang.org/std/arch/macro.is_powerpc_feature_detected.html)

<!-- END AUTO ITEMS -->
