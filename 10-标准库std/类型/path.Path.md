---
title: "std::path::Path"
type: std-条目
kind: 结构体
module: path
slug: path.Path
stable: "1.0.0"
tags:
  - std/类型
aliases:
  - Path
一句话: 借用的路径切片，负责拆分、判断与拼接路径，本身不拥有内存。
---

# `Path`

> [!abstract] 一句话
> `Path` 是对一段路径的**借用视图**，相当于路径世界的 `str`：可以拆分分量、取文件名和扩展名、判断绝对/相对，但真正持有字符串的是 [[path.PathBuf|PathBuf]]。

## 简介

`Path` 是**未定长类型**（unsized），和 `str`、`[T]` 一样不能直接放在变量里，只能通过 `&Path`、`Box<Path>` 这类指针使用。它内部包着一个 [[ffi.OsStr|OsStr]]，因此路径**不要求是合法 UTF-8**——这正是它能表达任意操作系统文件名的原因。

日常写法是先 `Path::new("dir/file.txt")` 得到 `&Path`，需要修改或保存时再 `to_path_buf()` 转成拥有所有权的 [[path.PathBuf|PathBuf]]。`PathBuf` 实现了 `Deref<Target = Path>`，所以下面所有方法在 `PathBuf` 上也能直接调用。

关于分隔符：Unix 只认 `/`，Windows 同时接受 `/` 和 `\`。所以**不要手写分隔符**，拼接用 `join()`，遍历用 `components()`。路径比较也是按「分量」而不是按字节进行的，例如 `Path::new("a/b")` 与 `Path::new("a/b/")` 相等。

`Path` 只是字符串层面的类型，`exists`、`is_file`、`read_dir` 这类方法会真的去访问文件系统。

## 常用方法

### 构造与转换

| 方法 | 说明 |
| --- | --- |
| `new(s)` | 把字符串或 `OsStr` 包装成 `&Path` 切片。 |
| `as_os_str()` | 取出底层的 `&OsStr` 视图。 |
| `as_mut_os_str()` | 取出底层 `OsStr` 的可变引用。 |
| `to_str()` | 是合法 UTF-8 时返回 `Some(&str)`。 |
| `to_string_lossy()` | 转换为 `Cow<str>`，非法字节被替换。 |
| `to_path_buf()` | 复制成拥有所有权的 `PathBuf`。 |
| `into_path_buf()` | 把 `Box<Path>` 零拷贝地转成 `PathBuf`。 |
| `display()` | 返回可安全打印非 Unicode 路径的包装。 |

### 拆解与判断

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
| `components()` | 迭代各分量，区分根、`..` 与普通段。 |
| `iter()` | 按分量迭代，每次给出 `&OsStr`。 |

### 拼接与比较

| 方法 | 说明 |
| --- | --- |
| `strip_prefix(base)` | 去掉 `base` 前缀，失败返回 `Err`。 |
| `starts_with(base)` | 判断 `base` 是否为自身的前缀分量。 |
| `ends_with(child)` | 判断 `child` 是否为自身的后缀分量。 |
| `join(path)` | 追加一段路径并返回新的 `PathBuf`。 |
| `with_file_name(name)` | 返回替换文件名后的新 `PathBuf`。 |
| `with_extension(ext)` | 返回替换扩展名后的新 `PathBuf`。 |
| `with_added_extension(ext)` | 返回在现有扩展名后再追加扩展名的 `PathBuf`。 |

### 文件系统查询

| 方法 | 说明 |
| --- | --- |
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
use std::ffi::OsStr;
use std::path::Path;

fn main() {
    // 用 join 拼接，避免手写分隔符（Windows 是 `\`）
    let path = Path::new("docs").join("note.txt");

    assert_eq!(path.file_name(), Some(OsStr::new("note.txt")));
    assert_eq!(path.file_stem(), Some(OsStr::new("note")));
    assert_eq!(path.extension(), Some(OsStr::new("txt")));
    assert_eq!(path.parent(), Some(Path::new("docs")));

    // 前后缀按「分量」匹配，与分隔符写法无关
    assert!(path.starts_with("docs"));
    assert!(path.ends_with("note.txt"));
    assert!(path.is_relative());
    assert!(!path.is_empty());

    // 逐级列出祖先目录
    let names: Vec<String> = path.ancestors().map(|p| p.display().to_string()).collect();
    println!("祖先：{:?}", names);
}
```

## 常见陷阱

1. **手写字符串拼路径**：`format!("{}/{}", a, b)` 在 Windows 上会产生混合分隔符；拼接请用 `Path::new(a).join(b)`。
2. **对 `to_str()` 无脑 `unwrap()`**：路径可能不是合法 UTF-8（尤其 Unix 下的旧文件名），展示用 `display()` 或 `to_string_lossy()`。
3. **误以为 `starts_with` 是字符串前缀**：它按分量比较，`Path::new("foobar/x").starts_with("foo")` 是 `false`。
4. **`join` 一个绝对路径**：绝对路径会**替换**整个路径，`Path::new("a").join("/b")` 得到 `/b`；拼接前先判断 `is_absolute()`。
5. **用 `exists()` 做分支判断**：它把「不存在」和「无权限」都当成 `false`，还容易踩到 TOCTOU；需要区分错误时用 `try_exists()`。

## 相关

- [[path.PathBuf|PathBuf]]：拥有所有权的路径，`Path` 的可变版本。
- [[path|std::path]]：本条目所属模块，还有 `Component`、`Components` 等类型。
- [[ffi.OsStr|OsStr]]：`Path` 的底层表示，处理非 UTF-8 路径时直接打交道。
- [[fs|std::fs]]：真正读写文件、遍历目录的模块。
- [[13-字符串|字符串]]：`OsStr` / `str` / `String` 三者的关系。
