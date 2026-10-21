---
title: "std::hash::Hash"
type: std-条目
kind: 特质
module: hash
slug: hash.Hash
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - Hash
一句话: 定义「值怎样喂给哈希器」的契约，是 HashMap / HashSet 能把键放进桶里的前提。
---

# `Hash`

> [!abstract] 一句话
> `Hash` 让一个值可以把自身内容写进任意 `Hasher`：实现者只负责「往哈希器里喂什么」，具体算法由哈希器决定，所以同一份数据既能算 `DefaultHasher`，也能算别的摘要。

## 简介

`Hash` 与 `Eq` 是一对搭档。`HashMap` 查键分两步：先用 `Hash` 算出桶号，再在桶里用 `Eq` 逐个比较。因此 `Hash` 不负责判等，只负责「把相等的值压到同一个哈希上」。

契约只有一条，但极其重要：**若 `a == b`，则 `hash(a) == hash(b)`**。反过来不成立——不同的值哈希碰撞是允许的，`HashMap` 会靠 `Eq` 解决掉。破坏这条契约的后果是「刚插进去的键查不到」。

字段全部实现 `Hash` 时，`#[derive(Hash)]` 会把每个字段依次喂进哈希器，够用就不要再手写。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `hash(&self, state)` | 把值的全部内容喂给给定的 `Hasher`。 |

完整签名：`fn hash<H: Hasher>(&self, state: &mut H)`。

## 提供的方法

| 方法 | 说明 |
| --- | --- |
| `hash_slice(data, state)` | 把同类型切片一次性喂入哈希器（1.3.0 起）。 |

`hash_slice` 有默认实现（逐个元素调用 `hash`），所以实现 `Hash` 时不必写它。但 `[u8]`、`[i32]` 等内置类型重写了它，按字节块整体写入；自己给字节切片写手工循环反而更慢。特化只对实现了 `Hash` 的类型生效，不能由用户任意扩展。

## 与相邻 trait 的关系

| trait | 关系 |
| --- | --- |
| `Eq` / `PartialEq` | `HashMap` 要求键同时满足 `Hash + Eq`；两者必须覆盖同一批字段。 |
| `Hasher` | 哈希算法的另一端：`write_u64`、`write`、`finish` 都由它定义。 |
| `Borrow` | `map.get(&key)` 能接受 `&str` 查 `HashMap<String, _>`，靠 `Hash` 与 `Borrow` 的一致性。 |
| `Ord` / `PartialOrd` | 有序容器（`BTreeMap`）用的是排序而不是哈希，与 `Hash` 无关。 |

## 示例

### 派生 `Hash` 并使用哈希器

```rust
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

// 想当 HashMap 的键，Hash 与 Eq 必须成对派生
#[derive(Hash, PartialEq, Eq)]
struct Rustacean {
    name: String,
    country: String,
}

fn hash_of<T: Hash>(value: &T) -> u64 {
    let mut hasher = DefaultHasher::new();
    value.hash(&mut hasher);
    hasher.finish()
}

fn main() {
    let ferris = Rustacean {
        name: String::from("Ferris"),
        country: String::from("Crabland"),
    };
    let twin = Rustacean {
        name: String::from("Ferris"),
        country: String::from("Crabland"),
    };

    // 相等的值必须哈希相同，这是 Hash 的核心契约
    assert_eq!(hash_of(&ferris), hash_of(&twin));

    // 正因为契约成立，键的「副本」才能查回原值
    let mut map = std::collections::HashMap::new();
    map.insert(ferris, 1);
    assert_eq!(map.get(&twin), Some(&1));
}
```

### 手写实现，只哈希参与判等的字段

```rust
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

struct Person {
    id: u32,
    name: String,
    phone: u64,
}

// 只把 id 与 phone 喂进哈希器，name 不参与
impl Hash for Person {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.id.hash(state);
        self.phone.hash(state);
    }
}

// 判等必须正好覆盖同一批字段，否则契约被破坏
impl PartialEq for Person {
    fn eq(&self, other: &Self) -> bool {
        self.id == other.id && self.phone == other.phone
    }
}

impl Eq for Person {}

fn main() {
    let mut hasher = DefaultHasher::new();
    Person { id: 7, name: String::from("Ada"), phone: 100 }.hash(&mut hasher);
    let first = hasher.finish();

    let mut hasher = DefaultHasher::new();
    Person { id: 7, name: String::from("Grace"), phone: 100 }.hash(&mut hasher);

    // name 不同但判等相同，所以哈希也必须相同
    assert_eq!(first, hasher.finish());
}
```

## 常见陷阱

1. **`Hash` 与 `Eq` 的字段集合不一致**：`Hash` 只哈希 `id`、`Eq` 却比较 `name`，就会出现「插入成功但 `get` 返回 `None`」，这是 `HashMap` 最典型的幽灵 bug。
2. **把哈希值当唯一 ID**：`finish()` 返回值会碰撞，去重和身份判断仍然依赖 `Eq`。
3. **哈希值不可持久化**：`DefaultHasher` 的算法不保证跨版本、跨平台一致，存进数据库或做跨进程比较都会失效。
4. **浮点数不能直接做键**：`f64` / `f32` 没有实现 `Hash`，必须用 `to_bits()` 或换成定点数。
5. **给字节切片手写哈希循环**：`hash_slice` 与内置实现的整体写入更快，逐字节 `hash(&mut h)` 会慢得多。
6. **忘记 `Sized` 约束**：`hash_slice` 的 `Self: Sized` 意味着 trait 对象不能直接调用它。

## 相关

- [[hash|std::hash 模块]]：`Hash`、`Hasher`、`BuildHasher` 与各哈希器实现。
- [[collections.HashMap|HashMap]]：最需要 `Hash` 一致性的容器。
- [[collections.HashSet|HashSet]]：基于 `Hash + Eq` 的集合类型。
- [[cmp.Eq|Eq]]：与 `Hash` 必须同步实现的判等特质。
- [[cmp.PartialEq|PartialEq]]：`Eq` 的基础，浮点只实现它。
- [[borrow.Borrow|Borrow]]：让 `map.get(&str)` 这种借用查询成立的前提。
