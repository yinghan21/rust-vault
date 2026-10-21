---
title: "std::primitive::str"
type: std-条目
kind: 原始类型
module: primitive
slug: primitive.str
stable: "1.0.0"
tags:
  - std/类型
  - rust/基础
aliases:
  - Type str
一句话: UTF-8 字符串切片，是唯一的内建字符串类型，只能以 &str 或 Box<str> 的形式使用。
---

# `str`

> [!abstract] 一句话
> `str` 是 Rust 的**字符串切片**类型，内容一定是合法 UTF-8；它是未定长类型（DST），实际使用时总是出现在引用后面，写作 `&str`。

## 简介

`str` 是语言内置的字符串类型，但它是**未定长**的：编译器不知道一个 `str` 有多长，所以不能直接当变量类型用。你实际接触到的形式是：

- `&str`：借用的字符串切片，指向某段 UTF-8 字节，通常长度固定、不拥有数据；
- `Box<str>`：堆上拥有的字符串，长度不可变，但可以零拷贝转成 `String` 或 `Box<[u8]>`；
- `&'static str`：字符串字面量 `"hello"` 的类型，直接编译进二进制。

它和 [[string.String|String]] 的关系是「视图」与「所有者」：`String` 是可增长、可修改的堆缓冲区，`&str` 是对其中一段的只读借阅。函数参数尽量写 `&str`，这样 `String`、`&String`、字面量都能传进来。

几个必须记住的事实：

- **没有位宽，只有字节**：`str` 的长度是字节数，中文一个字 3 字节、emoji 通常 4 字节，`len()` 不等于字符数。
- **字面量写法**：`"abc"`、`r"a\b"`（原始字符串）、多行字面量都产生 `&'static str`；`"abc".to_string()` 或用 `String::from` 才得到 `String`。
- **不能按整数下标取字符**：`s[0]` 不成立，切片只能用字节范围 `&s[0..3]`，且边界必须落在字符边界上，否则 panic。
- 所有方法都定义在这个原始类型上，`std::str` 模块里另有 `FromStr`、`Utf8Error`、`Chars` 等配套条目。

## 常用方法

共 76 个稳定方法，按用途分成 9 组。

### 长度与字符边界

| 方法 | 说明 |
| --- | --- |
| `len()` | 返回字节长度（不是字符个数）。 |
| `is_empty()` | 判断字节长度是否为 0。 |
| `is_char_boundary()` | 判断该字节位置是否为字符边界。 |
| `floor_char_boundary()` | 向下取整到最近的字符边界。 |
| `ceil_char_boundary()` | 向上取整到最近的字符边界。 |

### UTF-8 构造与所有权转换

| 方法 | 说明 |
| --- | --- |
| `from_utf8()` | 校验 UTF-8 后把字节切片转为 `&str`。 |
| `from_utf8_mut()` | 校验 UTF-8 后把可变字节切片转为 `&mut str`。 |
| `from_utf8_unchecked()` | 跳过校验直接转 `&str`，调用者保证合法。 |
| `from_utf8_unchecked_mut()` | 跳过校验直接转 `&mut str`，调用者保证合法。 |
| `into_boxed_bytes()` | 把 `Box<str>` 零拷贝转为 `Box<[u8]>`。 |
| `into_string()` | 把 `Box<str>` 零拷贝转为 `String`。 |

### 底层字节访问与切片

| 方法 | 说明 |
| --- | --- |
| `as_bytes()` | 借用为字节切片，不复制。 |
| `as_bytes_mut()` | 借用为可变字节切片，改坏即 UB。 |
| `as_ptr()` | 返回指向首字节的裸指针。 |
| `as_mut_ptr()` | 返回指向首字节的可变裸指针。 |
| `get()` | 按索引或范围取子串，越界返回 `None`。 |
| `get_mut()` | 取可变子串，越界或非边界返回 `None`。 |
| `get_unchecked()` | 不做任何检查地取子串（unsafe）。 |
| `get_unchecked_mut()` | 不做任何检查地取可变子串（unsafe）。 |
| `split_at()` | 按字节位置切成前后两段。 |
| `split_at_mut()` | 按字节位置切成两个可变切片。 |
| `split_at_checked()` | 同 `split_at`，非法位置返回 `None`。 |
| `split_at_mut_checked()` | 同 `split_at_mut`，非法位置返回 `None`。 |
| `substr_range()` | 返回子串在原串中的字节范围。 |

> [!warning] 切片的索引是字节
> `&s[0..3]` 里的 `3` 是字节偏移。切在多字节字符中间会 panic，宁可用 `get()` 拿 `Option`。

### 遍历

| 方法 | 说明 |
| --- | --- |
| `chars()` | 按 `char` 迭代字符串。 |
| `char_indices()` | 迭代每个 `char` 及其字节位置。 |
| `bytes()` | 按 `u8` 字节迭代字符串。 |
| `split_whitespace()` | 按空白切分，并合并连续空白。 |
| `split_ascii_whitespace()` | 只按 ASCII 空白切分。 |
| `lines()` | 按行切分，去掉行尾换行符。 |
| `encode_utf16()` | 迭代字符串的 UTF-16 码元。 |

### 切分

| 方法 | 说明 |
| --- | --- |
| `split()` | 按模式切分，保留空子串。 |
| `split_inclusive()` | 切分并把分隔符留在子串末尾。 |
| `rsplit()` | 从右向左切分。 |
| `split_terminator()` | 切分，忽略末尾空子串。 |
| `rsplit_terminator()` | 从右向左切分，忽略末尾空子串。 |
| `splitn()` | 最多切出 `n` 段。 |
| `rsplitn()` | 从右向左最多切出 `n` 段。 |
| `split_once()` | 在首个分隔符处切成两段。 |
| `rsplit_once()` | 在最后一个分隔符处切成两段。 |

### 查找与匹配

| 方法 | 说明 |
| --- | --- |
| `contains()` | 判断是否包含某模式。 |
| `starts_with()` | 判断是否以某模式开头。 |
| `ends_with()` | 判断是否以某模式结尾。 |
| `find()` | 返回首个匹配的起始字节位置。 |
| `rfind()` | 返回最后一个匹配的起始字节位置。 |
| `matches()` | 迭代所有不重叠的匹配子串。 |
| `rmatches()` | 从右往左迭代匹配子串。 |
| `match_indices()` | 迭代匹配子串及其起始位置。 |
| `rmatch_indices()` | 从右往左迭代匹配子串与位置。 |

### 裁剪与剥离

| 方法 | 说明 |
| --- | --- |
| `trim()` | 去掉首尾 Unicode 空白。 |
| `trim_start()` | 去掉开头的空白。 |
| `trim_end()` | 去掉结尾的空白。 |
| `trim_matches()` | 反复去掉首尾匹配到的模式。 |
| `trim_start_matches()` | 反复去掉开头匹配到的模式。 |
| `trim_end_matches()` | 反复去掉结尾匹配到的模式。 |
| `strip_prefix()` | 去掉给定前缀，无前缀返回 `None`。 |
| `strip_suffix()` | 去掉给定后缀，无后缀返回 `None`。 |
| `strip_circumfix()` | 同时去掉前后缀，缺一返回 `None`。 |

### ASCII 与转义

| 方法 | 说明 |
| --- | --- |
| `is_ascii()` | 判断是否全为 ASCII 字符。 |
| `eq_ignore_ascii_case()` | 忽略 ASCII 大小写比较是否相等。 |
| `make_ascii_uppercase()` | 原地把 ASCII 字母转为大写。 |
| `make_ascii_lowercase()` | 原地把 ASCII 字母转为小写。 |
| `trim_ascii_start()` | 去掉开头的 ASCII 空白。 |
| `trim_ascii_end()` | 去掉结尾的 ASCII 空白。 |
| `trim_ascii()` | 去掉首尾的 ASCII 空白。 |
| `to_ascii_uppercase()` | 返回 ASCII 大写的新 `String`。 |
| `to_ascii_lowercase()` | 返回 ASCII 小写的新 `String`。 |
| `escape_debug()` | 按 `escape_debug` 规则迭代转义结果。 |
| `escape_default()` | 按 `escape_default` 规则迭代转义结果。 |
| `escape_unicode()` | 按 `escape_unicode` 规则迭代转义结果。 |

### 解析与生成新字符串

| 方法 | 说明 |
| --- | --- |
| `parse()` | 把字符串解析为指定类型。 |
| `replace()` | 替换全部匹配，返回新 `String`。 |
| `replacen()` | 只替换前 `n` 个匹配。 |
| `to_lowercase()` | 返回 Unicode 小写的新 `String`。 |
| `to_uppercase()` | 返回 Unicode 大写的新 `String`。 |
| `repeat()` | 重复 `n` 次生成新 `String`。 |

## 示例

### 字节长度与字符边界

```rust
fn main() {
    let s = "Hello, 世界!";

    // 字节长度是 14，字符个数只有 10
    assert_eq!(s.len(), 14);
    assert_eq!(s.chars().count(), 10);

    // 7 是「世」的第一个字节，所以是合法的字符边界
    assert!(s.is_char_boundary(7));
    // 8 落在「世」的中间，不是字符边界
    assert!(!s.is_char_boundary(8));

    assert_eq!(s.get(0..5), Some("Hello"));
    assert_eq!(s.get(0..8), None);
    assert_eq!(s.chars().nth(7), Some('世'));
}
```

### 查找、切分与解析

```rust
fn main() {
    let line = "  key=value  ";

    // trim 去掉首尾空白，split_once 在首个 '=' 处切开
    let (k, v) = line.trim().split_once('=').unwrap();
    assert_eq!((k, v), ("key", "value"));

    // parse 依赖 FromStr，失败时返回 Err
    let n: i32 = "42".parse().unwrap();
    assert_eq!(n, 42);
    assert!("4x2".parse::<i32>().is_err());

    // split 保留空子串，split_terminator 会丢掉末尾的空串
    let parts: Vec<&str> = "a,b,,c".split(',').collect();
    assert_eq!(parts, vec!["a", "b", "", "c"]);
    let tail: Vec<&str> = "a,b,".split_terminator(',').collect();
    assert_eq!(tail, vec!["a", "b"]);

    // to_uppercase 生成新 String，原串不变
    let upper = "abc".to_uppercase();
    assert_eq!(upper, "ABC");
    assert_eq!("abc".len(), 3);
}
```

## 常见陷阱

1. **把 `len()` 当字符数**：它返回字节数，`"世界".len()` 是 6 而不是 2；要字符数用 `chars().count()`。
2. **按字节下标切片会 panic**：`&s[0..1]` 切在多字节字符中间会崩溃；先 `is_char_boundary` 检查，或直接用 `get()`。
3. **不能用整数下标**：`s[0]` 直接编译失败，取第一个字节写 `s.as_bytes()[0]`，取第一个字符写 `s.chars().next()`。
4. **`trim()` 与 `trim_ascii()` 语义不同**：前者按 Unicode 空白处理全角空格等，后者只认 ASCII 空白，字节流场景更快也更容易预测。
5. **大小写转换可能改变长度**：`to_lowercase()` 是 Unicode 语义，`ß` 转大写会变成 `SS`；只处理 ASCII 时用 `make_ascii_uppercase()` 原地改，避免额外分配。
6. **已弃用的旧名字**：`trim_left`、`trim_right`、`trim_left_matches`、`trim_right_matches`、`slice_unchecked`、`lines_any` 都已被 `trim_start`、`trim_end`、`trim_start_matches`、`trim_end_matches`、`get_unchecked`、`lines` 取代。

## 相关

- [[str|std::str 模块]]：`FromStr`、`Utf8Error`、`Chars` 等配套条目都在这里。
- [[primitive|std::primitive]]：`str` 所属的原始类型集合。
- [[string.String|String]]：拥有所有权、可增长的字符串缓冲区。
- [[13-字符串|字符串]]：字符串处理的整体学习笔记。
- [[primitive.slice|Type slice]]：`str` 在 API 形态上与字节切片高度相似。
