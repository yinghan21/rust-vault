---
title: "std::format!"
type: std-条目
kind: 宏
module: std
slug: macro.format
stable: "1.0.0"
tags:
  - std/宏
aliases:
  - "format!"
  - "format 宏"
一句话: "用格式串把运行时表达式插值成一个新的 String 并返回，展开成 fmt::format(format_args!(..))。"
---

# `format!`

> [!abstract] 一句话
> `format!` 按格式串把若干表达式拼成一个**新的 `String`** 返回，不打印也不写文件。它展开成 `std::fmt::format(std::format_args!(..))`：先打包参数，再分配一个 `String` 把内容写进去。

## 简介

`format!` 解决的是「字符串拼接」这个高频需求。写 `format!("{name} 今年 {age} 岁")` 比一长串 `+`、`push_str`、`to_string` 清楚得多，而且编译器会检查占位符和参数是否对得上——类型、个数、有没有实现对应特质，都在编译期验完。

它和 `println!`、`write!` 共用同一套格式化语法，内部都走 `format_args!`，区别只在输出去处：`format!` 返回 `String`，`println!` 写标准输出，`write!` 写进任意实现了 `Write` 的缓冲区。所以凡是讲 `{}`、`{:?}`、`{name}` 的规则，三个宏完全一致。

展开结果与返回值：`format!($($arg)*)` 展开为 `std::fmt::format(std::format_args!($($arg)*))`，返回值类型是 `String`。注意它一定**分配堆内存**——这是它与 `format_args!`（只借用、零分配、只能用在一处）的本质差别。同理，在循环里反复 `format!` 再丢弃结果很浪费，能直接 `write!` 就 `write!`。

参数不要求 `Copy`/`Clone`：`format_args!` 只借用参数，所以 `format!("{}", big_string)` 之后 `big_string` 依然归你所有。

## 签名与参数

```text
format!($($arg:tt)*) -> String
```

| 参数 | 说明 |
| --- | --- |
| `$arg...` | 第一个必须是字面量格式串，后面跟零个或多个用来填空的参数。 |
| 返回 `String` | 新建的、拥有所有权的 UTF-8 字符串；不会修改任何已有值。 |

| 格式写法 | 说明 |
| --- | --- |
| `{}` | 按位置顺序取参数，要求实现 `Display`。 |
| `{name}` | 用具名参数 `name = expr` 填充，可重复出现。 |
| `{:?}` | 走 `Debug`，适合快速拼调试信息。 |
| `{:>8}` / `{:08}` | 宽度与填充，常用来拼对齐的表格。 |

## 示例

### 基本插值

```rust
fn main() {
    let s = format!("test");
    assert_eq!(s, "test");

    let s = format!("hello {}", "world!");
    assert_eq!(s, "hello world!");

    // 位置参数与具名参数可以混用
    let s = format!("x = {}, y = {val}", 10, val = 30);
    assert_eq!(s, "x = 10, y = 30");

    // 便捷捕获：作用域里同名变量直接写进 {} 里
    let (x, y) = (1, 2);
    let s = format!("{x} + {y} = 3");
    assert_eq!(s, "1 + 2 = 3");

    println!("{s}");
}
```

### 拼接不会拿走参数的所有权

```rust
fn main() {
    let name = String::from("小明");
    let age = 18;

    // format! 只借用 name，之后 name 仍然可用
    let line = format!("{name} 今年 {age} 岁");
    assert_eq!(line, "小明 今年 18 岁");
    assert_eq!(name.len(), 6);

    // 拼多行文本：用 format! 一次成型，比多次 push_str 更好读
    let table = format!("{:<6}|{:>4}\n{:<6}|{:>4}\n", "name", "age", "小明", 18);
    assert_eq!(table.lines().count(), 2);

    // 循环里只需要追加时，直接 push_str 到同一个 String，少一次分配
    let mut out = String::new();
    for i in 0..3 {
        out.push_str(&format!("{i},"));
    }
    assert_eq!(out, "0,1,2,");

    println!("{line}\n{table}");
}
```

## 常见陷阱

1. **格式串不是字面量**：`format!(tpl, x)` 编译失败，宏只能在编译期看到字面量；运行时拼接请用 `str::replace` 或 `String::push_str`。
2. **在热循环里反复 `format!`**：每次都要分配一个 `String`，能直接 `write!` 到同一个缓冲区就别中途建字符串。
3. **以为 `format!` 会打印**：它只在内存里生成 `String`，要输出得自己 `print!` / `println!`。
4. **`{}` 用在 `Option` 上**：`Option<T>`/`Result<T, E>` 没实现 `Display`，要写 `{:?}`，或者先 `unwrap` / `unwrap_or` 再格式化。
5. **转义花括号**：想输出字面量 `{` 或 `}` 要写 `{{` 和 `}}`，直接写 `{}` 会被当成占位符。

## 相关

- [[macro.println|println!]]：同样语法，但直接写到标准输出。
- [[macro.write|write!]]：写进 `String`、`Vec<u8>`、文件等任意 writer。
- [[fmt|std::fmt]]：格式串语法与 `Display`/`Debug` 的权威说明。
- [[string.String|String]]：返回值的类型，`push_str`、`truncate` 等方法都在这里。
- [[13-字符串|字符串]]：`String`、`&str`、格式化与拼接的完整讲法。
