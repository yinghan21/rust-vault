---
title: "std::println!"
type: std-条目
kind: 宏
module: std
slug: macro.println
stable: "1.0.0"
tags:
  - std/宏
aliases:
  - "println!"
  - "println 宏"
一句话: "把格式化后的文本写到标准输出并补一个换行，展开成「format_args! + 写 stdout」的语句，返回 ()。"
---

# `println!`

> [!abstract] 一句话
> `println!` 把格式化后的文本写到标准输出，并在末尾自动补一个换行。它展开成一句「先用 `format_args!` 打包参数，再交给 `std::io` 写到 stdout」的语句，整条语句的值是 `()`。

## 简介

`println!` 是最常用的输出宏：调试打印、命令行程序的用户界面、示例代码里的结果展示，都靠它。它和 `print!` 共用同一套格式化语法，区别只在结尾那个换行符——所有平台上都是单个 LINE FEED（`\n`，U+000A），不会额外写 `\r`，所以 Windows 上也不会出现 `\r\n`。

格式化能力和 [[fmt|std::fmt]] 完全一致：`{}` 按顺序吃掉后面的参数，`{name}` 用具名参数，`{0}` 按下标取参，`{:?}` / `{:#?}` 走 `Debug`，`{:>8}` 右对齐，`{:.2}` 保留两位小数。格式字符串必须是字面量，因为编译器要在编译期检查参数个数与类型。

展开结果值得记一下。`println!("x = {}", x)` 大致展开为 `::std::io::_print(::std::format_args_nl!("x = {}", x));`：`format_args!` 生成一个只借用参数的 `Arguments` 值（不分配堆内存、不移动参数），`_print` 把它写进 stdout。返回值就是 `()`。也正因为是借用，`println!("{}", s)` 之后 `s` 还能继续用。

代价在锁上：每次调用 `println!` 都会锁一次 stdout 的全局互斥量。热循环里逐行打印会被这把锁拖慢，正确写法是先 `io::stdout().lock()` 拿到 `StdoutLock`，再用 `writeln!` 循环写。

## 签名与参数

```text
println!() -> ()
println!($($arg:tt)*) -> ()
```

| 参数 | 说明 |
| --- | --- |
| `$arg...` | 零个或多个格式化参数；第一个通常是含 `{}` 的字面量格式串。 |
| 返回 `()` | 宏语句的值是 `()`；写入 stdout 失败时内部 panic，不返回 `Result`。 |

常用格式说明符：

| 写法 | 说明 |
| --- | --- |
| `{}` | 按顺序取下一个参数，要求实现 `Display`。 |
| `{:?}` / `{:#?}` | 紧凑 / 缩进美化版 `Debug` 输出。 |
| `{name}` / `{0}` | 具名参数 / 按索引取参，可重复引用同一个参数。 |
| `{:>8}` / `{:<8}` / `{:^8}` | 宽度 8，右 / 左 / 居中对齐，可加填充字符。 |
| `{:.2}` | 浮点保留两位小数；对字符串表示最多 2 个字符。 |

## 示例

### 基本用法与参数形式

```rust
fn main() {
    println!();                                  // 只输出一个换行
    println!("hello there!");

    // 位置参数、具名参数、捕获同名变量
    println!("format {} arguments", "some");
    let local_variable = "some";
    println!("format {local_variable} arguments");
    println!("{0} {1} {0}", "a", "b");           // 同一个参数可以用多次
    println!("x = {}, y = {y}", 10, y = 30);

    // 宽度与精度
    println!("[{:>5}] [{:<5}] [{:^5}]", 42, 42, 42);
    println!("pi ≈ {:.3}", 3.141_592_6);
    println!("{:?}", vec![1, 2, 3]);
}
```

### 热循环里先锁住 stdout

```rust
use std::io::{stdout, Write};

fn main() {
    // 每次 println! 都会锁一次 stdout；先锁一次再循环写就只锁一回
    let mut lock = stdout().lock();
    for i in 1..=3 {
        writeln!(lock, "第 {i} 行").unwrap();
    }
}
```

## 常见陷阱

1. **把变量当格式串直接传**：`println!(x)` 报 `format argument must be a string literal`，格式串必须是字面量，改成 `println!("{x}")` 或 `println!("{}", x)`。
2. **打印自定义类型报错**：`{:?}` 要求类型实现 `Debug`（通常加 `#[derive(Debug)]`），`{}` 要求实现 `Display`，两者都没有就编译失败。
3. **热循环里逐行 `println!`**：每次都要抢 stdout 锁，`--release` 下也快不起来，改用 `io::stdout().lock()` 配 `writeln!`。
4. **以为 `println!` 会移动参数**：`format_args!` 只借用参数，数值和 `String` 打印完仍然可用，不必 `clone`。
5. **靠 `{:>8}` 对齐中文**：宽度按字符数算，不看显示宽度，一个汉字占两个终端列，列对齐会错位，需要缩进就自己拼空格。
6. **stdout 写失败直接 panic**：管道下游提前关闭（例如 `| head`）时会 panic 在 `_print`，做健壮 CLI 就把结果写成 `writeln!` 并处理 `Err`。

## 相关

- [[fmt|std::fmt]]：格式串语法、`Display` 与 `Debug` 的完整说明。
- [[macro.format|format]]：需要把结果留成 `String` 而不是立刻打印时用它。
- [[macro.write|write!]]：把同样格式化的内容写进 `String`、`Vec<u8>` 或文件。
- [[macro.dbg|dbg!]]：临时调试时打到 stderr，还会带上文件名与行号。
- [[13-字符串|字符串]]：`String`、`&str` 与格式化的关系。
