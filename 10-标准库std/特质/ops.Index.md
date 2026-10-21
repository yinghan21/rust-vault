---
title: "std::ops::Index"
type: std-条目
kind: 特质
module: ops
slug: ops.Index
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - Index
一句话: 定义不可变索引 container[index] 的行为，必须返回内部数据的引用而不是临时值。
---

# `Index`

> [!abstract] 一句话
> `Index` 让 `container[idx]` 这种语法对自己类型可用：`c[i]` 会展开成 `*c.index(i)`，所以它必须交出一个指向容器内部数据的引用，不能返回当场算出来的临时值。

## 简介

`Index` 是少数会改变「表达式类型」的运算符特质。`container[index]` 不是复制出一个值，而是对 `index()` 返回的引用做一次解引用——这也是为什么 `let x = v[i];` 只在元素是 `Copy` 时才能拿到值，否则得到的是「不能移出借用」的报错。

索引分两个方向：`Index` 用于不可变上下文（`&self`），`IndexMut` 用于 `v[i] = x` 这样的赋值（`&mut self`）。实现了 `Index` 不会自动获得 `IndexMut`，而 `IndexMut` 是 `Index` 的子特质。

索引参数 `Idx` 也是自由类型：可以是 `usize`，也可以是枚举、字符串、区间。越界检查完全由实现者决定——标准库的 `Vec` 选择 panic，`HashMap` 的 `Index` 也是 panic，而「查不到返回 `Option`」的需求要靠普通方法 `get`。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `index(&self, index)` | 执行索引运算，返回内部数据的引用。 |
| `type Output` | 关联类型，声明索引结果的类型。 |

完整签名：`fn index(&self, index: Idx) -> &Self::Output`。

`Output` 决定 `c[i]` 解引用后的类型，返回的引用必须真的指向 `self` 拥有的数据。

## 与相邻 trait 的关系

| trait | 关系 |
| --- | --- |
| `IndexMut` | 子特质，负责 `c[i] = v`；`IndexMut` 隐含 `Index`，反之不然。 |
| `Deref` | 同样是「借出一个引用」的运算符，但作用于 `*x` 而非 `x[i]`。 |
| `Get`（切片方法 `get`） | 返回 `Option<&T>` 的安全版本，不受索引语法约束。 |
| `RangeBounds` | `&v[1..3]` 这类切片索引通过 `Idx = Range<usize>` 实现。 |

## 示例

### 用枚举做索引

```rust
use std::ops::Index;

enum Nucleotide {
    A,
    C,
    G,
    T,
}

struct NucleotideCount {
    a: usize,
    c: usize,
    g: usize,
    t: usize,
}

impl Index<Nucleotide> for NucleotideCount {
    type Output = usize;

    // 返回值必须借自 self 的字段，而不是计算出的新值
    fn index(&self, nucleotide: Nucleotide) -> &Self::Output {
        match nucleotide {
            Nucleotide::A => &self.a,
            Nucleotide::C => &self.c,
            Nucleotide::G => &self.g,
            Nucleotide::T => &self.t,
        }
    }
}

fn main() {
    let counts = NucleotideCount { a: 14, c: 9, g: 10, t: 12 };

    assert_eq!(counts[Nucleotide::A], 14);
    assert_eq!(counts[Nucleotide::C], 9);
    assert_eq!(counts[Nucleotide::G], 10);
    assert_eq!(counts[Nucleotide::T], 12);
}
```

### 借用型索引：用 `&str` 查表

```rust
use std::collections::HashMap;
use std::ops::Index;

struct Scores(HashMap<String, u32>);

impl<'a> Index<&'a str> for Scores {
    type Output = u32;

    fn index(&self, name: &'a str) -> &u32 {
        // 索引语法无法表达「没找到」，所以查不到只能 panic
        self.0.get(name).expect("没有这个玩家的记录")
    }
}

fn main() {
    let mut table = HashMap::new();
    table.insert(String::from("ada"), 99);
    let scores = Scores(table);

    assert_eq!(scores["ada"], 99);
}
```

## 常见陷阱

1. **返回临时值**：`fn index(&self, i: usize) -> &u32 { &(self.a + self.b) }` 编译失败——借用检查器不允许把引用指向临时值；要么缓存到字段，要么改成普通方法返回裸值。
2. **以为 `Index` 给了 `IndexMut`**：`v[i] = x` 需要单独实现 `IndexMut`，只实现 `Index` 会报「cannot assign」。
3. **把越界交给调用者**：索引语法的返回类型里没有 `Option`，查不到就得 panic；要安全的语义请用 `get()` 或自定义方法。
4. **`c[i]` 会移动 `Output`**：`let s = map["k"];` 在 `Output = String` 时无法移动出借用，写 `let s = &map["k"];` 或 `clone()`。
5. **`Idx` 太难用**：索引参数定成 `String` 会让 `c["k"]` 直接报类型不匹配，用 `&str` 加生命周期参数更顺手。
6. **拿 `Index` 做有副作用的操作**：索引应当只读且便宜，别在里面加锁、做 I/O 或惰性初始化。

## 相关

- [[ops|std::ops 模块]]：索引、调用与算术运算符的特质集合。
- [[ops.Add|Add]]：同样依赖 `Output` 关联类型的运算符特质。
- [[ops.Deref|Deref]]：另一个「解引用」语义的运算符。
- [[collections.HashMap|HashMap]]：`Index` 与 `get` 的语义差异在这里最典型。
- [[primitive.slice|slice]]：内置切片索引与 `Range` 参数的实现。
- [[15-trait 基础|trait 基础]]：自定义 trait 实现的基本写法。
