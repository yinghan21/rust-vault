---
title: "std::ffi::CStr"
type: std-条目
kind: 结构体
module: ffi
slug: ffi.CStr
stable: "1.0.0"
tags:
  - std/类型
  - std/IO
aliases:
  - CStr
一句话: 借用的 C 字符串视图，以 NUL 结尾的一段字节，通常以 &CStr 形式出现在 FFI 边界上。
---

# `CStr`

> [!abstract] 一句话
> `CStr` 是**借用的 C 字符串视图**：一段以 `\0` 结尾的字节，本身不拥有内存，实际使用时几乎总是 `&CStr`。

## 简介

`CStr` 是定位于 FFI 边界的类型：C 侧给你一个 `*const c_char`，Rust 侧需要「带长度、带不变量」的表示，两者之间的桥就是 `&CStr`——它假定指针指向一段以 NUL 结尾的数据，并提供 `to_bytes()`、`to_str()` 等方法安全地读取。

构造方式有三种粒度：

- **安全**：`CStr::from_bytes_until_nul(&[u8])` 从字节切片构造，遇到第一个 NUL 就截断，适合处理「可能有多个 NUL」的缓冲区。
- **安全但严格**：`CStr::from_bytes_with_nul(&[u8])` 要求切片**恰好**一个结尾 NUL、中间没有 NUL，否则报错。
- **不安全**：`CStr::from_ptr(*const c_char)` 直接包装裸指针，假定它确实指向一段合法的 NUL 结尾字符串。

从 Rust 1.77 起还可以用 C 字符串字面量 `c"hello"`，它的类型就是 `&'static CStr`，会自动补上结尾 NUL。需要长期保存或跨线程传递时，用 `to_owned()` 或 [[ffi.CString|CString]] 复制一份。

对应关系：`&CStr` 之于 [[ffi.CString|CString]]，就像 `&str` 之于 `String`。它和 [[ffi.OsStr|OsStr]] 不同：`CStr` 只关心 C 的 NUL 约定，不承担操作系统原生编码的语义。

## 常用方法

### 构造

| 方法 | 说明 |
| --- | --- |
| `from_ptr(ptr)` | 未检查地包装 C 裸指针，需保证以 NUL 结尾。 |
| `from_bytes_until_nul(bytes)` | 从字节切片构造，取第一个 NUL 之前的部分。 |
| `from_bytes_with_nul(bytes)` | 从恰好一个结尾 NUL 的字节切片构造。 |
| `from_bytes_with_nul_unchecked(bytes)` | 未检查地从字节切片构造 `&CStr`。 |

### 读取与转换

| 方法 | 说明 |
| --- | --- |
| `as_ptr()` | 返回指向内容的裸指针，可交给 C。 |
| `count_bytes()` | 返回长度，不含结尾 NUL，类似 `strlen`。 |
| `is_empty()` | 判断内容长度是否为 0。 |
| `to_bytes()` | 转换为不含结尾 NUL 的字节切片。 |
| `to_bytes_with_nul()` | 转换为含结尾 NUL 的字节切片。 |
| `to_str()` | 是合法 UTF-8 时返回 `Ok(&str)`。 |
| `to_string_lossy()` | 转换为 `Cow<str>`，非法字节被替换。 |
| `into_c_string()` | 把 `Box<CStr>` 零拷贝转成 `CString`。 |

## 示例

```rust
use std::ffi::{CStr, CString};

fn main() {
    // from_bytes_until_nul 最宽松：从第一个 NUL 处截断
    let s = CStr::from_bytes_until_nul(b"hi\0rest").unwrap();
    assert_eq!(s.to_bytes(), b"hi");
    assert_eq!(s.to_bytes_with_nul(), b"hi\0");
    assert_eq!(s.count_bytes(), 2);
    assert!(!s.is_empty());
    assert_eq!(s.to_str().unwrap(), "hi");

    // from_bytes_with_nul 要求恰好一个结尾 NUL
    let exact = CStr::from_bytes_with_nul(b"hi\0").unwrap();
    assert_eq!(exact, s);

    // 与 CString 之间零成本互转
    let owned = CString::new("hi").unwrap();
    assert_eq!(s, owned.as_c_str());

    // 缺少结尾 NUL 会被拒绝
    assert!(CStr::from_bytes_with_nul(b"hi").is_err());
    println!("内容：{}", s.to_string_lossy());
}
```

## 常见陷阱

1. **`from_ptr` 之后指针失效**：返回的 `&CStr` 生命周期由调用方负责，源缓冲区被释放后继续使用就是未定义行为，务必让原数据活得足够久。
2. **滥用 `from_bytes_with_nul`**：它要求「恰好一个结尾 NUL、中间无 NUL」，缓冲里有多个 NUL 会报错；这种数据请用 `from_bytes_until_nul`。
3. **把 `to_str()` 当必然成功**：它只做 UTF-8 校验，C 侧常见的 Latin-1 或 GBK 字节会返回 `Err(Utf8Error)`，改用 `to_bytes()` 自行解码。
4. **在循环里反复 `count_bytes()`**：它和 C 的 `strlen` 一样要扫描到 NUL，复杂度 O(n)，多次使用应当先存下长度。
5. **手写结尾 `\0`**：`c"hi"` 字面量已经自动补上 NUL，再写 `c"hi\0"` 只会多出一个字节，容易造成长度算错。

## 相关

- [[ffi.CString|CString]]：拥有所有权的对应类型，需要保存或修改时用它。
- [[ffi|std::ffi]]：本条目所属模块，还有 `NulError` 等错误类型。
- [[ffi.OsStr|OsStr]]：同样承载非 UTF-8 字节，但语义是操作系统原生字符串。
- [[24-unsafe 与 FFI|unsafe 与 FFI]]：`from_ptr`、`c"..."` 与 `extern "C"` 的完整用法。
- [[primitive.str|str]]：`&str` 与 `&CStr` 在结尾和编码上的区别。
