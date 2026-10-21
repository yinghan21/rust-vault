---
title: "std::ffi::CString"
type: std-条目
kind: 结构体
module: ffi
slug: ffi.CString
stable: "1.0.0"
tags:
  - std/类型
  - std/IO
aliases:
  - CString
一句话: 拥有所有权的 C 兼容 NUL 结尾字符串，保证内部没有杂散 0 字节，可直接传给 FFI。
---

# `CString`

> [!abstract] 一句话
> `CString` 是**拥有所有权、C 兼容、NUL 结尾**的字符串，类型本身就保证「中间没有 0 字节、末尾一定是 0」，因此可以放心把它的指针交给 C 函数。

## 简介

C 语言没有「带长度的字符串」，只有「以 `\0` 结尾的字节数组」，而且长度靠 `strlen` 现场扫描。Rust 的 `String` 既不以 NUL 结尾、内部又允许出现 `\0`，直接传指针给 C 会读到越界或提前截断。`CString` 就是补上这一层的类型：

- **构造时校验**：`CString::new` 会检查输入里没有中间 `\0`，有就返回 `Err(NulError)`；这份校验让「实例存在」等价于「满足 C 的不变量」。
- **两种视图**：`as_bytes()` 不含结尾 NUL（内容本身），`as_bytes_with_nul()` 含结尾 NUL（完整的 C 缓冲区）。
- **所有权可移交**：`into_raw()` 把指针交给 C，之后必须用 `from_raw()` 收回，否则内存泄漏。
- **借用视图**：`as_c_str()` 得到 [[ffi.CStr|CStr]]，传参时优先用它而不是裸指针。

对应关系：`CString` 之于 `&CStr`，就像 `String` 之于 `&str`。反过来，从 C 拿到 `*const c_char` 时应该用 `CStr::from_ptr` 借一个视图，**不要**用 `CString::from_raw`（那是「收回所有权」的语义，两者混用会导致 double free）。

注意 `CString` 与 [[ffi.OsString|OsString]] 是两条线：前者面向 C 接口，后者面向操作系统字符串，二者之间没有直接转换。

## 常用方法

### 构造

| 方法 | 说明 |
| --- | --- |
| `new(t)` | 从字节容器创建，并检查内部没有 NUL。 |
| `from_vec_unchecked(v)` | 未检查地消耗字节向量创建，需自证无内部 NUL。 |
| `from_vec_with_nul(v)` | 校验字节向量恰好一个结尾 NUL 后转换。 |
| `from_vec_with_nul_unchecked(v)` | 未检查地把带 NUL 的字节向量转为 `CString`。 |
| `from_raw(ptr)` | 收回曾被 `into_raw` 移交出去的裸指针。 |

### 转换与所有权移交

| 方法 | 说明 |
| --- | --- |
| `into_raw()` | 交出裸指针，把所有权转给 C 调用方。 |
| `into_string()` | 转成 `String`，非 UTF-8 时返回 `Err`。 |
| `into_bytes()` | 消耗自身，返回不含结尾 NUL 的字节。 |
| `into_bytes_with_nul()` | 消耗自身，返回含结尾 NUL 的字节。 |
| `as_c_str()` | 借用成 `&CStr` 视图，不复制数据。 |
| `into_boxed_c_str()` | 转成 `Box<CStr>`，不复制数据。 |
| `as_ptr()` | 返回指向内容的裸指针，可直接传给 C。 |

### 读取与判断

| 方法 | 说明 |
| --- | --- |
| `as_bytes()` | 返回不含结尾 NUL 的字节切片。 |
| `as_bytes_with_nul()` | 返回含结尾 NUL 的字节切片。 |
| `count_bytes()` | 返回内容长度，不含结尾 NUL。 |
| `is_empty()` | 判断内容长度是否为 0。 |
| `to_bytes()` | 转换为不含结尾 NUL 的字节切片。 |
| `to_bytes_with_nul()` | 转换为含结尾 NUL 的字节切片。 |
| `to_str()` | 是合法 UTF-8 时返回 `Ok(&str)`。 |
| `to_string_lossy()` | 转换为 `Cow<str>`，非法字节被替换。 |

## 示例

```rust
use std::ffi::CString;

fn main() {
    let c = CString::new("hello").unwrap();

    // as_bytes 不含结尾 NUL，as_bytes_with_nul 含
    assert_eq!(c.as_bytes(), b"hello");
    assert_eq!(c.as_bytes_with_nul(), b"hello\0");
    assert_eq!(c.count_bytes(), 5);
    assert!(!c.is_empty());
    assert_eq!(c.to_str().unwrap(), "hello");

    // 借用成 CStr 视图，不复制数据
    assert_eq!(c.as_c_str().to_bytes(), b"hello");

    // 含内部 NUL 的输入会被拒绝
    assert!(CString::new("a\0b").is_err());

    // 取出带 NUL 的字节向量，再原样还原成 CString
    let with_nul = c.into_bytes_with_nul();
    assert_eq!(with_nul.as_slice(), b"hello\0");
    let c2 = CString::from_vec_with_nul(with_nul).unwrap();
    assert_eq!(&*c2.to_string_lossy(), "hello");

    // as_ptr 给出的指针可以直接传给 C 函数
    assert!(!c2.as_ptr().is_null());
}
```

## 常见陷阱

1. **输入里带 `\0` 却 `unwrap()`**：`CString::new` 会返回 `Err(NulError)`，来自用户或文件的字符串要先清洗或改用 `from_vec_unchecked` 前自证。
2. **把 `as_ptr()` 的指针存起来后 `CString` 被 drop**：指针会立刻悬垂，必须保证 `CString` 活得比 C 侧使用更久。
3. **`into_raw()` 之后忘记 `from_raw()`**：C 用完不交回所有权就是内存泄漏。
4. **从 C 的 `*const c_char` 用 `CString::from_raw` 收尾**：那是转移所有权的语义，借用场景应使用 `CStr::from_ptr`，否则会 double free。
5. **混淆两组字节方法**：`as_bytes()` / `count_bytes()` 不含结尾 NUL，`*_with_nul` 版本含；拷贝缓冲区时用前者，传给 C 时用后者。

## 相关

- [[ffi.CStr|CStr]]：借用版本，传参时优先用它取得视图。
- [[ffi|std::ffi]]：本条目所属模块。
- [[ffi.OsString|OsString]]：操作系统原生字符串，和 `CString` 用途不同。
- [[24-unsafe 与 FFI|unsafe 与 FFI]]：裸指针、所有权移交与 `extern "C"` 的基础。
- [[primitive.str|str]]：`&str` 与 C 字符串在编码和结尾上的差异。
