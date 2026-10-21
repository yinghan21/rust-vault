---
title: "std::fs::read_to_string"
type: std-条目
kind: 函数
module: fs
slug: fs.read_to_string
stable: "1.26.0"
tags:
  - std/IO
  - std/类型
aliases:
  - "read_to_string"
  - "fs::read_to_string"
一句话: "一次性把一个文件的全部内容读成 String，文件不存在或内容不是合法 UTF-8 都返回 Err。"
---

# `read_to_string`

> [!abstract] 一句话
> `std::fs::read_to_string(path)` 打开文件、把全部字节读进内存、按 UTF-8 校验后返回 `String`。它是 `File::open` 加 `read_to_string` 的便捷组合，省掉中间变量和几行 `use`。

## 简介

读一个文本文件是脚本、配置加载、模板处理里最常见的 IO 操作。手动写法是 `File::open(path)?` 拿 `File`，再 `file.read_to_string(&mut s)?`，还得 `use std::io::Read`；`fs::read_to_string` 把这三步包成一个函数，返回 `io::Result<String>`。

参数是 `P: AsRef<Path>`，所以 `&str`、`String`、`PathBuf`、`&Path` 都能直接传，不必先转成 `Path`。返回值要么是完整的 `String`，要么是 `Err`——**不会返回半个文件**：内部会把所有字节读进一个 `Vec<u8>`，最后统一做 UTF-8 校验，失败时整个结果作废。

三种错误最常见：路径不存在（`ErrorKind::NotFound`）、权限不足（`PermissionDenied`）、内容不是合法 UTF-8（`InvalidData`，消息形如 `stream did not contain valid UTF-8`）。注意它**不做换行符转换**：Windows 的 `\r\n` 会原样留在字符串里，逐行处理用 `str::lines()`，它会自动去掉行尾的 `\r`。

需要字节而不是文本时用 `fs::read`；需要读超大文件、不能全塞进内存时，改用 [[io.BufReader|BufReader]] 逐行读；要读的是标准输入而不是文件，用 `io::read_to_string` 或 `io::stdin()`。

## 签名与参数

```text
pub fn read_to_string<P: AsRef<Path>>(path: P) -> io::Result<String>
```

| 参数 | 说明 |
| --- | --- |
| `path` | 文件路径，`&str`、`String`、`PathBuf`、`&Path` 都可以（实现 `AsRef<Path>`）。 |
| 返回 `Ok(String)` | 文件全部内容构成的 UTF-8 字符串。 |
| 返回 `Err(io::Error)` | 打开/读取失败，或内容不是合法 UTF-8（`ErrorKind::InvalidData`）。 |

| 函数 | 说明 |
| --- | --- |
| `fs::read_to_string` | 读成 `String`，要求 UTF-8。 |
| `fs::read` | 读成 `Vec<u8>`，不做编码校验。 |
| `fs::write` | 对应的写入函数，整体覆盖文件内容。 |
| `io::Read::read_to_string` | 已有 `File` / `BufReader` 时的方法版。 |

## 示例

### 读文件并逐行处理

```rust
use std::fs;

fn main() -> std::io::Result<()> {
    let path = "demo_read.txt";
    fs::write(path, "hello\nworld\n")?;

    let text = fs::read_to_string(path)?;
    assert_eq!(text, "hello\nworld\n");
    assert_eq!(text.lines().count(), 2);
    assert_eq!(text.lines().next(), Some("hello"));

    fs::remove_file(path)?;
    println!("读到了 {} 字节", text.len());
    Ok(())
}
```

### 两类典型错误

```rust
use std::fs;
use std::io::ErrorKind;

fn main() {
    // 1. 文件不存在
    let e = fs::read_to_string("绝对不存在的文件.txt").unwrap_err();
    assert_eq!(e.kind(), ErrorKind::NotFound);

    // 2. 内容不是合法 UTF-8：二进制文件、图片都会这样
    let bin = "demo_invalid_utf8.bin";
    fs::write(bin, [0xffu8, 0xfe]).unwrap();

    let bytes = fs::read(bin).unwrap();          // 读字节没问题
    assert_eq!(bytes, vec![0xff, 0xfe]);

    let e = fs::read_to_string(bin).unwrap_err(); // 读成字符串就失败
    assert_eq!(e.kind(), ErrorKind::InvalidData);
    fs::remove_file(bin).unwrap();

    println!("{e}");
}
```

## 常见陷阱

1. **对二进制文件用它**：内容不是 UTF-8 就整体失败，图片、压缩包、`protobuf` 一律改用 `fs::read` 拿 `Vec<u8>`。
2. **忘了它会把整个文件读进内存**：几个 GB 的日志会让内存暴涨，大文件请用 [[io.BufReader|BufReader]] 加 `read_line` 逐行处理。
3. **以为行尾会被规范化**：`\r\n`、`\n` 原样保留，`text.lines()` 自动剥离行尾的 `\r`，但 `split('\n')` 不会，会留下 `\r`。
4. **路径用错当前工作目录**：相对路径以进程的工作目录为基准，而不是源码所在目录；测试与 `cargo run` 的 cwd 常常不同，用 `env::current_dir` 或绝对路径更稳。
5. **忽略 `Err` 直接 `unwrap`**：配置文件缺失是常态，应该 `match` / `unwrap_or_default` / 给出友好提示，而不是让程序 panic。
6. **当成「流式读取」用**：它把当下的全部内容一次性读完，之后文件被追加也不会反映到已有的 `String` 里，要跟随变化就得重新读。

## 相关

- [[fs|std::fs 模块]]：文件读写、目录遍历、元数据都在这里。
- [[fs.write|write]]：`read_to_string` 的写入对照函数。
- [[io.BufReader|BufReader]]：大文件逐行读的标准做法。
- [[io.Read|io::Read]]：`read_to_string` 方法的来源特质。
- [[11-错误处理|错误处理]]：`io::Result` 与 `?`、`Box<dyn Error>` 的组合用法。
