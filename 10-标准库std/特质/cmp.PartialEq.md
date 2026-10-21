---
title: "std::cmp::PartialEq"
type: std-条目
kind: 特质
module: cmp
slug: cmp.PartialEq
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - PartialEq
一句话: 定义 == 与 != 的语义，只要求部分等价，因此 NaN 也能参与比较。
---

# PartialEq

> [!abstract] 一句话
> `PartialEq` 规定两个值「相等」是什么意思：实现它，类型就获得 `==` 和 `!=`；它比 [[cmp.Eq|Eq]] 宽松，允许某些值连自己都不等于自己，`f64::NAN` 就是标准库给出的例子。

## 简介

`PartialEq` 是 `==` 与 `!=` 运算符背后的 trait。它的定义带一个默认的泛型参数：`pub trait PartialEq<Rhs: ?Sized = Self>`，所以既可以写 `impl PartialEq for Book`（与自身比较），也可以写 `impl PartialEq<BookFormat> for Book`（跨类型比较）。`Rhs` 允许 `?Sized`，这就是 `String == str`、`String == &str` 能直接写的原因。

「Partial」指的是**部分等价关系**：它要求对称（`a == b` 蕴含 `b == a`）和传递，但不要求自反。浮点数恰好卡在这一条上——`NaN == NaN` 为 `false`，所以 `f64` 实现了 `PartialEq` 却没有实现 `Eq`。补上自反性的工作由 [[cmp.Eq|Eq]] 承担。

只有 `eq` 是必须实现的，`ne` 有默认实现 `!self.eq(other)`。派生宏 `#[derive(PartialEq)]` 会逐字段生成 `eq`：所有字段都相等才算相等，并要求每个字段类型都是 `PartialEq`。

比较本身可以很便宜（比较一个 `i32`），也可以很贵（逐元素比较 `Vec`、逐字节比较 `String`）。标准库里大量 API 建立在它之上：`Vec::contains`、`slice::sort` 之外的查找、`HashMap` 的键比较、`assert_eq!` 宏。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `eq()` | 判断 `self` 与 `other` 是否相等，对应 `==`。 |

签名是 `fn eq(&self, other: &Rhs) -> bool`。它借用两个值而不是消耗它们，比较之后双方都还在。

## 提供的方法

| 方法 | 说明 |
| --- | --- |
| `ne()` | 判断两者是否不等，对应 `!=`，默认返回 `eq` 的反。 |

签名是 `fn ne(&self, other: &Rhs) -> bool`。几乎没有理由覆写它：只要 `eq` 正确，取反就正确。反过来，若覆写了 `ne` 却忘了让它与 `eq` 互斥，就会出现 `a == b` 与 `a != b` 同时为真的荒唐结果。

## 与相邻 trait 的关系

`PartialEq` 与 [[cmp.Eq|Eq]] 的区别只有一条：自反性。

| 维度 | `PartialEq` | `Eq` |
| --- | --- | --- |
| 关系强度 | 部分等价：对称、传递，但**不一定自反** | 完全等价：在 `PartialEq` 之上要求自反 |
| 方法 | 必须实现 `eq`，自带 `ne` | 空特质，没有任何方法 |
| `f64` | 实现 | **不实现**，因为 `NaN != NaN` |
| 编译器检查 | 不检查这些性质 | 同样不检查，只能靠实现者自觉 |
| 典型用途 | 任何「能比较相等」的类型 | `HashMap`、`BTreeMap` 的键，需要可靠去重的场景 |

另外两个方向：[[cmp.PartialOrd|PartialOrd]] 以 `PartialEq` 为 supertrait，要求 `a == b` 与 `a.partial_cmp(b) == Some(Ordering::Equal)` 完全一致；[[hash.Hash|Hash]] 与它有一个跨 trait 的契约——`a == b` 时两者的哈希值必须相同。这就是手写 `eq` 之后经常必须同时手写 `hash` 的原因。

## 示例

### 只比较用于「身份」的字段

```rust
#[derive(PartialEq, Debug)]
enum BookFormat {
    Paperback,
    Hardback,
    Ebook,
}

struct Book {
    isbn: i32,
    format: BookFormat,
}

// 只按 isbn 判断两本书是不是同一本书，装帧不参与比较
impl PartialEq for Book {
    fn eq(&self, other: &Self) -> bool {
        self.isbn == other.isbn
    }
}

fn main() {
    let b1 = Book { isbn: 3, format: BookFormat::Paperback };
    let b2 = Book { isbn: 3, format: BookFormat::Ebook };
    let b3 = Book { isbn: 10, format: BookFormat::Paperback };

    assert!(b1 == b2);
    assert!(b1 != b3);
    // ne 是默认实现，等价于 !(b1 == b3)
    assert!(b1.ne(&b3));
}
```

### 跨类型比较

`Rhs` 参数允许同一个类型与别的类型比较。注意 `==` 的类型检查要求**两个方向各自有 impl**，只写一半时 `b1 == format` 能编译、`format == b1` 不能。

```rust
#[derive(PartialEq, Debug)]
enum BookFormat {
    Paperback,
    Hardback,
    Ebook,
}

struct Book {
    isbn: i32,
    format: BookFormat,
}

impl PartialEq for Book {
    fn eq(&self, other: &Self) -> bool {
        self.isbn == other.isbn
    }
}

// Book == BookFormat
impl PartialEq<BookFormat> for Book {
    fn eq(&self, other: &BookFormat) -> bool {
        self.format == *other
    }
}

// BookFormat == Book，补上反方向，比较才是对称的
impl PartialEq<Book> for BookFormat {
    fn eq(&self, other: &Book) -> bool {
        *self == other.format
    }
}

fn main() {
    let b1 = Book { isbn: 3, format: BookFormat::Paperback };

    assert!(b1 == BookFormat::Paperback);
    assert!(BookFormat::Ebook != b1);
}
```

### NaN 说明为什么需要 Partial

```rust
fn main() {
    let nan = f64::NAN;

    // 自反性失效：自己不等于自己
    assert!(nan != nan);
    assert!(!nan.eq(&nan));

    // 于是 contains 找不到任何 NaN
    let values = vec![f64::NAN];
    assert!(!values.contains(&f64::NAN));

    // 排序所需的 Ordering 也拿不到
    assert_eq!(nan.partial_cmp(&nan), None);
}
```

## 常见陷阱

1. **让 `eq` 与 `ne` 打架**：覆写 `ne` 时忘了保持互斥，`a == b` 与 `a != b` 可能同时为真，逻辑上无法自洽。
2. **用 `==` 比较浮点数**：`0.1 + 0.2 != 0.3`，这是二进制表示问题而不是 `PartialEq` 的问题；比较浮点应判断差值是否小于误差，或改用整数/定点数。
3. **跨类型比较只写一个方向**：对称性要靠两个 impl 支撑，只写 `impl PartialEq<BookFormat> for Book` 时反方向编译不过。
4. **手写 `eq` 后忘了 `Hash`**：`a == b` 必须保证 `hash(a) == hash(b)`。若 `eq` 只比较部分字段（例如忽略大小写），派生的 `hash` 就与它不一致，键会「存得进、查不到」。
5. **以为 `==` 会移动值**：`eq` 接收 `&self` 与 `&other`，比较后两个值都还能继续用。
6. **忽略派生的泛型约束**：为 `struct Wrapper<T>` 派生会生成 `impl<T: PartialEq> PartialEq for Wrapper<T>`；想让外层「永远相等」而不管 `T`，必须手写 `impl<T> PartialEq for Wrapper<T>`。

## 相关

- [[cmp|std::cmp 模块]]：`PartialEq` 所属模块。
- [[cmp.Eq|Eq]]：在 `PartialEq` 之上补上自反性。
- [[cmp.PartialOrd|PartialOrd]]：以 `PartialEq` 为前提提供大小比较。
- [[cmp.Ordering|Ordering]]：比较得到的三个值。
- [[hash.Hash|Hash]]：与 `PartialEq` 共享「相等则同哈希」的契约。
- [[primitive.浮点类型|f64]]：只实现 `PartialEq` 而不实现 `Eq` 的典型。
- [[15-trait 基础|trait 基础]]：trait 定义、派生宏与泛型约束的基础。
