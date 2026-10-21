---
title: "std::string::String"
type: std-条目
kind: 结构体
module: string
slug: string.String
stable: "1.0.0"
tags:
  - std/类型
aliases:
  - String
一句话: "拥有所有权、可增长、保证 UTF-8 的堆分配字符串，是 &str 的可修改版本。"
---

# String

> [!abstract] 一句话
> `String` 是**拥有所有权、可增长、保证 UTF-8** 的堆分配字符串，可以理解为 `Vec<u8>` 的字符串特化，也是 [[primitive.str|str]] 的可修改版本。

## 简介

`String` 与 `str` 的关系，就像 [[vec.Vec|Vec]] 与 `[T]` 的关系：`str` 是一段定长的 UTF-8 字节序列（只能以 `&str` 之类的引用形式出现），`String` 则把这段字节放在堆上，并额外记录容量，所以能修改、追加和扩容。

- **布局**：三个字（指针、长度、容量），与 `Vec<u8>` 完全一致，所以 `into_bytes()` 只是交出缓冲区，`as_str()` 只是借用，两者都是零成本。
- **UTF-8 不变量**：任何 `String` 的内容都是合法 UTF-8，这是类型层面的保证。因此**所有索引、切片位置、`len()` 都以字节为单位**，一个中文字符占 3 字节，`chars().count()` 才是人类眼中的「字数」。
- **`Deref<Target = str>`**：`split`、`trim`、`contains`、`chars` 等 `str` 方法可以直接在 `String` 上调用，不需要先 `.as_str()`。
- **怎么选**：函数参数写 `&str`（`&String` 会自动解引用，两种实参都能传），需要持有或修改内容时用 `String`；`format!`、`to_string()`、`read_to_string` 返回的都是 `String`。

`String` 内部没有结尾的 `\0`，内容里也可以出现 `\0`，这一点与 C 字符串不同；需要传给 C 代码时用 [[ffi.CString|CString]]。

## 常用方法

> [!note] 表中的 `str` 方法
> `String` 实现了 `Deref<Target = str>`，`get`、`split`、`trim`、`contains`、`chars` 等方法实际上是 `str` 的，通过解引用转发到 `String` 上；`len`、`is_empty`、`as_bytes` 在两侧同名同义，下表合并为一行。

> [!tip] 新老工具链差异
> `from_utf16le*`（1.98）、`from_utf8_lossy_owned`（1.99）、`strip_circumfix`（1.98）、`substr_range`（1.98）是较新的稳定 API；此外 `new`、`as_str`、`capacity`、`len`、`is_empty`、`into_bytes` 等是 `const fn`，可用于常量上下文。

### 创建、转换与拆解

| 方法 | 说明 |
| --- | --- |
| `new()` | 创建一个空 `String`，不分配堆内存。 |
| `with_capacity(capacity)` | 创建空串，并预留至少指定字节容量。 |
| `from_utf8(vec)` | 校验字节向量是合法 UTF-8，失败返回 `Err`。 |
| `from_utf8_lossy(v)` | 把字节切片转为字符串，非法序列换成 `U+FFFD`。 |
| `from_utf8_lossy_owned(v)` | 消耗字节向量转字符串，非法序列换成 `U+FFFD`。 |
| `from_utf16(v)` | 按原生端序解码 UTF-16，非法数据返回 `Err`。 |
| `from_utf16_lossy(v)` | 按原生端序解码 UTF-16，非法单元换成 `U+FFFD`。 |
| `from_utf16le(v)` | 按小端解码 UTF-16，非法数据返回 `Err`。 |
| `from_utf16le_lossy(v)` | 按小端解码 UTF-16，非法单元换成 `U+FFFD`。 |
| `from_utf16be(v)` | 按大端解码 UTF-16，非法数据返回 `Err`。 |
| `from_utf16be_lossy(v)` | 按大端解码 UTF-16，非法单元换成 `U+FFFD`。 |
| `from_raw_parts(buf, length, capacity)` | 由指针、长度、容量重组 `String`（unsafe）。 |
| `from_utf8_unchecked(bytes)` | 跳过 UTF-8 校验直接构造（unsafe）。 |
| `into_raw_parts()` | 拆解为（指针，长度，容量）并交出所有权。 |
| `into_bytes()` | 消耗自身，把缓冲区转成字节向量。 |
| `as_str()` | 借用整体内容为 `&str`，零成本。 |
| `as_mut_str()` | 借用整体内容为 `&mut str`。 |
| `as_mut_vec()` | 以 `&mut Vec<u8>` 暴露内部缓冲区（unsafe）。 |
| `into_boxed_str()` | 消耗自身，转换为 `Box<str>`，可能顺手缩容。 |
| `leak()` | 泄漏缓冲区，返回 `&'a mut str`。 |
| `as_bytes()` | 借用内容为字节切片。 |
| `as_bytes_mut()` | 以 `&mut [u8]` 暴露内容（unsafe）。 |
| `as_ptr()` | 返回指向内容的只读裸指针。 |
| `as_mut_ptr()` | 返回指向内容的可变裸指针。 |

### 原地修改

| 方法 | 说明 |
| --- | --- |
| `push(ch)` | 追加一个 `char` 到末尾。 |
| `push_str(string)` | 追加一个字符串切片到末尾。 |
| `insert(idx, ch)` | 在字节位置 `idx` 插入一个字符。 |
| `insert_str(idx, string)` | 在字节位置 `idx` 插入一个字符串切片。 |
| `extend_from_within(src)` | 把自身的一段字节区间复制到末尾。 |
| `pop()` | 弹出并返回最后一个字符，空串返回 `None`。 |
| `remove(idx)` | 删除并返回字节位置 `idx` 处的字符。 |
| `truncate(new_len)` | 截断到指定字节长度，须落在字符边界。 |
| `clear()` | 清空内容，长度归零但保留容量。 |
| `retain(f)` | 仅保留谓词返回 `true` 的字符。 |
| `split_off(at)` | 在字节位置切开，返回后半段组成的新串。 |
| `drain(range)` | 批量删除区间，返回被删字符的迭代器。 |
| `replace_range(range, replace_with)` | 用给定字符串替换指定字节区间。 |
| `make_ascii_uppercase()` | 原地把 ASCII 字母转为大写。 |
| `make_ascii_lowercase()` | 原地把 ASCII 字母转为小写。 |

### 替换、大小写与转义

| 方法 | 说明 |
| --- | --- |
| `replace(from, to)` | 替换全部匹配，返回新的 `String`。 |
| `replacen(pat, to, count)` | 只替换前 `count` 次匹配，返回新串。 |
| `to_lowercase()` | 返回 Unicode 小写副本，长度可能变化。 |
| `to_uppercase()` | 返回 Unicode 大写副本，长度可能变化。 |
| `repeat(n)` | 返回原串重复 `n` 次后的新串。 |
| `to_ascii_uppercase()` | 返回 ASCII 大写副本，长度不变。 |
| `to_ascii_lowercase()` | 返回 ASCII 小写副本，长度不变。 |
| `escape_debug()` | 迭代近似 `Debug` 输出形式的转义字符。 |
| `escape_default()` | 迭代按默认转义规则处理的字符。 |
| `escape_unicode()` | 迭代 `\u{...}` 形式的转义字符。 |

### 长度、容量与索引边界

| 方法 | 说明 |
| --- | --- |
| `len()` | 返回内容的字节长度，不是字符数。 |
| `is_empty()` | 判断内容是否为空（长度是否为 0）。 |
| `capacity()` | 返回当前已分配的字节容量。 |
| `reserve(additional)` | 预留至少 `additional` 字节，可能多留。 |
| `reserve_exact(additional)` | 预留恰好够用的容量，不多留。 |
| `try_reserve(additional)` | 可失败地预留容量，内存不足返回 `Err`。 |
| `try_reserve_exact(additional)` | 可失败地精确预留，失败时内容不变。 |
| `shrink_to_fit()` | 把容量收缩到与长度一致。 |
| `shrink_to(min_capacity)` | 收缩容量，但不低于给定下界。 |
| `is_char_boundary(index)` | 判断该字节位置是否是字符边界。 |
| `floor_char_boundary(index)` | 向前找最近的字符边界，不超过 `index`。 |
| `ceil_char_boundary(index)` | 向后找最近的字符边界，不低于 `index`。 |
| `substr_range(substr)` | 返回子串在原串中的字节范围。 |

### 查询与迭代

| 方法 | 说明 |
| --- | --- |
| `chars()` | 按 `char` 迭代，正确处理多字节字符。 |
| `char_indices()` | 迭代每个字符及其起始字节位置。 |
| `bytes()` | 按 `u8` 迭代原始字节。 |
| `split_whitespace()` | 按任意空白切分，连续空白视为一个。 |
| `split_ascii_whitespace()` | 只按 ASCII 空白切分。 |
| `lines()` | 按行迭代，去掉 `\n` 与行尾的 `\r`。 |
| `encode_utf16()` | 迭代 UTF-16 编码的 `u16` 序列。 |
| `contains(pat)` | 判断是否包含给定模式。 |
| `starts_with(pat)` | 判断是否以给定模式开头。 |
| `ends_with(pat)` | 判断是否以给定模式结尾。 |
| `find(pat)` | 返回首个匹配的起始字节位置。 |
| `rfind(pat)` | 返回最后一个匹配的起始字节位置。 |
| `matches(pat)` | 迭代所有不重叠的匹配。 |
| `rmatches(pat)` | 逆序迭代所有不重叠的匹配。 |
| `match_indices(pat)` | 迭代匹配及其起始字节位置。 |
| `rmatch_indices(pat)` | 逆序迭代匹配及其位置。 |
| `parse()` | 解析为实现 `FromStr` 的目标类型。 |
| `is_ascii()` | 判断是否全部是 ASCII 字符。 |
| `eq_ignore_ascii_case(other)` | 判断是否 ASCII 大小写不敏感地相等。 |

### 切片与分割

| 方法 | 说明 |
| --- | --- |
| `get(i)` | 按区间取子切片，越界或非边界返回 `None`。 |
| `get_mut(i)` | 按区间取可变子切片，同上失败返回 `None`。 |
| `get_unchecked(i)` | 不做边界检查地取子切片（unsafe）。 |
| `get_unchecked_mut(i)` | 不做边界检查地取可变子切片（unsafe）。 |
| `split_at(mid)` | 在字节位置切成两段，位置非法则 panic。 |
| `split_at_mut(mid)` | 在字节位置切成两个可变子切片。 |
| `split_at_checked(mid)` | 切成两段，位置非法返回 `None`。 |
| `split_at_mut_checked(mid)` | 可变版本，位置非法返回 `None`。 |
| `split(pat)` | 按模式切分，返回子串迭代器。 |
| `split_inclusive(pat)` | 切分并把分隔符留在子串末尾。 |
| `rsplit(pat)` | 从右往左按模式切分。 |
| `split_terminator(pat)` | 切分，但去掉末尾的空子串。 |
| `rsplit_terminator(pat)` | 从右往左切分，去掉末尾空子串。 |
| `splitn(n, pat)` | 最多切成 `n` 段，剩余部分合并。 |
| `rsplitn(n, pat)` | 从右往左，最多切成 `n` 段。 |
| `split_once(delimiter)` | 在首个分隔符处切成前后两部分。 |
| `rsplit_once(delimiter)` | 在最后一个分隔符处切成两部分。 |

### 修剪与剥离

| 方法 | 说明 |
| --- | --- |
| `trim()` | 去掉首尾的 Unicode 空白。 |
| `trim_start()` | 只去掉开头的 Unicode 空白。 |
| `trim_end()` | 只去掉结尾的 Unicode 空白。 |
| `trim_matches(pat)` | 反复去掉首尾匹配模式的片段。 |
| `trim_start_matches(pat)` | 反复去掉开头匹配模式的片段。 |
| `trim_end_matches(pat)` | 反复去掉结尾匹配模式的片段。 |
| `strip_prefix(prefix)` | 去掉指定前缀，不匹配返回 `None`。 |
| `strip_suffix(suffix)` | 去掉指定后缀，不匹配返回 `None`。 |
| `strip_circumfix(prefix, suffix)` | 同时去掉前后缀，任一不匹配返回 `None`。 |
| `trim_ascii()` | 去掉首尾的 ASCII 空白。 |
| `trim_ascii_start()` | 只去掉开头的 ASCII 空白。 |
| `trim_ascii_end()` | 只去掉结尾的 ASCII 空白。 |

## 示例

### 示例 1：构建、借用与容量

```rust
fn main() {
    // 从 &str 创建，再逐块追加内容
    let mut s = String::from("Hello");
    s.push_str(", ");
    s.push('世');
    s.push('界');
    assert_eq!(s, "Hello, 世界");

    // len() 返回字节数（世、界各占 3 字节），chars().count() 才是字符数
    assert_eq!(s.len(), 13);
    assert_eq!(s.chars().count(), 9);

    // 借用为 &str 不复制，into_bytes 才会把缓冲区交出来
    let borrowed: &str = s.as_str();
    assert_eq!(borrowed.chars().next(), Some('H'));

    // 字节与字符串互转：非法 UTF-8 返回 Err，lossy 版本替换为 U+FFFD
    let bytes: Vec<u8> = s.clone().into_bytes();
    assert_eq!(String::from_utf8(bytes).unwrap(), s);
    assert!(String::from_utf8(vec![0xff, 0xfe]).is_err());
    assert_eq!(String::from_utf8_lossy(&[0x66, 0x6f, 0xff]), "fo\u{fffd}");

    // 预分配容量避免反复扩容，之后再用 shrink_to_fit 收回多余空间
    let mut buf = String::with_capacity(16);
    buf.push_str("abc");
    assert!(buf.capacity() >= 16);
    buf.shrink_to_fit();
    assert!(buf.capacity() >= buf.len());
}
```

### 示例 2：解析、切分与替换

```rust
fn main() {
    // lines() 按行切分，trim() 去掉首尾空白，parse() 转成数字
    let raw = "  42 \n 7 \n 100 ";
    let mut total = 0u32;
    for line in raw.lines() {
        let text = line.trim();
        if text.is_empty() {
            continue;
        }
        total += text.parse::<u32>().expect("不是合法数字");
    }
    assert_eq!(total, 149);

    // split 按分隔符切分，split_once 只在第一个分隔符处切开
    let csv = "name,age,city";
    let fields: Vec<&str> = csv.split(',').collect();
    assert_eq!(fields.len(), 3);
    assert_eq!(fields[2], "city");

    let record = "key=value=extra";
    let (key, value) = record.split_once('=').unwrap();
    assert_eq!((key, value), ("key", "value=extra"));

    // 查找与替换：replace 返回新 String，原串不变
    let slogan = "Rust is fast";
    assert!(slogan.contains("fast"));
    assert_eq!(slogan.find("fast"), Some(8));
    assert_eq!(slogan.replace("fast", "safe"), "Rust is safe");
    assert_eq!(slogan, "Rust is fast");

    // 大小写：to_uppercase 会新分配，eq_ignore_ascii_case 只做比较
    assert_eq!(slogan.to_uppercase(), "RUST IS FAST");
    assert!(slogan.eq_ignore_ascii_case("rust IS FAST"));
}
```

## 常见陷阱

1. **`len()` 是字节数，不是字数**：`"你好".len()` 是 6，`chars().count()` 才是 2；用 `len()` 判断「几个字」或截取固定字数一定会错。
2. **切片位置必须落在字符边界**：`"你好"[0..1]` 会 panic（`byte index 1 is not a char boundary`）。用 `get(0..1)` 拿到 `None`、用 `floor_char_boundary` 找安全位置，或者干脆改用 `chars()`。
3. **`+` 会消耗左值**：`let c = a + &b;` 之后 `a` 已经被移动；多次拼接请用 `format!` 或 `push_str`。
4. **`from_utf8_unchecked`、`as_mut_vec` 破坏不变量是未定义行为**：外部输入一律走 `from_utf8` / `from_utf8_lossy`；用 `as_mut_vec` 改完必须保证内容仍是合法 UTF-8，否则后续所有字符串操作都在 UB 上运行。
5. **循环里追加要预分配**：`push_str` 在容量不足时会扩容并整体复制，已知大小时先 `with_capacity` 或 `reserve`；数据只读时直接借用 `&str`，不要 `clone()`。

## 相关

- [[string|std::string]]：`String` 所属模块，还有 `FromUtf8Error`、`Drain` 等配套类型。
- [[primitive.str|str]]：借用的定长字符串视图，也是上表中大量方法的真正来源。
- [[vec.Vec|Vec]]：`String` 的底层缓冲区类型，`into_bytes` 就是换成它。
- [[string.ToString|ToString]]：把实现了 `Display` 的类型变成 `String` 的 `to_string()`。
- [[str.FromStr|FromStr]]：`parse()` 依赖的目标特型，解析失败时返回它的 `Err`。
- [[13-字符串|字符串]]：`String` 与 `&str` 的所有权、切片与常见用法。
