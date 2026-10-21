---
title: "std::ffi::OsString"
type: std-条目
kind: 结构体
module: ffi
slug: ffi.OsString
stable: "1.0.0"
tags:
  - std/类型
  - std/IO
aliases:
  - OsString
一句话: 拥有所有权、可修改的操作系统原生字符串，与 String 之间可零成本互转。
---

# `OsString`

> [!abstract] 一句话
> `OsString` 是**拥有所有权、可原地修改**的操作系统原生字符串，相当于 `String` 的宽松版：内容不要求是合法 UTF-8，因此能原样保存任意文件名、环境变量和命令行参数。

## 简介

`String` 要求内容必须是合法 UTF-8，但操作系统的字符串并非如此：Unix 的文件名可以是任意非 NUL 字节序列，Windows 用 UTF-16 的扩展表示。如果强行用 `String` 承载，遇到非法编码就只能报错或丢数据；`OsString` 则是「平台原生表示 + 可选的 Rust 字符串视图」——能存下一切，需要时再尝试转成文本。

常见的转换关系：

- `String` → `OsString`：直接 `OsString::from(s)` 或 `s.into()`，不检查、不转换编码。
- `OsString` → `String`：用 `into_string()`，成功是零成本的（内部布局一致），失败时把原 `OsString` 完整还回 `Err`。
- 只读视图：`as_os_str()` 得到 [[ffi.OsStr|OsStr]]；要文本用 `to_str()`（可能 `None`）或 `to_string_lossy()`（替换非法字节）。

`OsString` 实现了 `Deref<Target = OsStr>`，所以 `len()`、`is_empty()`、`eq_ignore_ascii_case()` 等 [[ffi.OsStr|OsStr]] 方法可以直接用；它还有一套自己的容量管理与追加方法（`with_capacity`、`push`、`reserve`、`shrink_to_fit`）。

一个关键区别：`OsString` **不是** NUL 结尾的。要传给 C 函数，必须先转成 [[ffi.CString|CString]]；要当作路径使用，请改用 [[path.PathBuf|PathBuf]]。

## 常用方法

### 构造与容量

| 方法 | 说明 |
| --- | --- |
| `new()` | 创建一个空的 `OsString`。 |
| `with_capacity(capacity)` | 创建容量至少为 `capacity` 的空 `OsString`。 |
| `capacity()` | 返回无需重新分配即可容纳的字节数。 |
| `clear()` | 清空内容，长度归零但保留容量。 |
| `reserve(additional)` | 预留至少 `additional` 字节的额外容量。 |
| `try_reserve(additional)` | 预留容量的可失败版本，返回 `Result`。 |
| `reserve_exact(additional)` | 精确预留至少 `additional` 字节容量。 |
| `try_reserve_exact(additional)` | 精确预留容量的可失败版本。 |
| `shrink_to_fit()` | 把容量收缩到刚好等于当前长度。 |
| `shrink_to(min_capacity)` | 把容量收缩到不低于给定下界。 |

### 追加与转换

| 方法 | 说明 |
| --- | --- |
| `push(s)` | 在末尾追加一段 `OsStr` 内容。 |
| `as_os_str()` | 转换成借用的 `&OsStr` 视图。 |
| `to_str()` | 是合法 UTF-8 时返回 `Some(&str)`。 |
| `to_string_lossy()` | 转换为 `Cow<str>`，非法字节被替换。 |
| `to_os_string()` | 复制成新的 `OsString`。 |
| `into_string()` | 转成 `String`，失败时把 `OsString` 还回 `Err`。 |
| `into_encoded_bytes()` | 消耗自身，交出编码后的字节向量。 |
| `into_boxed_os_str()` | 转成 `Box<OsStr>`，不重新分配。 |
| `leak()` | 泄漏内存，得到 `&'static mut OsStr`。 |
| `display()` | 返回可安全打印非 Unicode 内容的包装。 |
| `from_encoded_bytes_unchecked(bytes)` | 未检查地把字节向量还原为 `OsString`。 |

### 查询与 ASCII 操作

| 方法 | 说明 |
| --- | --- |
| `is_empty()` | 判断字符串是否为空。 |
| `len()` | 返回编码后的字节长度，不是字符数。 |
| `as_encoded_bytes()` | 取出编码后的字节切片，用于同进程传递。 |
| `is_ascii()` | 判断所有字节是否都在 ASCII 范围内。 |
| `make_ascii_lowercase()` | 原地把 ASCII 字母转成小写。 |
| `make_ascii_uppercase()` | 原地把 ASCII 字母转成大写。 |
| `to_ascii_lowercase()` | 返回 ASCII 小写副本，原值不变。 |
| `to_ascii_uppercase()` | 返回 ASCII 大写副本，原值不变。 |
| `eq_ignore_ascii_case(other)` | 忽略 ASCII 大小写比较是否相等。 |

## 示例

```rust
use std::ffi::{OsStr, OsString};

fn main() {
    // 预先估好容量，后续 push 不会反复分配
    let mut s = OsString::with_capacity(16);
    s.push("tmp");
    s.push(OsStr::new(".log"));

    assert_eq!(s.len(), 7);
    assert!(!s.is_empty());
    assert!(s.to_str().is_some());
    assert_eq!(&*s.to_string_lossy(), "tmp.log");

    // 原地把 ASCII 字母改成大写
    s.make_ascii_uppercase();
    assert_eq!(s.as_os_str(), OsStr::new("TMP.LOG"));

    // 转回 String 不会丢数据：失败时原 OsString 会回到 Err 里
    let text: String = s.clone().into_string().unwrap();
    assert_eq!(text, "TMP.LOG");

    // 需要字节时用 into_encoded_bytes
    let bytes = s.into_encoded_bytes();
    assert_eq!(bytes.as_slice(), b"TMP.LOG");
}
```

## 常见陷阱

1. **拿它当 `String` 用**：`OsString` 不支持 `&s[..]` 下标和切片，也不保证 UTF-8；要按字符处理先 `to_str()` 转成 `&str`。
2. **`into_string()` 直接 `unwrap()`**：非 UTF-8 内容会返回 `Err(OsString)`，请用 `match` 或 `map_err` 处理，数据本身不会丢。
3. **把它直接交给 C 函数**：`OsString` 没有结尾 NUL，必须改走 [[ffi.CString|CString]]。
4. **用 `push` 拼路径**：它只是字符串追加，不会补分隔符；拼路径请用 [[path.PathBuf|PathBuf]] 的 `push`。
5. **以为 `with_capacity` 是精确值**：它只保证「至少」，实际容量可能更大，且单位是编码字节。

## 相关

- [[ffi.OsStr|OsStr]]：借用版本，`OsString` 通过 `Deref` 提供它的全部方法。
- [[ffi|std::ffi]]：本条目所属模块，还有 `CString`、`CStr`。
- [[ffi.CString|CString]]：真正面向 C 接口的 NUL 结尾字符串。
- [[path.PathBuf|PathBuf]]：内部就是 `OsString`，专门表示路径。
- [[13-字符串|字符串]]：`String`、`str`、`OsString`、`OsStr` 的关系与转换。
