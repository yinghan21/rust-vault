---
title: "std::ffi::OsStr"
type: std-条目
kind: 结构体
module: ffi
slug: ffi.OsStr
stable: "1.0.0"
tags:
  - std/类型
  - std/IO
aliases:
  - OsStr
一句话: 借用的操作系统原生字符串切片，允许非 UTF-8 字节，是 Path 与 OsString 的桥梁。
---

# `OsStr`

> [!abstract] 一句话
> `OsStr` 是**借用的操作系统原生字符串**，`&OsStr` 之于 [[ffi.OsString|OsString]]，就像 `&str` 之于 `String`；它不保证是合法 UTF-8，因此能安全承载任意文件名和命令行参数。

## 简介

Rust 的 `str`/`String` 要求内容是合法 UTF-8，但操作系统并不这样要求：Unix 的文件名是任意字节序列（只排除 `/` 和 NUL），Windows 用的是 UTF-16 的扩展形式。`OsStr` 就是这两者之间的公共视图——它保存「平台原生表示」，同时允许在需要时零成本地当作 Rust 字符串使用。

典型用途：

- 从 [[env.args|args]]、环境变量、目录项里拿到字符串后，**先当作 `OsStr` 保存**，只在确实需要文本处理时才转 `&str`。
- 作为 [[path.Path|Path]] 和 [[path.PathBuf|PathBuf]] 的底层表示：路径的每个分量（`file_name`、`extension`）都是 `&OsStr`。
- 传给 [[process.Command|Command]] 的参数也是 `AsRef<OsStr>`。

和 `&str` 的转换有三档：`to_str()` 严格校验、返回 `Option`；`to_string_lossy()` 宽松、非法字节替换成 `U+FFFD` 并返回 `Cow<str>`；`as_encoded_bytes()` 则拿到原始编码字节，配合 `from_encoded_bytes_unchecked` 做同进程内的往返。

`OsStr` 是未定长类型，只能以 `&OsStr` 或 `Box<OsStr>` 的形式出现。

## 常用方法

### 构造与转换

| 方法 | 说明 |
| --- | --- |
| `new(s)` | 把字符串包装成借用的 `&OsStr`。 |
| `from_encoded_bytes_unchecked(bytes)` | 未检查地把字节切片还原为 `&OsStr`。 |
| `to_str()` | 是合法 UTF-8 时返回 `Some(&str)`。 |
| `to_string_lossy()` | 转换为 `Cow<str>`，非法字节被替换。 |
| `to_os_string()` | 复制成拥有所有权的 `OsString`。 |
| `into_os_string()` | 把 `Box<OsStr>` 零拷贝转成 `OsString`。 |
| `as_encoded_bytes()` | 取出编码后的字节切片，用于同进程传递。 |
| `display()` | 返回可安全打印非 Unicode 内容的包装。 |

### 长度与 ASCII 操作

| 方法 | 说明 |
| --- | --- |
| `is_empty()` | 判断字符串是否为空。 |
| `len()` | 返回编码后的字节长度，不是字符数。 |
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
    let s = OsStr::new("Hello.txt");

    // len 是字节数，is_empty 看长度是否为 0
    assert_eq!(s.len(), 9);
    assert!(!s.is_empty());
    assert!(s.is_ascii());

    // 严格转换与宽松转换
    assert_eq!(s.to_str(), Some("Hello.txt"));
    assert_eq!(&*s.to_string_lossy(), "Hello.txt");

    // ASCII 大小写比较，与 to_ascii_lowercase 配合使用
    assert!(s.eq_ignore_ascii_case("hello.TXT"));

    // 借用的 OsStr 可以复制成拥有所有权的 OsString
    let owned: OsString = s.to_os_string();
    assert_eq!(owned, OsString::from("Hello.txt"));

    // 只有 ASCII 字母会被改写，其他字节原样保留
    let lower: OsString = s.to_ascii_lowercase();
    assert_eq!(lower, OsString::from("hello.txt"));

    // 与 &str 直接比较也可以，不必先转换
    assert_eq!(OsStr::new("tmp"), "tmp");
}
```

## 常见陷阱

1. **把 `to_str()` 当作必然成功**：非 UTF-8 路径（Unix 上很常见）会返回 `None`，`unwrap()` 直接 panic；展示请用 `display()` 或 `to_string_lossy()`。
2. **把 `len()` 当字符数**：它返回编码字节数，`OsStr::new("中文").len()` 是 6 而不是 2。
3. **拿 `as_encoded_bytes()` 的结果做持久化**：字节格式不保证跨平台、跨版本稳定，只适合在同一程序内立即往返。
4. **随手用 `from_encoded_bytes_unchecked`**：它是 `unsafe`，字节必须来自同一程序里 `as_encoded_bytes()` 的结果，否则行为未定义。
5. **想按下标切片**：`OsStr` 不支持 `&s[0..2]`，要切分请先转成 `&str` 或字节切片。
6. **指望 `to_ascii_uppercase` 处理非英文字符**：它只转换 ASCII 的 `a-z`，中文、德文变音等一个字节都不会动。

## 相关

- [[ffi.OsString|OsString]]：拥有所有权的对应类型。
- [[ffi|std::ffi]]：本条目所属模块。
- [[path.Path|Path]]：直接构建在 `OsStr` 之上的路径切片。
- [[string.String|String]]：必须合法 UTF-8 的字符串，和 `OsStr` 互相转换。
- [[24-unsafe 与 FFI|unsafe 与 FFI]]：`from_encoded_bytes_unchecked` 等 `unsafe` 接口的前置知识。
