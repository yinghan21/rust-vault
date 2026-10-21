---
title: "std::fs::OpenOptions"
type: std-条目
kind: 结构体
module: fs
slug: fs.OpenOptions
stable: "1.0.0"
tags:
  - std/类型
  - std/IO
aliases:
  - OpenOptions
一句话: 用链式调用配置文件的打开方式，再一次性打开成 File 的构建器。
---

# `OpenOptions`

> [!abstract] 一句话
> `OpenOptions` 是打开文件的**选项构建器**：先 `new()` 得到空白配置，逐个设置读/写/追加/创建，最后 `open(path)` 拿到 [[fs.File|File]]。

## 简介

[[fs.File|File]] 上只有 `open`、`create`、`create_new` 三个便捷入口，它们其实是 `OpenOptions` 的固定组合。需要「读写同开」「追加写入」「不存在才创建」「清空但不截断」这类组合时，就必须自己搭一套选项。

用法固定为三步：`OpenOptions::new()` → 链式设置开关 → `open(path)`。每个设置方法都接收 `bool` 并返回 `&mut Self`，所以可以连续点下去，最后一步 `open` 借用配置完成打开。

几个开关会互相影响：只写但既没 `create` 也没 `truncate` 时，文件不存在会报错、存在则从开头覆盖；`append(true)` 会让每次写入都落到文件末尾，与当前定位无关；`create_new(true)` 要求同时设置 `write(true)` 或 `append(true)`，否则打开会失败。

## 常用方法

### 构造

| 方法 | 说明 |
| --- | --- |
| `new()` | 创建空白的选项集合，默认不允许读写。 |

### 访问模式

| 方法 | 说明 |
| --- | --- |
| `read(read)` | 设置是否允许读取。 |
| `write(write)` | 设置是否允许写入。 |
| `append(append)` | 设置追加模式，写入总在文件末尾。 |
| `truncate(truncate)` | 设置打开时是否清空已有内容。 |

### 创建策略

| 方法 | 说明 |
| --- | --- |
| `create(create)` | 文件不存在时创建，存在则沿用。 |
| `create_new(create_new)` | 只在文件不存在时创建，否则报错。 |

### 打开

| 方法 | 说明 |
| --- | --- |
| `open(path)` | 按当前选项打开路径，返回 `File`。 |

## 示例

```rust
use std::fs::OpenOptions;
use std::io::{Read, Seek, SeekFrom, Write};
use std::path::PathBuf;

fn main() -> std::io::Result<()> {
    let mut path: PathBuf = std::env::temp_dir();
    path.push("rust_open_options_demo.txt");
    let _ = std::fs::remove_file(&path); // 清掉上次残留，保证 create_new 成功

    // 只写 + 仅新建：文件已存在就返回错误
    let mut f = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&path)?;
    f.write_all(b"line1")?;
    drop(f);
    assert!(OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&path)
        .is_err());

    // 追加模式：不清空原内容，写到末尾
    let mut f = OpenOptions::new().append(true).open(&path)?;
    f.write_all(b",line2")?;
    drop(f);

    // 读写同开，再定位回开头读
    let mut f = OpenOptions::new().read(true).write(true).open(&path)?;
    f.seek(SeekFrom::Start(0))?;
    let mut s = String::new();
    f.read_to_string(&mut s)?;
    assert_eq!(s, "line1,line2");

    drop(f);
    std::fs::remove_file(&path)?;
    Ok(())
}
```

## 常见陷阱

1. **忘记设置任何访问模式**：`OpenOptions::new().open(path)` 会直接报错，至少要 `read(true)` 或 `write(true)`。
2. **`write(true)` 不带 `truncate` 不会清空**：新内容从第 0 字节覆盖，旧文件更长时会留下尾巴，需要清空就加 `truncate(true)`。
3. **`append(true)` 让定位失效**：即使先 `seek` 到中间，写入仍然落在末尾，别指望用 `Seek` 在追加模式里改中间内容。
4. **`create_new` 缺写权限会失败**：它要求配合 `write(true)` 或 `append(true)`，只设 `read(true)` 会得到错误而不是新文件。
5. **`create(true)` 不等于清空**：它只在文件缺失时创建，想要「空的文件」请改用 `File::create` 或显式 `truncate(true)`。

## 相关

- [[fs|std::fs 模块]]：文件系统相关条目总览。
- [[fs.File|File]]：`open` 的返回类型，也是 `File::options` 的来源。
- [[io.BufReader|BufReader]]、[[io.BufWriter|BufWriter]]：给打开后的句柄加缓冲。
- [[path.Path|Path]]：`open` 的路径参数类型。
- [[11-错误处理|错误处理]]：打开失败时如何区分「不存在」「无权限」等错误。
