---
title: "std::write!"
type: std-条目
kind: 宏
module: std
slug: macro.write
stable: "1.0.0"
tags:
  - std/宏
aliases:
  - "write!"
  - "write 宏"
一句话: "把格式化后的数据写进任意有 write_fmt 的 writer，返回该方法的返回值（fmt::Result 或 io::Result）。"
---

# `write!`

> [!abstract] 一句话
> `write!` 把格式化结果写进一个「writer」——任何带 `write_fmt` 方法的对象，典型是实现了 `fmt::Write` 的 `String` 或实现了 `io::Write` 的 `Vec<u8>`、`File`。宏本身不返回结果值，它返回的是 `write_fmt` 的返回值：`fmt::Result` 或 `io::Result<()>`。

## 简介

`write!` 是「格式化 + 输出到指定位置」的组合。`println!` 只能打到标准输出，而 `write!` 的第一个参数决定了去何处：`String` 得到拼好的文本，`Vec<u8>` 得到字节缓冲，`File` 或 `TcpStream` 直接落盘/发网。

它有两个「write」特质，按 writer 类型二选一：

- `std::fmt::Write`：面向字符串，方法签名是 `fn write_str(&mut self, s: &str) -> fmt::Result`，`write_fmt` 返回 `fmt::Result`，即 `Result<(), fmt::Error>`。
- `std::io::Write`：面向字节流，方法签名是 `fn write(&mut self, buf: &[u8]) -> io::Result<usize>`，`write_fmt` 返回 `io::Result<()>`。

展开结果与返回值：`write!($dst, $($arg)*)` 展开为 `$dst.write_fmt(format_args!($($arg)*))`。所以宏的返回值就是那个 `write_fmt` 的返回值——对 `String` 是 `fmt::Result`，对 `Vec<u8>`/`File` 是 `io::Result<()>`。也正因为它返回 `Result`，而 `Result` 带 `#[must_use]`，直接写 `write!(s, "x");` 会得到一个「unused `Result`」警告，必须 `?`、`unwrap()` 或 `let _ =`。

`writeln!` 是同一个宏加换行。想一次性省掉多次锁/系统调用，用 [[io.BufWriter|BufWriter]] 包一层；想省掉每轮格式化分配，就复用同一个 `String` 反复 `write!`。

## 签名与参数

```text
write!($dst:expr, $($arg:tt)*) -> $dst.write_fmt(format_args!($($arg)*)) 的类型
```

| 参数 | 说明 |
| --- | --- |
| `$dst` | writer 表达式，需有 `write_fmt` 方法；传 `&mut` 借用即可，宏会原样调用方法。 |
| `$($arg)*` | 字面量格式串加若干格式化参数，语法与 `format!` 相同。 |
| 返回 `fmt::Result` | `$dst` 实现 `fmt::Write` 时（如 `String`）。 |
| 返回 `io::Result<()>` | `$dst` 实现 `io::Write` 时（如 `Vec<u8>`、`File`）。 |

| 宏 | 说明 |
| --- | --- |
| `write!` | 写格式化内容，不加换行。 |
| `writeln!` | 写格式化内容并补 `\n`，返回值同上。 |
| `print!` / `println!` | 固定写到 stdout，不返回 `Result`。 |

## 示例

### 写进 `String`：用 `std::fmt::Write`

```rust
use std::fmt::Write;

fn main() {
    let mut s = String::new();

    // 返回 fmt::Result，这里直接 unwrap
    write!(&mut s, "{} {}", "abc", 123).unwrap();
    assert_eq!(s, "abc 123");

    // 拼接多行的标准写法：复用同一个 String，避免每轮都分配
    let mut table = String::new();
    for i in 1..=3 {
        writeln!(table, "第 {i} 行").unwrap();
    }
    assert_eq!(table, "第 1 行\n第 2 行\n第 3 行\n");

    // 复用它继续追加（先算出行数，避免同时借用 table）
    let rows = table.lines().count();
    write!(&mut table, "共 {rows} 行").unwrap();
    assert!(table.ends_with("共 3 行"));

    print!("{table}");
}
```

### 写进字节缓冲：用 `std::io::Write`

```rust
use std::io::Write;

fn main() -> std::io::Result<()> {
    let mut buf: Vec<u8> = Vec::new();

    // 这里返回的是 io::Result<()>，可以直接 ?
    write!(&mut buf, "test")?;
    write!(&mut buf, "formatted {}", "arguments")?;
    assert_eq!(buf, b"testformatted arguments");

    let len = buf.len();
    writeln!(&mut buf, "{len}")?;
    assert!(buf.ends_with(b"23\n"));

    println!("缓冲区共 {} 字节", buf.len());
    Ok(())
}
```

## 常见陷阱

1. **两个 `Write` 特质同时引入**：同时 `use std::fmt::Write;` 和 `use std::io::Write;` 会报名字冲突，且 `write_fmt` 方法二义，改用 `use std::fmt::Write as _;` 加 `use std::io::Write as _;`。
2. **忘了用返回值**：`write!` 返回 `Result`，语句位置直接丢弃会触发 `unused_must_use` 警告，写 `?`、`.unwrap()` 或 `let _ =`。
3. **对 `String` 用了 `io::Write`**：`String` 不实现 `io::Write`，只能配 `fmt::Write`；要字节就往 `Vec<u8>` 或 `File` 写。
4. **忘了引入特质**：只 `use std::io::Write` 却对 `Vec<u8>` 调 `write!` 是对的，但反过来说，不引入对应特质时 `write_fmt` 找不到方法，编译报「no method named `write_fmt`」。
5. **在循环里对 `File` 逐次 `write!`**：每次一行会触发大量小写入，套一层 [[io.BufWriter|BufWriter]] 并在结尾 `flush`。
6. **把 `write!` 当作 `println!` 的替代品**：`write!` 不会自动加换行，也不会自动刷缓冲。

## 相关

- [[io.Write|io::Write]]：字节流写入特质，`File`、`Vec<u8>`、`TcpStream` 都实现它。
- [[io.BufWriter|BufWriter]]：包一层缓冲，减少 `write!` 的系统调用次数。
- [[fmt|std::fmt]]：`fmt::Write` 与格式串语法。
- [[string.String|String]]：`fmt::Write` 最常用的实现者。
- [[macro.format|format!]]：只需要拼出 `String` 时，它比 `write!` 更直接。
