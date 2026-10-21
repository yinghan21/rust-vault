---
title: "unsafe 与 FFI"
type: 学习笔记
stage: 进阶
order: 24
tags:
  - rust/进阶
aliases:
  - unsafe
  - FFI
  - 外部函数接口
一句话: unsafe 是「编译器无法验证、由我担保」的五种能力，FFI 是把这份担保延伸到别的语言边界上。
updated: 2026-10-21
---

# unsafe 与 FFI

> [!abstract] 一句话
> `unsafe` 不关闭借用检查、不关闭类型检查，它只是**额外允许**五种编译器无法证明的操作；FFI 是在语言边界上使用这些操作，再把不变量包装回安全 API。

## 为什么需要它

编译器只能验证它「看得懂」的规则：所有权、借用、生命周期。硬件寄存器、C 的 ABI、自引用结构、无锁算法里的别名，这些前提它证明不了，只能由人担保。Rust 把这个担保**显式写出来并圈定范围**——对比 C，同样危险的代码可以藏在任意一行，无从审计。

## unsafe 能做的五件事

| 能力 | 说明 |
| --- | --- |
| 解引用裸指针 | `*const T` / `*mut T` 解引用，绕过借用检查 |
| 调用 unsafe 函数 | 含 `extern` 函数、其他 `unsafe fn`、内建 intrinsics |
| 访问可变静态变量 | 读写 `static mut`，天然没有同步 |
| 实现 unsafe trait | 如手写 `Send` / `Sync`（见 [[marker.Send\|Send]]） |
| 访问 union 字段 | 读 `union` 字段，编译器不知道哪个变体是活跃的 |

块内的普通代码规则照旧生效：所有权、借用、泛型约束一个都没放松，所以「加个 unsafe 就能过编译」是错觉。

## 裸指针


```rust
fn main() {
    let mut x = 42;
    let p: *mut i32 = &mut x;
    let q = p as *const i32; // 可自由转换，编译器不管别名
    unsafe {
        *p += 1; // 解引用必须在 unsafe 块里
        assert_eq!(*q, 43);
    }
}
```

要点：从 `0x1000 as *const i32` 解引用是 UB；偏移用 `p.add(n)`；裸指针只管地址，不管有效期。

## unsafe 函数与安全封装

`unsafe fn` 表示「调用者必须先满足某个前提」，前提写在文档的 `# Safety` 小节。库作者的标准做法是：**外面套一个安全函数，在入口处检查不变量，把 `unsafe` 压到最小**。

```rust
fn split_at_mut_checked(values: &mut [i32], mid: usize) -> (&mut [i32], &mut [i32]) {
    let len = values.len();
    assert!(mid <= len, "mid 不能超过长度");
    let ptr = values.as_mut_ptr();
    // SAFETY: 已断言 mid <= len；两段区间不重叠，且都落在同一块分配内
    unsafe {
        (std::slice::from_raw_parts_mut(ptr, mid),
         std::slice::from_raw_parts_mut(ptr.add(mid), len - mid))
    }
}

fn main() {
    let mut data = [1, 2, 3, 4, 5];
    let (a, b) = split_at_mut_checked(&mut data, 2);
    a[0] = 10;
    b[0] = 30;
    assert_eq!(data, [10, 2, 30, 4, 5]);
}
```


## extern "C" 与 #[no_mangle]

`#[no_mangle]` 关掉符号名修饰（name mangling），`extern "C"` 指定 C 的调用约定（ABI）；两者合起来才是「C 能调用的函数」。

```rust
mod c_side {
    // 假装这是 C 提供的函数：没有修饰名，ABI 是 C
    #[no_mangle]
    pub extern "C" fn rust_add(a: i32, b: i32) -> i32 { a + b }
}

extern "C" {
    fn rust_add(a: i32, b: i32) -> i32;
}

fn main() {
    // SAFETY: 符号就在同一个二进制里，签名与声明一致
    assert_eq!(unsafe { rust_add(1, 2) }, 3);
}
```

跨语言传结构体必须加 `#[repr(C)]`；`bool`、`char`、`String`、`&str` 都不是 C 类型，边界上要换成 `i32`/`u8`、`c_char` 和 `CString`/`CStr`（[[ffi.CString|CString]]、[[ffi.CStr|CStr]]）。

## 调用 C 库：libc 的 extern 声明

`extern "C" { fn strlen(...); }` 只是**声明**，编译期足够，链接期才需要真实符号。所以下面这段只声明、不调用，任何平台都能编译。

```rust
use std::os::raw::c_char;

extern "C" {
    fn strlen(s: *const c_char) -> usize;
}

fn main() {
    // 平台差异：Linux / macOS 的 strlen 来自 libc（rustc 默认已链接）；Windows MSVC 来自 ucrt，
    // 部分 CRT 函数带下划线前缀（如 _snprintf）。真实项目用 libc / windows-sys，别手写声明。
    println!("已声明 strlen，但不调用，链接期不依赖它");
}
```

## 安全封装的原则

1. **先问能不能不用**：`Vec`、`split_at_mut`、`Cell`、`Box::from_raw` 已经封装了绝大多数需求。
2. **unsafe 块尽量小**，上方写 `// SAFETY:` 说明为什么满足前提，这是 review 的关键信息。
3. **对外只暴露安全 API**：不变量在入口用 `assert!`、类型（`NonZeroU32`、私有字段）挡住；`unsafe fn` 必须写 `# Safety` 说明调用者义务。
4. **所有权要明确**：`Box::into_raw` 之后必须有人 `Box::from_raw`，不配对就是泄漏或双重释放。

## Miri：抓 unsafe 里的未定义行为

普通测试跑不出 UB。Miri 是 MIR 解释器，能检测越界、悬垂指针、读未初始化内存、别名违规（Stacked Borrows）和数据竞争；用法是 `rustup +nightly component add miri`、`cargo +nightly miri setup`，然后 `cargo +nightly miri test`。它慢几十倍，所以只对含 `unsafe` 的用例跑，也不支持内联汇编。

## 常见错误与解决

| 错误 | 原因 | 解决 |
| --- | --- | --- |
| `E0133: requires unsafe block` | 忘了把调用包进 `unsafe` | 包上 `unsafe { ... }`，并写 SAFETY 注释 |
| `undefined reference to strlen` | 只声明了符号，链接期找不到 | 加 `#[link(name = "c")]`，或改用 `libc` crate |
| `E0428: defined multiple times` | `#[no_mangle]` 与同名声明冲突 | 定义放进子模块，或用不同符号名 |
| 随机崩溃、数据损坏 | 裸指针导致悬垂或双重释放 | 用 `cargo miri test` 定位 |

## 练习

1. 用裸指针实现 `fn swap_raw(a: &mut i32, b: &mut i32)`，写出它的 SAFETY 注释。
2. 把 `split_at_mut_checked` 改成 `unsafe fn`，补 `# Safety` 小节说明调用者义务。

## 相关

- [[ptr|std::ptr]]：`null`、`read`、`write`、`copy` 等裸指针工具。
- [[20-智能指针|智能指针]]：`Box::into_raw` / `from_raw` 的所有权交接。
- [[26-性能与优化|性能与优化]]：用 `unsafe` 换性能之前先测量。
