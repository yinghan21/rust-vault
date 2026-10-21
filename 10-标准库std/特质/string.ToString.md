---
title: "std::string::ToString"
type: std-条目
kind: 特质
module: string
slug: string.ToString
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - ToString
一句话: 把值转换为 String 的便利特质，任何实现了 Display 的类型都会自动获得。
---

# `ToString`

> [!abstract] 一句话
> `ToString` 提供 `.to_string()`：它对任何实现了 `Display` 的类型自动生效，所以你只需要写 `Display`，永远不要手写 `ToString`。

## 简介

`ToString` 只有 `to_string` 一个方法，标准库里有一条覆盖它的空白实现：

```text
impl<T: fmt::Display + ?Sized> ToString for T
```

这条实现意味着「只要实现了 `Display`，`.to_string()` 就免费可用」。因此对这个 trait 的正确用法是**不实现它**：把功夫花在 `Display` 上，`ToString` 自己会跟上。

内部它等价于 `format!("{}", self)`，也就是一次分配加一次格式化。需要拼装多个片段时，用 `write!` 往同一个 `String` 里追加，比反复 `to_string()` 再相加省下大量分配。

`ToString` 本身在 trait 声明里没有超特质约束，但唯一有用的实现依赖 `Display`，所以实践上可以认为二者捆绑：实现 `Display` ⇒ 拥有 `ToString`，手写 `ToString` ⇒ 与空白实现冲突。

## 必须实现

无需实现。`to_string` 由标准库的空白实现统一提供：

| 方法 | 说明 |
| --- | --- |
| `to_string(&self)` | 把值转换为 `String`，内部走一次 `format!`。 |

手写 `impl ToString for MyType` 会与那条空白实现冲突（conflicting implementations），编译直接失败。想自定义输出，改 `Display::fmt`。

## 与相邻 trait 的关系

| trait | 关系 |
| --- | --- |
| `Display` | 唯一有意义的来源：`T: Display` 自动带来 `ToString`。 |
| `From<&str>` / `From<String>` | 拥有所有权的转换，不需要格式化。 |
| `Into<String>` | 转换语法的通用入口，与 `to_string()` 覆盖范围不同。 |
| `format!` | 同一套格式化引擎，只是直接产出 `String` 而不经过方法调用。 |

## 示例

### 实现 `Display`，白得 `ToString`

```rust
use std::fmt;

struct Point {
    x: i32,
    y: i32,
}

impl fmt::Display for Point {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({}, {})", self.x, self.y)
    }
}

// 这里什么都不用写，Point 已经自动实现了 ToString
fn main() {
    let p = Point { x: 1, y: 2 };

    let s: String = p.to_string();
    assert_eq!(s, "(1, 2)");

    // to_string 与 format! 等价，选一个用就好
    assert_eq!(p.to_string(), format!("{p}"));

    // 需要再次使用时仍可借用，p 没有被消耗
    assert_eq!(p.x, 1);
}
```

### 拼接时复用缓冲区

```rust
use std::fmt::Write;

fn main() {
    // 循环里反复 to_string() 会不断分配；write! 追加到同一个 String 更省
    let mut line = String::new();
    for i in 1..=3 {
        write!(line, "{i},").unwrap();
    }
    assert_eq!(line, "1,2,3,");

    // 只有一个值时，to_string 已经足够清晰
    let n = 42;
    assert_eq!(n.to_string(), "42");
}
```

## 常见陷阱

1. **手写 `impl ToString`**：与 `impl<T: Display> ToString for T` 冲突，报 conflicting implementations；正确做法是实现 `Display`。
2. **以为 `ToString` 能替代 `Display` 做约束**：`fn f<T: ToString>(t: T)` 会让调用方必须满足格式化能力，而在函数内部还要再拿到 `String` 分配一次；需要展示时直接要求 `T: Display` 更省。
3. **热路径里滥用 `to_string()`**：每次调用都分配一个 `String`，循环拼接请用 `write!` 或 `String::push_str`。
4. **`to_string()` 与 `to_owned()` 混用**：`to_owned()` 走的是 `ToOwned`，用于 `&str` → `String`、`&[T]` → `Vec<T>` 这类复制，语义不同。
5. **`to_string()` 吞掉错误**：格式化本身理论上可能失败（`fmt::Error`），`to_string` 内部直接 panic 处理，写 `Display` 时别在 `fmt` 里做会失败的 I/O。
6. **给同一类型同时实现两个转换入口**：既写 `Display` 又想自定义 `to_string`，会导致语义分叉，选一条路走。

## 相关

- [[string|std::string 模块]]：`String`、`ToString` 与字符串相关条目。
- [[fmt.Display|Display]]：`ToString` 的真正实现来源。
- [[string.String|String]]：可增长的 UTF-8 字符串类型。
- [[fmt.Debug|Debug]]：调试向的文本化，与 `Display` 并列。
- [[macro.format|format]]：直接产出 `String` 的格式化宏。
- [[13-字符串|字符串]]：`String` 与 `&str` 的完整笔记。
