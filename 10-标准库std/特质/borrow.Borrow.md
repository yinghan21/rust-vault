---
title: "std::borrow::Borrow"
type: std-条目
kind: 特质
module: borrow
slug: borrow.Borrow
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - Borrow
一句话: 声明「我是同一份数据的另一种形态」，让 HashMap 能用 &str 查找 String 键。
---

# Borrow

> [!abstract] 一句话
> `Borrow<T>` 表示「我就是那个 `T` 的另一种表示」，`borrow` 借出 `&T`；与 [[convert.AsRef|AsRef]] 的签名一样，但它多承诺一条：`Eq`、`Ord`、`Hash` 的语义必须与借出的形式完全一致。`HashMap::get` 能用 `&str` 查 `String` 键，全靠这条契约。

## 简介

定义是 `pub trait Borrow<Borrowed> where Borrowed: ?Sized { fn borrow(&self) -> &Borrowed; }`。`Borrowed` 允许 `?Sized`，实际目标多是 `str`、`[T]`、`Path` 这类动态大小类型。

它要解决的是「同一种数据有多种表示」的问题。`String` 在 `str` 之上加了可增长的能力，`Vec<T>` 在 `[T]` 之上加了容量管理，`Box<T>`、`Rc<T>`、`Arc<T>` 加了存放位置与共享方式。这些包装类型都能通过引用「借成」被包装的形态：`String` 借成 `str`，`Vec<T>` 借成 `[T]`，`Box<T>` 借成 `T`。

标准库给出了一组自洽的实现：

| 条目 | 说明 |
| --- | --- |
| `impl<T: ?Sized> Borrow<T> for T` | 自反：任何类型都能借成自己。 |
| `impl<T: ?Sized> Borrow<T> for &T` | 引用借成被引用者。 |
| `Box<T>`、`Rc<T>`、`Arc<T>` | 借出内部的 `T`。 |
| `String` → `str`、`Vec<T>` → `[T]` | 包装类型借成切片/字符串。 |
| `Cow<'_, str>` → `str` | 写时克隆的两种形态都能借成 `str`。 |

关键在**语义契约**：`Borrow` 不只是「能转换」，而是「换了形态还是同一个东西」。因此官方文档要求 `Eq`、`Ord`、`Hash` 的行为在 `Self` 与 `Borrowed` 上必须一致。`String` 与 `str` 天然满足——同样的字节，同样的哈希，同样的比较结果。

这条契约的唯一大用户是容器的「异构查找」。`HashMap<K, V>::get` 的签名是 `fn get<Q>(&self, k: &Q) -> Option<&V> where K: Borrow<Q>, Q: Hash + Eq + ?Sized`：先用 `Q` 算哈希，再与 `K` 比较。只有当 `K` 与 `Q` 的哈希与相等语义一致时，这个查找才可能命中。`BTreeMap` 同理，边界是 `K: Borrow<Q>, Q: Ord`。

如果只是要「能拿到 `&T`」，用 [[convert.AsRef|AsRef]] 就够，不必背上一致性义务；需要可变形态则用 `BorrowMut`。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `borrow()` | 借出内部的 `&Borrowed`，必须与自身语义一致。 |

签名是 `fn borrow(&self) -> &Borrowed`。实现要直接返回内部那个值，不能做规范化、复制或分配——一旦借出的形态与自身在相等性上分家，容器的查找就会失效。

## 提供的方法

无。`Borrow` 只有 `borrow` 一个方法，`BorrowMut` 另有 `borrow_mut`，两者都没有默认实现。

## 与相邻 trait 的关系

这是全篇最需要分清的一对：

| 维度 | `Borrow<T>` | `AsRef<T>` |
| --- | --- | --- |
| 语义 | 同一份数据的另一种形态 | 能廉价地拿到某种 `&T` |
| 行为契约 | `Eq`/`Ord`/`Hash` 必须与 `T` 一致 | 无任何行为约束 |
| 目标数量 | 通常只有「那个」规范形态 | 可以有多个（`str`、`[u8]`、`Path`…） |
| 自反实现 | 有 `impl<T: ?Sized> Borrow<T> for T` | 没有，泛型里不能假设 `T: AsRef<T>` |
| 主要用途 | 容器键查找、`Cow` | 放宽函数参数 |
| 用在 `HashMap::get` | 正确，且是唯一被支持的写法 | 不行，缺少一致性保证 |

一个具体反例最能说明差别：假设给「大小写不敏感字符串」实现 `Borrow<str>`。`HashMap<CaseInsensitive, V>` 插入时用的是忽略大小写的哈希，而 `get(&str)` 用普通 `str` 的哈希去查，两者对不上，键永远查不到。这种实现对 `AsRef<str>` 无妨（它只是「能借成 `str`」），对 `Borrow<str>` 就是违约。反过来，`HashMap<String, V>` 用 `&str` 查找一切正常，因为 `String` 与 `str` 的哈希、相等完全一致。

第二个区分点是自反性：`Borrow` 有 `impl<T: ?Sized> Borrow<T> for T`，所以任何 `K` 都能借成 `K`，`HashMap::get(&k)` 传 `&K` 总是可行；`AsRef` 没有这个 blanket 实现。

## 示例

### HashMap 用 &str 查 String 键

```rust
use std::collections::HashMap;

fn main() {
    let mut scores: HashMap<String, i32> = HashMap::new();
    scores.insert("alice".to_string(), 90);
    scores.insert("bob".to_string(), 80);

    // K = String，Q = str：String: Borrow<str>，直接用 &str 查，无需建临时 String
    assert_eq!(scores.get("alice"), Some(&90));

    // 传 &String 也行，此时 Q 由自反实现推断为 String
    let key = String::from("bob");
    assert_eq!(scores.get(&key), Some(&80));

    assert_eq!(scores.get("carol"), None);
}
```

### 自定义 Borrow 让 newtype 按内部值查找

```rust
use std::borrow::Borrow;
use std::collections::HashMap;

#[derive(Hash, PartialEq, Eq, Debug)]
struct UserId(u32);

// 契约成立：UserId 的 Hash 与 Eq 都由内部 u32 派生，
// 所以借成 u32 之后语义完全一致
impl Borrow<u32> for UserId {
    fn borrow(&self) -> &u32 {
        &self.0
    }
}

fn main() {
    let mut names: HashMap<UserId, &str> = HashMap::new();
    names.insert(UserId(1), "alice");

    // 不必构造 UserId 就能查
    assert_eq!(names.get(&1u32), Some(&"alice"));
}
```

### Cow：借用与拥有共用一个接口

```rust
use std::borrow::Cow;

fn normalize(input: &str) -> Cow<'_, str> {
    if input.chars().all(|c| c.is_ascii_lowercase()) {
        // 已经是规范形式，直接借用，零分配
        Cow::Borrowed(input)
    } else {
        Cow::Owned(input.to_lowercase())
    }
}

fn main() {
    let borrowed = normalize("rust");
    let owned = normalize("RUST");

    assert!(matches!(borrowed, Cow::Borrowed(_)));
    assert!(matches!(owned, Cow::Owned(_)));
    assert_eq!(borrowed, "rust");
    assert_eq!(owned, "rust");
}
```

## 常见陷阱

1. **把 `Borrow` 当「廉价转换」随便实现**：它附带 `Eq`/`Ord`/`Hash` 一致性义务。给忽略大小写、忽略尾部空白的包装类型实现 `Borrow<str>`，`HashMap` 就会出现「存得进、查不到」。
2. **以为 `Borrow` 与 `AsRef` 可以互换**：函数参数用 `AsRef` 没问题，容器键查找必须用 `Borrow`；两者混用会编译不过或埋下不一致。
3. **忘了 `Borrow` 的目标只有一个规范形态**：`String` 只实现 `Borrow<str>`，没有 `Borrow<[u8]>`；想要字节视图请用 `AsRef<[u8]>`。
4. **`borrow` 与 `RefCell::borrow` 混淆**：同名不同物，后者返回 `Ref<T>` 并在运行时检查借用规则；两者都在作用域内时可能需要 `Borrow::borrow(&x)` 消歧。
5. **对引用类型多套一层**：`Borrow<T> for &T` 已经存在，`&&String` 这类写法常常多此一举，`*` 解一层更清楚。
6. **在 `borrow` 里做转换或分配**：返回的必须是内部那个值的引用；复制一份再返回既编译不过（生命周期不够）也违背语义。
7. **认为 `HashMap` 的键必须同型**：借助 `Borrow`，`HashMap<String, V>` 可以用 `&str` 查、`HashMap<Box<str>, V>` 也能用 `&str` 查，这是设计意图而非特例。

## 相关

- [[borrow|std::borrow 模块]]：`Borrow` 所属模块。
- [[borrow.Cow|Cow]]：把「借用或拥有」编码进类型，内部大量使用 `Borrow`。
- [[convert.AsRef|AsRef]]：签名相同但语义更弱的引用转换。
- [[collections.HashMap|HashMap]]：`get` 的 `K: Borrow<Q>` 边界是 `Borrow` 的主战场。
- [[collections.BTreeMap|BTreeMap]]：用 `Ord` 版本的同款查找边界。
- [[string.String|String]]：实现 `Borrow<str>`，让 `&str` 能查 `String` 键。
