---
title: "std::rc"
type: std-模块
module: rc
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - rc
一句话: 单线程引用计数指针 Rc<T>：一份数据多处只读共享，计数归零自动释放。
---

# std::rc

> [!abstract] 一句话
> `std::rc` 提供单线程的引用计数智能指针 [[rc.Rc|Rc]]：`clone` 只是把计数加一，最后一个指针销毁时才释放堆上的值。

## 模块简介

`Rc<T>` 解决的是「**同一份数据、多个所有者**」的问题。[[boxed.Box|Box]] 只能有一个主人，想给两个人用就得克隆数据；`Rc` 把值放在堆上，外面套一个「指向分配的指针 + 强引用计数 + 弱引用计数」，每次 `clone` 只复制指针并把计数加一，所有 `Rc` 都指向同一个值，计数减到 0 时才 drop 内部值。这是典型的共享所有权（shared ownership）结构，常用于图、树的双向链接、观察者列表、以及「多个结构体引用同一份只读配置」这类场景。

`Rc` 只提供**共享**访问，不提供可变访问。Rust 的借用规则没有因为 `Rc` 而放宽：拿到 `Rc<T>` 只能借出 `&T`。真要修改内部值，得把内部可变性容器塞进去，最常见的是 `Rc<RefCell<T>>`（单线程、运行时检查借用）或 `Rc<Cell<T>>`（`Copy` 类型、无借用检查）。这是 Rust 里「共享 + 可变」的标准组合，代价是借用错误从编译期推迟到运行期 panic。

「rc」是 Reference Counted 的缩写，前面的 r 也提醒你它是非原子的：计数用普通整数加减，开销极低，但**不是线程安全的**，`Rc<T>` 没有实现 `Send` / `Sync`，编译器会直接拦住把它送进 `thread::spawn` 的代码。需要跨线程共享，换 [[sync|std::sync]] 里的 `Arc<T>`——同样的语义，代价是原子操作。

模块里还有 [[rc.Rc|Rc]] 的弱引用版本 `Weak`：它不拥有数据、不增加强计数，用 `Rc::downgrade` 造出来、用 `upgrade` 尝试升级回 `Rc`。父子节点互相持有的结构（双向链表、树里子节点指回父节点）必须有一边用 `Weak`，否则两个 `Rc` 互指形成循环，计数永远不归零，内存就泄漏了。

## 快速上手

```rust
use std::cell::RefCell;
use std::rc::{Rc, Weak};

fn main() {
    // Rc::clone 只增加计数，不复制内部数据
    let shared = Rc::new(String::from("共享数据"));
    let a = Rc::clone(&shared);
    let b = shared.clone();
    assert_eq!(Rc::strong_count(&shared), 3); // shared、a、b 三个所有者
    assert_eq!(Rc::strong_count(&a), 3);
    drop(b);
    assert_eq!(Rc::strong_count(&a), 2);

    // 共享 + 可变：Rc<RefCell<T>> 是单线程的标准组合
    let log = Rc::new(RefCell::new(Vec::new()));
    log.borrow_mut().push("第一步");
    let log2 = Rc::clone(&log);
    log2.borrow_mut().push("第二步");
    assert_eq!(log.borrow().len(), 2);

    // Weak 不增加强计数，用来打破循环引用
    let owner = Rc::new(1u8);
    let weak: Weak<u8> = Rc::downgrade(&owner);
    assert_eq!(weak.strong_count(), 1);
    assert_eq!(weak.upgrade().as_deref(), Some(&1));
    drop(owner);
    assert!(weak.upgrade().is_none()); // 强引用清零后升级失败

    // 唯一引用时可以原地取出可变引用
    let mut only = Rc::new(10);
    if let Some(v) = Rc::get_mut(&mut only) {
        *v += 5;
    }
    assert_eq!(*only, 15);

    println!("强计数 = {}", Rc::strong_count(&shared));
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[rc.Rc\|Rc]] | 单线程引用计数指针，`clone` 只增计数。 |
| `rc::Weak` | 不拥有数据的弱引用，用于打破循环。 |
| `Rc::new` | 在堆上分配值并返回第一个 `Rc`。 |
| `Rc::clone` | 复制指针并把强计数加一。 |
| `Rc::strong_count` | 返回当前的强引用数量。 |
| `Rc::weak_count` | 返回当前的弱引用数量。 |
| `Rc::downgrade` | 从 `Rc` 创建 `Weak`，不增计数。 |
| `Weak::upgrade` | 尝试把 `Weak` 升级为 `Rc`，失败返回 `None`。 |
| `Rc::get_mut` | 唯一引用时取得 `&mut T`。 |
| `Rc::try_unwrap` | 计数为 1 时取出内部值。 |
| `Rc::ptr_eq` | 判断两个指针是否指向同一分配。 |
| `Rc::make_mut` | 写时克隆：多引用时先复制再给可变引用。 |
| `Rc::into_raw` / `Rc::from_raw` | 转成裸指针再收回（配合 FFI）。 |

## 注意事项

> [!warning] `Rc` 不是线程安全的
> `Rc<T>` 的计数是普通整数，多线程同时 `clone` 会数据竞争，所以它没有实现 `Send` / `Sync`。要把共享所有权送进 `thread::spawn`，请用 [[sync|std::sync]] 的 `Arc<T>`，别指望用 `unsafe` 绕过。

> [!danger] 循环引用会静默泄漏
> 两个 `Rc` 互指、或父节点用 `Rc` 持有子节点而子节点也用 `Rc` 指回父节点时，计数永远不归零，析构函数不会执行，`Weak::upgrade` 也一直成功。规则很简单：**单向拥有用 `Rc`，反向观察用 `Weak`**。Rust 不做循环检测，这类泄漏查起来比悬垂指针轻松，但仍是内存泄漏。

> [!tip] 性能与取舍
> `Rc::clone` 是一次非原子的整数自增，比 `Arc` 便宜，也比深拷贝便宜得多；但每次访问内部值都要多一次指针间接。真正需要「只读 + 多线程」时用 `Arc<T>`，完全不跨线程且只有一个所有者时用 [[boxed.Box|Box]] 更省一层计数。

## 相关

- [[rc.Rc|Rc]]：本模块的核心类型，方法都在这一页。
- [[sync|std::sync]]：`Arc`、`Mutex`、`RwLock`，多线程版本的共享所有权。
- [[cell|std::cell]]：[[cell.RefCell|RefCell]] 与 [[cell.Cell|Cell]]，给 `Rc` 补上内部可变性。
- [[boxed|std::boxed]]：单所有者的堆分配，与 `Rc` 对照看。
- [[20-智能指针|智能指针]]：`Box` / `Rc` / `RefCell` 的选型思路。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 3 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [[rc.Rc|`Rc`]]
- [`Weak`](https://doc.rust-lang.org/std/rc/struct.Weak.html)
- [`UniqueRc`](https://doc.rust-lang.org/std/rc/struct.UniqueRc.html)

<!-- END AUTO ITEMS -->
