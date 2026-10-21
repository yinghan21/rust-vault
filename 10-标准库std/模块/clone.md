---
title: "std::clone"
type: std-模块
module: clone
stable: "1.0.0"
unstable: false
tags:
  - std/模块
  - std/特质
aliases:
  - clone
  - 克隆
一句话: `Clone` 特质所在的模块：为不能隐式复制的类型提供显式的复制能力。
---

# std::clone

> [!abstract] 一句话
> `std::clone` 定义 `Clone` 特质与 `#[derive(Clone)]` 派生宏，用于显式地复制一个值。

## 模块简介

Rust 把复制分成两种。`Copy` 类型（整数、`bool`、`char`、只含 `Copy` 字段的结构体）在赋值和传参时是隐式按位复制，原值仍然可用；其余类型默认**移动**，原值失效。`Clone` 就是为后者准备的显式复制入口：调用 `.clone()`，得到一个独立的新值。

两者的边界很清楚：`Copy` 要求类型不含 `Drop`、所有字段都是 `Copy`，复制必须是廉价的按位拷贝；`Clone` 没有这些限制，可以深拷贝堆上的 `Vec`、`String`，也可以只增加引用计数（`Rc`、`Arc`）。**实现了 `Copy` 的类型一定实现了 `Clone`**，反之不然。

绝大多数情况下用 `#[derive(Clone)]` 就够了，它会按字段声明顺序逐个调用 `clone`。手写实现时，`clone_from` 可以复用目标值已有的堆分配（`String::clone_from` 不会重新分配缓冲区），在循环里反复克隆到同一个变量时能省下不少分配。

要注意克隆的语义差异：`i32` 的 `clone` 是复制，`Vec<String>` 的 `clone` 是逐元素深拷贝，`Rc<T>` 的 `clone` 只是增加计数。读文档时先确认你拿到的是哪一种。

## 快速上手

```rust
#[derive(Clone, Debug, PartialEq)]
struct Config {
    name: String,
    retries: u32,
}

fn main() {
    let a = Config {
        name: String::from("server"),
        retries: 3,
    };

    // 显式克隆：a 仍然可用，两个值各自拥有自己的 String
    let b = a.clone();
    assert_eq!(a, b);

    // clone_from 复用目标已有的堆分配
    let mut c = Config {
        name: String::new(),
        retries: 0,
    };
    c.clone_from(&a);
    assert_eq!(c, a);

    // Vec 的 clone 是深拷贝，元素逐个克隆
    let v = vec![String::from("你好")];
    let w = v.clone();
    assert_eq!(v, w);
    assert_eq!(v[0], w[0]);
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[clone.Clone|Clone]] | 允许显式复制值的特质，核心方法是 `clone`。 |
| `Clone::clone` | 返回 `Self` 的一份副本。 |
| `Clone::clone_from` | 把来源克隆进 `self`，可复用 `self` 已有分配。 |
| `#[derive(Clone)]` | 为结构体或枚举自动生成逐字段克隆实现。 |
| [[marker.Copy|Copy]] | 隐式按位复制的标记特质，`Copy` 隐含 `Clone`。 |
| `Rc::clone` / `Arc::clone` | 只增加引用计数的浅克隆。 |
| `Vec::clone` / `String::clone` | 深拷贝全部内容，成本与长度成正比。 |
| `Box::clone` | 克隆装箱的值，需要 `T: Clone`。 |
| `Option::clone` / `Result::clone` | 内部值可克隆时，整体即可克隆。 |
| `impl Clone for T` | 手写实现，可只克隆需要的字段或自定义语义。 |

## 注意事项

> [!tip] 克隆不是免费的
> `Vec`、`String`、`HashMap` 的 `clone` 是 O(n) 深拷贝。热路径里优先传借用 `&T`；确实需要共享所有权时用 `Rc` / `Arc`，避免反复深拷贝。

> [!danger] 实现了 `Drop` 就不能是 `Copy`
> 编译器会直接拒绝同时派生 `Copy` 与 `Drop`。需要「可复制但带析构责任」时只实现 `Clone`，并把复制成本写进类型文档。

> [!warning] `Rc::clone` 不是深拷贝
> 它只复制指针并让计数加一，两个句柄指向同一份数据；想复制内容必须写 `(*rc).clone()`。

## 相关

- [[clone.Clone|Clone]]：本模块的核心特质。
- [[marker|std::marker 模块]]：`Copy`、`Send`、`Sync` 等标记特质。
- [[rc|std::rc 模块]]：引用计数与浅克隆语义。
- [[sync|std::sync 模块]]：`Arc` 的线程安全克隆。
- [[20-智能指针|智能指针]]：`Rc`、`Arc`、`Box` 的所有权与克隆策略。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 6 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 特质

- [[clone.Clone|`Clone`]]
- [`CloneToUninit`](https://doc.rust-lang.org/std/clone/trait.CloneToUninit.html)
- [`Share`](https://doc.rust-lang.org/std/clone/trait.Share.html)
- [`TrivialClone`](https://doc.rust-lang.org/std/clone/trait.TrivialClone.html)
- [`UseCloned`](https://doc.rust-lang.org/std/clone/trait.UseCloned.html)

### 其他

- [[clone.Clone|`Clone`]]

<!-- END AUTO ITEMS -->
