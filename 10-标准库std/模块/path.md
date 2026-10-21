---
title: "std::path"
type: std-模块
module: path
stable: "1.0.0"
unstable: false
tags:
  - std/模块
  - std/IO
aliases:
  - path
一句话: 跨平台路径处理：用 PathBuf 拥有、用 Path 借用，逐段解析、拼接、取后缀、去前缀。
---

# std::path

> [!abstract] 一句话
> `std::path` 是路径版的 `String` / `str`：`PathBuf` 拥有并可修改，`Path` 是借用的路径切片，两者直接按平台语法工作，不要求内容是合法 UTF-8。

## 模块简介

模块只围绕两个类型转：`PathBuf` 对应 `String`（拥有、可增长、可修改），`Path` 对应 `str`（借用的、不定长的视图）。它们分别是对 `OsString` / `OsStr` 的薄包装，所以路径里可以出现任何平台允许的字节，不一定是合法 UTF-8——这也是为什么路径不能直接当 `String` 用。

`Path` 可以被拆成 `Component`：调用 `components()` 得到一个迭代器，每个分量大致对应分隔符之间的那一段，并区分根目录、当前目录、父目录、Windows 前缀、普通片段。反过来，用 `PathBuf::push` 把分量重新拼起来就能得到等价路径，但**语法上不一定逐字符相同**（`components` 会做归一化，比如合并重复分隔符、消掉中间的 `.`）。需要逐段比较时比的是分量，不是字符串。

`Path` 上大多数方法**完全不访问文件系统**：`starts_with`、`ends_with`、`is_absolute`、`extension`、`join`、`strip_prefix` 都是纯字面计算，因此它们是区分大小写的（Windows 盘符除外）。真要问「这个文件在不在、是不是目录」，得用 [[fs|std::fs]] 的 `metadata`、`read_dir` 等函数。

平台差异被收敛成几个常量：`MAIN_SEPARATOR` 是当前平台的主分隔符（Unix 是 `/`，Windows 是 `\`），`SEPARATORS` 列出所有被接受的分隔符（Windows 上 `\` 和 `/` 都算）。写跨平台代码就用 `PathBuf::push` / `join`，别手拼字符串。

## 快速上手

```rust
use std::path::{Path, PathBuf};

fn main() {
    // 1. 用 PathBuf 一步步拼路径，分隔符由平台决定
    let mut p = PathBuf::from("data");
    p.push("reports");
    p.push("2025.txt");
    println!("拼接结果：{}", p.display());

    // 2. 借用成 &Path，不复制底层的字符串
    let path: &Path = p.as_path();
    assert_eq!(path.file_stem().unwrap(), "2025");
    assert_eq!(path.extension().unwrap(), "txt");
    assert_eq!(path.parent().unwrap(), Path::new("data").join("reports"));

    // 3. 逐段解析：Component 大致对应分隔符之间的片段
    let parts: Vec<String> = path
        .components()
        .map(|c| c.as_os_str().to_string_lossy().into_owned())
        .collect();
    println!("分量：{parts:?}");

    // 4. 去掉前缀，得到相对路径
    let relative = path.strip_prefix("data").unwrap();
    assert_eq!(relative, Path::new("reports").join("2025.txt"));

    // 5. 转成绝对路径，不访问文件系统
    let absolute = std::path::absolute(path).unwrap();
    assert!(absolute.is_absolute());

    // 6. 不一定能转成 &str：文件名可能不是合法 UTF-8
    match path.to_str() {
        Some(text) => println!("可以直接当 &str 用：{text}"),
        None => println!("含非 UTF-8 字节，只能用 display 或 to_string_lossy"),
    }
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[path.PathBuf\|PathBuf]] | 拥有的可变路径，相当于 `String`。 |
| [[path.Path\|Path]] | 借用的路径切片，相当于 `str`。 |
| `Path::components` | 按分量迭代，返回 `Components`。 |
| `Component` | 单个分量：根、当前目录、父目录、前缀、普通片段。 |
| `Path::join` / `PathBuf::push` | 拼接路径，绝对路径会替换掉已有前缀。 |
| `Path::parent` / `file_name` / `file_stem` / `extension` | 取父目录、文件名、主干、后缀。 |
| `Path::display` | 得到可安全打印的包装（非 UTF-8 会显示替换字符）。 |
| `Path::to_str` / `to_string_lossy` | 尝试转成 `&str` / 宽松转成 `Cow<str>`。 |
| `Path::strip_prefix` | 去掉指定前缀，失败返回 `StripPrefixError`。 |
| `Path::starts_with` / `ends_with` | 按分量判断前缀 / 后缀。 |
| `Path::ancestors` | 从自身一路向上遍历到根。 |
| `std::path::absolute` | 拼成绝对路径，但不解析符号链接、不访问文件系统。 |
| [[ffi.OsStr\|OsStr]] / [[ffi.OsString\|OsString]] | 路径底层的 OS 字符串类型。 |
| `MAIN_SEPARATOR` / `MAIN_SEPARATOR_STR` | 当前平台的主分隔符，`char` 与 `&str` 两种形式。 |
| `SEPARATORS` / `is_separator` | 当前平台接受的全部分隔符 / 判断某个字符是不是分隔符。 |

## 注意事项

> [!warning] 别用字符串拼接路径
> `format!("{}/{}/{}", a, b, c)` 在 Windows 上虽然常能工作（Windows 接受 `/`），但会破坏「绝对路径替换」等语义，也处理不了非 UTF-8 文件名。统一用 `PathBuf::push` / `Path::join`；要输出给人看时套一层 `display()`。

> [!danger] 路径不等于文件
> `Path::new("x").is_absolute()`、`starts_with`、`ends_with` 全部是字面比较，不查磁盘，也不认大小写；一个路径「存在」与否必须问 [[fs|std::fs]]。反过来，`exists()` 这类要访问磁盘的检查有竞态：判断完到真正打开之间文件可能已被删掉，能直接操作就别先检查。

> [!tip] `Path` 的同名结构体是打印辅助
> `std::path::Display` 是 `display()` 返回的那个包装结构体，和 `std::fmt::Display` trait 同名但毫无关系；写 `use std::path::*;` 时容易撞名，建议按需导入具体名字。

## 相关

- [[fs|std::fs]]：路径只有配合文件系统操作才有意义。
- [[env|std::env]]：当前目录、临时目录、可执行文件路径都从这里来。
- [[ffi|std::ffi]]：`OsStr` / `OsString` 的完整说明。
- [[primitive.str|str]]：`Path` 与 `str` 的对照关系，理解「切片类型」的套路。
- [[io|std::io]]：打开文件后就是 `io` 的读写世界。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 17 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`Ancestors`](https://doc.rust-lang.org/std/path/struct.Ancestors.html)
- [`Components`](https://doc.rust-lang.org/std/path/struct.Components.html)
- [`Display`](https://doc.rust-lang.org/std/path/struct.Display.html)
- [`Iter`](https://doc.rust-lang.org/std/path/struct.Iter.html)
- [[path.Path|`Path`]]
- [[path.PathBuf|`PathBuf`]]
- [`PrefixComponent`](https://doc.rust-lang.org/std/path/struct.PrefixComponent.html)
- [`StripPrefixError`](https://doc.rust-lang.org/std/path/struct.StripPrefixError.html)
- [`NormalizeError`](https://doc.rust-lang.org/std/path/struct.NormalizeError.html)

### 枚举

- [`Component`](https://doc.rust-lang.org/std/path/enum.Component.html)
- [`Prefix`](https://doc.rust-lang.org/std/path/enum.Prefix.html)

### 函数

- [`absolute`](https://doc.rust-lang.org/std/path/fn.absolute.html)
- [`is_separator`](https://doc.rust-lang.org/std/path/fn.is_separator.html)

### 常量

- [`MAIN_SEPARATOR`](https://doc.rust-lang.org/std/path/constant.MAIN_SEPARATOR.html)
- [`MAIN_SEPARATOR_STR`](https://doc.rust-lang.org/std/path/constant.MAIN_SEPARATOR_STR.html)
- [`SEPARATORS`](https://doc.rust-lang.org/std/path/constant.SEPARATORS.html)
- [`SEPARATORS_STR`](https://doc.rust-lang.org/std/path/constant.SEPARATORS_STR.html)

<!-- END AUTO ITEMS -->
