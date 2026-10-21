---
title: "std::ffi"
type: std-模块
module: ffi
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - ffi
一句话: 跨语言边界的字符串与类型工具：CString/CStr、OsString/OsStr 以及 C 的 c_* 类型别名。
---

# std::ffi

> [!abstract] 一句话
> `std::ffi` 负责「Rust 字符串 ↔ 外部世界字符串」的转换：`CString`/`CStr` 对接 C 的 nul 结尾字符串，`OsString`/`OsStr` 承载平台原生字符串，另外还有一组对应 C 基本类型的 `c_*` 别名。

## 模块简介

Rust 的 [[string.String|String]] 和 `str` 永远是合法 UTF-8，长度是显式记录的，中间可以合法出现 `\0`，结尾也没有终止符。C 的字符串正好相反：以 `\0` 结尾、没有长度字段、编码由调用方约定。**这两套表示不能直接互换**，`std::ffi` 就是为此存在的。

第一组是 C 字符串：`CString` 是拥有所有权的版本，构造时检查「中间没有 `\0`」，并在末尾补一个 `\0`；`CStr` 是借用的胖指针视图，可以零拷贝地从 C 侧拿到的 `*const c_char` 包出来。两者都能和 `&str`/`String` 互转，转换失败的原因（中间有 nul、结尾缺 nul、合法 UTF-8 校验失败）各有专门的错误类型。

第二组是 OS 字符串：`OsString`/`OsStr`。它表示「操作系统眼里的字符串」——Windows 的文件名本质是 UTF-16（可能含孤立代理项），Unix 的文件名是任意字节序列，所以它**不保证 UTF-8**。文件名、环境变量、命令行参数本质上都是这种字符串，[[path.Path|Path]] 内部就是 `OsStr`。

此外还有三类辅助条目：`c_*` 类型别名（`c_int`、`c_char`、`c_size_t` 等）用来在 `extern "C"` 声明里精确表达 C 的整数宽度；`c_void` 对应 C 的 `void` 指针；`VaList` 用于调用 C 的可变参数函数。写 FFI 绑定时，这一模块是第一站。

## 快速上手

```rust
use std::ffi::{CStr, CString, OsStr, OsString};

fn main() {
    // 1. Rust 字符串 → C 字符串：自动在末尾补 \0
    let c = CString::new("hello").unwrap();
    assert_eq!(c.as_bytes(), b"hello");       // 不含结尾 nul
    assert_eq!(c.as_bytes_with_nul(), b"hello\0"); // 含结尾 nul
    assert_eq!(c.as_c_str().to_bytes(), b"hello");

    // 中间有 \0 会失败，NulError 是它的错误类型
    assert!(CString::new("he\0llo").is_err());

    // 2. C 字符串 → Rust 字符串
    let borrowed: &CStr = c.as_c_str();
    assert_eq!(borrowed.to_str().unwrap(), "hello");
    assert_eq!(borrowed.to_string_lossy(), "hello");

    // 3. 从已有的 nul 结尾字节零拷贝构造 &CStr
    let raw: &[u8] = b"world\0";
    let world = CStr::from_bytes_with_nul(raw).unwrap();
    assert_eq!(world.to_str().unwrap(), "world");
    assert_eq!(world.to_bytes(), b"world"); // to_bytes 去掉结尾 nul
    // 结尾没有 nul 会失败
    assert!(CStr::from_bytes_with_nul(b"oops").is_err());

    // 4. OsString / OsStr：不要求 UTF-8，装文件名、参数最合适
    let name: OsString = OsString::from("文件名.txt");
    assert_eq!(name.as_os_str(), OsStr::new("文件名.txt"));
    assert_eq!(name.to_str(), Some("文件名.txt")); // 是 UTF-8 时才拿到 &str
    assert_eq!(name.to_string_lossy(), "文件名.txt");

    // OsStr 可以来回转换，不丢数据
    let back: OsString = OsStr::new("a.txt").to_os_string();
    assert_eq!(back, OsString::from("a.txt"));
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[ffi.CString\|CString]] | 拥有所有权的 C 字符串：中间无 nul、末尾有 nul。 |
| [[ffi.CStr\|CStr]] | 借用的 C 字符串视图，可零拷贝包裹 `*const c_char`。 |
| [[ffi.OsString\|OsString]] | 拥有所有权的平台原生字符串，不要求 UTF-8。 |
| [[ffi.OsStr\|OsStr]] | 借用的平台原生字符串，`Path` 的底层表示。 |
| `NulError` | `CString::new` 发现中间有 nul 时的错误。 |
| `FromBytesWithNulError` | `CStr::from_bytes_with_nul` 的校验错误（结尾或中间 nul 位置不对）。 |
| `FromVecWithNulError` | `CString::from_vec_with_nul` 的校验错误。 |
| `IntoStringError` | `CString::into_string` 因非 UTF-8 失败时的错误。 |
| `c_char` | 等价于 C 的 `char`，`c_char` 的符号性随平台而变。 |
| `c_int` / `c_uint` | 等价于 C 的 `int` / `unsigned int`，宽度随平台。 |
| `c_long` / `c_size_t` | C 的 `long` / `size_t`，跨平台宽度差异最大的两个。 |
| `c_void` | C 的 `void`，用作指针目标类型。 |
| `VaList` | C 的可变参数列表，ABI 兼容 `va_list`。 |

## 注意事项

> [!danger] `as_ptr()` 的生命周期
> `CString::as_ptr()` 返回的指针只在 `CString` 存活期间有效，且没有 nul 之外的额外保证。常见错误是 `let p = c_string.as_ptr();` 然后 `c_string` 被移动或释放之后才使用 `p`——编译器不会拦你，这在 FFI 里就是野指针。

> [!warning] `OsStr` 不是 UTF-8
> 文件名在 Unix 上可以是任意字节（除了 `\0` 和 `/`），在 Windows 上是可能与 UTF-16 无损互转的扩展形式（WTF-8，允许孤立代理项）。所以 `OsStr::to_str()` 返回 `Option<&str>`：可能失败。处理路径时不要过早 `to_str().unwrap()`，`to_string_lossy()` 只适合展示，遇到非法序列会用 `�` 顶替、丢掉原始信息。

> [!tip] `c_*` 别名别自己写
> 不要假设 `c_long` 是 8 字节（Windows 上 `long` 是 4 字节而 `size_t` 是 8 字节），一律用 `std::ffi`（或 `core::ffi`）里的别名。`std::os::raw` 下有同名别名，但新代码建议用本模块这组。

## 相关

- [[ffi.CString|CString]] / [[ffi.CStr|CStr]]：C 字符串的所有权与借用形式。
- [[ffi.OsString|OsString]] / [[ffi.OsStr|OsStr]]：平台原生字符串。
- [[path.Path|Path]]：以 `OsStr` 为底层的路径类型。
- [[24-unsafe 与 FFI|unsafe 与 FFI]]：`extern "C"`、`#[repr(C)]` 与裸指针的完整笔记。
- [[string.String|String]]：UTF-8 拥有所有权字符串，与 `CString` 的对照。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 28 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [[ffi.CStr|`CStr`]]
- [[ffi.CString|`CString`]]
- [`FromBytesUntilNulError`](https://doc.rust-lang.org/std/ffi/struct.FromBytesUntilNulError.html)
- [`FromVecWithNulError`](https://doc.rust-lang.org/std/ffi/struct.FromVecWithNulError.html)
- [`IntoStringError`](https://doc.rust-lang.org/std/ffi/struct.IntoStringError.html)
- [`NulError`](https://doc.rust-lang.org/std/ffi/struct.NulError.html)
- [[ffi.OsStr|`OsStr`]]
- [[ffi.OsString|`OsString`]]
- [`VaList`](https://doc.rust-lang.org/std/ffi/struct.VaList.html)

### 枚举

- [`FromBytesWithNulError`](https://doc.rust-lang.org/std/ffi/enum.FromBytesWithNulError.html)
- [`c_void`](https://doc.rust-lang.org/std/ffi/enum.c_void.html)

### 特质

- [`VaArgSafe`](https://doc.rust-lang.org/std/ffi/trait.VaArgSafe.html)

### 类型别名

- [`c_char`](https://doc.rust-lang.org/std/ffi/type.c_char.html)
- [`c_double`](https://doc.rust-lang.org/std/ffi/type.c_double.html)
- [`c_float`](https://doc.rust-lang.org/std/ffi/type.c_float.html)
- [`c_int`](https://doc.rust-lang.org/std/ffi/type.c_int.html)
- [`c_long`](https://doc.rust-lang.org/std/ffi/type.c_long.html)
- [`c_longlong`](https://doc.rust-lang.org/std/ffi/type.c_longlong.html)
- [`c_schar`](https://doc.rust-lang.org/std/ffi/type.c_schar.html)
- [`c_short`](https://doc.rust-lang.org/std/ffi/type.c_short.html)
- [`c_uchar`](https://doc.rust-lang.org/std/ffi/type.c_uchar.html)
- [`c_uint`](https://doc.rust-lang.org/std/ffi/type.c_uint.html)
- [`c_ulong`](https://doc.rust-lang.org/std/ffi/type.c_ulong.html)
- [`c_ulonglong`](https://doc.rust-lang.org/std/ffi/type.c_ulonglong.html)
- [`c_ushort`](https://doc.rust-lang.org/std/ffi/type.c_ushort.html)
- [`c_ptrdiff_t`](https://doc.rust-lang.org/std/ffi/type.c_ptrdiff_t.html)
- [`c_size_t`](https://doc.rust-lang.org/std/ffi/type.c_size_t.html)
- [`c_ssize_t`](https://doc.rust-lang.org/std/ffi/type.c_ssize_t.html)

<!-- END AUTO ITEMS -->
