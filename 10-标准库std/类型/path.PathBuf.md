---
title: "std::path::PathBuf"
type: std-条目
kind: 结构体
module: path
slug: path.PathBuf
stable: "1.0.0"
tags:
  - std/类型
aliases:
  - PathBuf
一句话: 拥有所有权的可变路径，用 push、pop、set_extension 原地修改，并可自动解引用成 Path。
---

# `PathBuf`

> [!abstract] 一句话
> `PathBuf` 是**拥有所有权、可原地修改**的路径，相当于路径世界的 `String`；它内部是一个 [[ffi.OsString|OsString]]，并通过 `Deref` 把 [[path.Path|Path]] 的全部方法都借用过来。

## 简介

需要「先把路径拼起来，之后再交给别的函数」时就用 `PathBuf`：它自己持有内存，可以 `push`、`pop`、`set_extension`，不需要像 `&Path` 那样担心生命周期。反过来，只需要读路径的接口应该接收 `&Path`（或 `AsRef<Path>`），这样 `&Path`、`PathBuf`、`&str`、`String` 都能传进来。

`PathBuf` 实现了 `Deref<Target = Path>` 和 `DerefMut`，因此 `parent()`、`file_stem()`、`components()`、`starts_with()` 等 [[path.Path|Path]] 方法在 `PathBuf` 上可以直接调用，不需要先转换。要长期保存一份路径就用 `to_path_buf()` 复制，要交出底层数据就用 `into_os_string()`。

几个容易混淆的点：

- `push` 是**按路径分量追加**，会自动插入分隔符，而不是字符串拼接；传入绝对路径会**替换**整个路径。
- 底层是 [[ffi.OsString|OsString]]，所以路径允许是非 UTF-8；要 `&str` 用 `to_str()`（返回 `Option`）或 `to_string_lossy()`。
- 它**不是** NUL 结尾的，传给 C 接口前要先转成 [[ffi.CString|CString]]。

## 常用方法

### 构造与容量

| 方法 | 说明 |
| --- | --- |
| `new()` | 创建一个空的 `PathBuf`，不分配内存。 |
| `with_capacity(capacity)` | 创建容量至少为 `capacity` 的空 `PathBuf`。 |
| `capacity()` | 返回无需扩容即可容纳的字节数。 |
| `clear()` | 清空内容，长度归零但保留容量。 |
| `reserve(additional)` | 预留至少 `additional` 字节的额外容量。 |
| `try_reserve(additional)` | 预留容量的可失败版本，返回 `Result`。 |
| `reserve_exact(additional)` | 精确预留至少 `additional` 字节容量。 |
| `try_reserve_exact(additional)` | 精确预留容量的可失败版本。 |
| `shrink_to_fit()` | 把容量收缩到刚好等于当前长度。 |
| `shrink_to(min_capacity)` | 把容量收缩到不低于给定下界。 |

### 修改与拼接

| 方法 | 说明 |
| --- | --- |
| `push(path)` | 追加一段路径，必要时自动补分隔符。 |
| `pop()` | 删除最后一个分量，成功返回 `true`。 |
| `set_file_name(name)` | 原地替换最后的分量（文件名）。 |
| `set_extension(ext)` | 原地替换扩展名，传空串则删除扩展名。 |
| `add_extension(ext)` | 在已有扩展名之后再追加一段扩展名。 |
| `join(path)` | 追加路径并返回新的 `PathBuf`，不改自身。 |
| `with_file_name(name)` | 返回替换文件名后的新 `PathBuf`。 |
| `with_extension(ext)` | 返回替换扩展名后的新 `PathBuf`。 |
| `with_added_extension(ext)` | 返回追加扩展名后的新 `PathBuf`。 |

### 转换与借用

| 方法 | 说明 |
| --- | --- |
| `as_path()` | 强制转换成 `&Path` 切片。 |
| `as_os_str()` | 取出底层的 `&OsStr` 视图。 |
| `as_mut_os_str()` | 取出底层 `OsStr` 的可变引用。 |
| `as_mut_os_string()` | 取出底层 `OsString` 的可变引用。 |
| `to_str()` | 是合法 UTF-8 时返回 `Some(&str)`。 |
| `to_string_lossy()` | 转换为 `Cow<str>`，非法字节被替换。 |
| `to_path_buf()` | 复制成新的 `PathBuf`（`Clone` 的显式写法）。 |
| `into_os_string()` | 消耗自身，交出内部的 `OsString`。 |
| `into_string()` | 转成 `String`，失败时把 `PathBuf` 还回 `Err`。 |
| `into_boxed_path()` | 转成 `Box<Path>`，不重新分配。 |
| `leak()` | 泄漏内存，得到 `&'static mut Path`。 |
| `display()` | 返回可安全打印非 Unicode 路径的包装。 |

### 拆解、判断与文件系统

| 方法 | 说明 |
| --- | --- |
| `is_absolute()` | 判断是否为绝对路径。 |
| `is_relative()` | 判断是否为相对路径。 |
| `has_root()` | 判断是否带根，如 `/` 或 `C:\`。 |
| `is_empty()` | 判断路径字符串是否为空。 |
| `parent()` | 返回去掉最后一个分量的父路径。 |
| `ancestors()` | 迭代自身以及各级父路径。 |
| `file_name()` | 返回最后一个分量的文件名。 |
| `file_stem()` | 返回不含扩展名的文件名主干。 |
| `file_prefix()` | 返回文件名中扩展名之前的前缀部分。 |
| `extension()` | 返回扩展名（不含点），没有则 `None`。 |
| `strip_prefix(base)` | 去掉 `base` 前缀，失败返回 `Err`。 |
| `starts_with(base)` | 判断 `base` 是否为自身的前缀分量。 |
| `ends_with(child)` | 判断 `child` 是否为自身的后缀分量。 |
| `components()` | 迭代各分量，区分根、`..` 与普通段。 |
| `iter()` | 按分量迭代，每次给出 `&OsStr`。 |
| `metadata()` | 查询元数据，跟随符号链接。 |
| `symlink_metadata()` | 查询元数据，但不跟随符号链接。 |
| `canonicalize()` | 返回规范化绝对路径并解析符号链接。 |
| `read_link()` | 读取符号链接指向的目标路径。 |
| `read_dir()` | 返回目录项的迭代器。 |
| `exists()` | 判断路径是否存在。 |
| `try_exists()` | 存在性检查的可失败版本，返回 `Result<bool>`。 |
| `is_file()` | 判断是否存在且为普通文件。 |
| `is_dir()` | 判断是否存在且为目录。 |
| `is_symlink()` | 判断是否存在且为符号链接。 |

## 示例

```rust
use std::path::{Path, PathBuf};

fn main() {
    // 从空路径开始逐段拼装
    let mut path = PathBuf::new();
    path.push(Path::new("src"));
    path.push("main.rs");
    assert_eq!(path.components().count(), 2);
    assert_eq!(path.extension().and_then(|e| e.to_str()), Some("rs"));

    // 原地改扩展名，注意 PathBuf 的方法会修改自身
    path.set_extension("toml");
    assert_eq!(path.file_name().and_then(|n| n.to_str()), Some("main.toml"));

    // pop 去掉最后一个分量，回到父目录
    assert!(path.pop());
    assert_eq!(path, PathBuf::from("src"));

    // 也可以直接从迭代器收集
    let built: PathBuf = ["src", "lib.rs"].iter().collect();
    assert_eq!(built.file_name().and_then(|n| n.to_str()), Some("lib.rs"));

    // 需要 &Path 时用 as_path，不需要复制
    let slice: &Path = built.as_path();
    assert!(slice.is_relative());
    println!("路径：{}", built.display());
}
```

## 常见陷阱

1. **把 `push` 当字符串拼接**：`push` 会按分量追加并补分隔符，传入绝对路径还会替换整个路径；纯文本拼接请自己 `format!`。
2. **分不清 `set_extension` 与 `add_extension`**：前者替换，后者追加；`set_extension("")` 会**删除**扩展名，这也是清掉 `.rs` 的正规写法。
3. **对 `to_str()` 直接 `unwrap()`**：非 UTF-8 路径会 panic，日志和界面展示请用 `display()`。
4. **在需要 `&Path` 的地方传 `PathBuf` 的引用**：直接传 `&path` 即可（`Deref` 强制转换），函数参数写成 `impl AsRef<Path>` 更通用。
5. **`into_os_string()` 之后继续使用原变量**：它按值消耗 `self`，需要保留就改用 `as_os_str()` 或先 `clone()`。

## 相关

- [[path.Path|Path]]：借用的路径切片，`PathBuf` 通过 `Deref` 提供它的全部方法。
- [[path|std::path]]：本条目所属模块。
- [[ffi.OsString|OsString]]：`PathBuf` 的内部存储类型。
- [[fs|std::fs]]：接收 `Path` / `PathBuf` 做实际文件操作。
- [[13-字符串|字符串]]：理解 `String`、`OsString`、`PathBuf` 三者的层次关系。
