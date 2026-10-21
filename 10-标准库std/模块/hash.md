---
title: "std::hash"
type: std-模块
module: hash
stable: "1.0.0"
unstable: false
tags:
  - std/模块
  - std/特质
aliases:
  - hash
一句话: 泛型哈希：Hash 特质描述值如何喂给哈希器，Hasher/BuildHasher 提供算法与构造，是 HashMap/HashSet 的地基。
---

# std::hash

> [!abstract] 一句话
> `std::hash` 把「一个值怎么变成哈希」抽象成三个角色：[[hash.Hash|Hash]]（值的哈希行为）、`Hasher`（哈希算法）、`BuildHasher`（哈希器的工厂），[[collections.HashMap|HashMap]] 与 [[collections.HashSet|HashSet]] 全靠它们工作。

## 模块简介

哈希表需要一个数字来定位桶。Rust 把这个过程拆成三层：`Hasher` 是**算法本身**，接收任意字节流并累积状态，最后 `finish()` 给出 `u64`；`Hash` 是**值如何写入这个字节流**的约定，只有方法 `hash(&self, state: &mut H)`；`BuildHasher` 则是**工厂**，每次建表时造一个 `Hasher`，从而支持「每张表用不同的随机种子」。

三者组合的好处是算法与数据类型解耦：标准库只需要给 `u64`、`String`、`&[T]` 等实现 `Hash`，任何哈希算法都能立即用于任何键类型。代价是你不能假设「同一个值在任何情况下哈希值相同」——`HashMap` 默认用 `RandomState`，每个进程、每张表都会换种子。

绝大多数场景只需要 `#[derive(Hash)]`。要求是：所有字段都实现 `Hash`，并且该类型同时实现 `Eq`——**`a == b` 必须推出 `hash(a) == hash(b)`**。这条契约哈希表无法检查，违反它不会报错，只会表现成「插入成功但查不到」。

需要自定义时手写 `impl Hash`，比如只哈希 ID 而忽略缓存字段。这时要格外小心：参与 `Eq` 比较的字段必须参与 `Hash`，反之（多哈希了无关字段）虽然合法，但会让相等的值得到不同哈希，同样破坏契约。

## 快速上手

```rust
use std::collections::HashMap;
use std::hash::{BuildHasherDefault, DefaultHasher, Hash, Hasher};

#[derive(Hash, PartialEq, Eq, Debug)]
struct User {
    id: u64,
    name: String,
}

// 用固定的 DefaultHasher 手动算哈希值
fn hash_of<T: Hash + ?Sized>(value: &T) -> u64 {
    let mut hasher = DefaultHasher::new();
    value.hash(&mut hasher);
    hasher.finish()
}

fn main() {
    // 1. 派生 Hash 后可以直接当 HashMap 的键
    let mut scores: HashMap<User, u32> = HashMap::new();
    scores.insert(User { id: 1, name: "alice".into() }, 100);
    let key = User { id: 1, name: "alice".into() };
    assert_eq!(scores.get(&key), Some(&100));

    // 2. 值相等 → 哈希相等；String 的 Hash 与 str 一致
    assert_eq!(hash_of(&key), hash_of(&User { id: 1, name: "alice".into() }));
    assert_eq!(hash_of("rust"), hash_of(&"rust".to_string()));

    // 3. 哈希值只在本进程内有意义：HashMap 默认用 RandomState，
    //    每次换种子结果就不同，所以不要持久化哈希值。

    // 4. 想固定种子、让结果可复现，就用 BuildHasherDefault
    let mut fixed: HashMap<&str, u8, BuildHasherDefault<DefaultHasher>> =
        HashMap::with_hasher(BuildHasherDefault::default());
    fixed.insert("k", 1);
    assert_eq!(fixed.get("k"), Some(&1));
    // 同样的键插两次仍然是同一个条目
    fixed.insert("k", 2);
    assert_eq!(fixed.len(), 1);

    // 5. 手动把字段按顺序喂给 Hasher，等价于自己写 Hash 实现
    let mut h = DefaultHasher::new();
    key.id.hash(&mut h);
    key.name.hash(&mut h);
    println!("手动哈希 = {}", h.finish());
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[hash.Hash\|Hash]] | 可哈希类型的特质，方法 `hash` 把自身写入 `Hasher`。 |
| `Hash::hash` | 实现它决定字段如何进入字节流，必须与 `Eq` 保持一致。 |
| `Hasher` | 哈希算法特质：`write` 系列输入 + `finish` 输出。 |
| `Hasher::finish` | 返回 `u64` 哈希值；同一状态多次调用结果相同。 |
| `Hasher::write_u64` / `write_u8` | 按整数宽度写入，避免借道 `&[u8]`。 |
| `BuildHasher` | 创建 `Hasher` 实例的工厂特质，`HashMap` 用它造哈希器。 |
| `RandomState` | `HashMap` 默认的 `BuildHasher`，带随机种子。 |
| `BuildHasherDefault` | 用 `Default` 造 `Hasher`，种子固定、结果可复现。 |
| `DefaultHasher` | 标准库默认的 `Hasher`，算法不承诺跨版本稳定。 |
| `SipHasher` | SipHash 2-4 的实现，已标记 `deprecated`，新代码用 `DefaultHasher`。 |
| `#[derive(Hash)]` | 按字段顺序自动生成 `Hash` 实现。 |

## 注意事项

> [!danger] `Hash` 与 `Eq` 必须一致
> 契约是「`a == b` ⇒ `hash(a) == hash(b)`」。只实现了 `Hash` 忘记 `Eq` 编译不过；手写 `Hash` 时漏掉参与比较的字段则能编译，但会让 `HashMap` 插入后查不到——这是最难查的一类 bug。派生 + 不改字段是最安全的做法。

> [!warning] 哈希值不是稳定标识
> `RandomState` 的随机种子意味着同一个键在不同进程、不同表里的哈希值不同（这是为了防 HashDoS 攻击）。所以：不要持久化哈希值、不要用哈希值当 ID、不要依赖遍历顺序——需要有序输出就用 [[collections.BTreeMap|BTreeMap]]。

> [!tip] 自定义 `Hash` 的时机
> 只在「键的相等语义少于所有字段」时才手写，例如只按 `id` 判等、忽略 `name`。这时应同时手写 `PartialEq`/`Eq` 与 `Hash`，保证两者看同一组字段；`Hash` 里不要做分配或重计算，它是每次查找都会走的热路径。

## 相关

- [[collections.HashMap|HashMap]] / [[collections.HashSet|HashSet]]：本模块最主要的消费者。
- [[cmp.Eq|Eq]]：与 `Hash` 绑定的一致性契约。
- [[borrow.Borrow|Borrow]]：`map.get(&str)` 这种跨类型查找依赖它。
- [[collections.BTreeMap|BTreeMap]]：需要有序遍历时的替代方案。
- [[collections|std::collections]]：哈希表与其他集合类型的总览。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 8 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`BuildHasherDefault`](https://doc.rust-lang.org/std/hash/struct.BuildHasherDefault.html)
- [`DefaultHasher`](https://doc.rust-lang.org/std/hash/struct.DefaultHasher.html)
- [`RandomState`](https://doc.rust-lang.org/std/hash/struct.RandomState.html)
- [`SipHasher`](https://doc.rust-lang.org/std/hash/struct.SipHasher.html)

### 特质

- [`BuildHasher`](https://doc.rust-lang.org/std/hash/trait.BuildHasher.html)
- [[hash.Hash|`Hash`]]
- [`Hasher`](https://doc.rust-lang.org/std/hash/trait.Hasher.html)

### 其他

- [[hash.Hash|`Hash`]]

<!-- END AUTO ITEMS -->
