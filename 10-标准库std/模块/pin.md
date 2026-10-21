---
title: "std::pin"
type: std-模块
module: pin
stable: "1.33.0"
unstable: false
tags:
  - std/模块
aliases:
  - pin
一句话: 把值钉在内存地址上：Pin 保证被指的值不移动，!Unpin 类型靠它支撑自引用结构与异步状态机。
---

# std::pin

> [!abstract] 一句话
> `std::pin` 用 `Pin<P>` 这个指针包装把「这个值在生命周期内不会被移动」写进类型系统，让安全代码能放心地在自引用结构和异步状态机上持有内部指针。

## 模块简介

只要有人持有指向某个值的指针，这个值就不能被搬走，否则指针立刻悬垂。Rust 平时靠移动语义加借用检查绕开这个问题：`&mut T` 独占借用期间，没人能移动它。但有两类东西躲不开——**自引用结构**（结构体里存着指向自己某个字段的指针）和**异步状态机**（`async fn` 编译后是一个保存局部变量的状态机，跨 `await` 的局部变量可能被自己的其它字段引用）。

`Pin<P>` 就是把「不能移动」写进类型系统的那层包装。`P` 可以是 `&mut T`、`Box<T>`、`&T` 等指针类型；一旦值处于 `Pin` 之下，安全代码就再也拿不到能把整个值移走的 `&mut T` —— 拿到的是 `Pin<&mut T>`，只能原地改、不能整体搬。

例外是 `Unpin`：一个自动实现的标记 trait，表示「移动这个类型没有危害」。`i32`、`String`、`Vec<T>` 以及绝大多数你自己写的结构体都是 `Unpin`，所以对它们 `Pin` 几乎没有额外限制，`get_mut`、`into_inner`、`Pin::set` 都能正常用。真正需要小心的是 `!Unpin` 类型：给结构体加一个 `PhantomPinned` 字段（[[marker|std::marker]] 里的零大小类型）就能让它不再自动实现 `Unpin`，此时 `Pin<&mut T>` 才真正锁死地址。

日常钉住一个值只有两种手法：`pin!` 宏在栈上钉（作用域结束自动释放），`Box::pin` 在堆上钉（可以放进结构体、跨任务传递）。`Pin::new` 只接受 `Unpin` 类型；给 `!Unpin` 类型用 `Pin::new_unchecked`、`map_unchecked_mut` 属于 `unsafe`，是给库作者写抽象时用的。

> [!note] 与异步的关系
> 这一层是**异步的地基**：[[future.Future|Future]] 的 `poll` 接收者是 `self: Pin<&mut Self>`，正因为它可能是自引用的状态机。看不懂 `Future` 时可以先记住结论——`Pin` 只负责「不许移动」，`Future` 只负责「可以反复轮询」。

## 快速上手

```rust
use std::marker::PhantomPinned;
use std::pin::Pin;

// PhantomPinned 让这个结构体不再自动实现 Unpin，也就是「不能移动」
struct SelfRef {
    name: String,
    _pin: PhantomPinned,
}

impl SelfRef {
    fn new(name: &str) -> Self {
        SelfRef {
            name: name.to_string(),
            _pin: PhantomPinned,
        }
    }

    // 接收者是 Pin<&mut Self>：调用者已经保证自己不会移动它
    fn greet(self: Pin<&mut Self>) -> String {
        format!("你好，{}", self.name)
    }
}

fn main() {
    // 1. 在栈上钉住：值活到作用域结束，期间地址不变
    let value = SelfRef::new("Rust");
    let mut pinned: Pin<&mut SelfRef> = std::pin::pin!(value);
    println!("{}", pinned.as_mut().greet());

    // 2. 需要放进结构体或跨任务传递时，用 Box::pin 钉在堆上
    let boxed: Pin<Box<SelfRef>> = Box::pin(SelfRef::new("Pin"));
    assert_eq!(boxed.name, "Pin");
    println!("堆上钉住：{}", boxed.name);

    // 3. 普通类型都是 Unpin，Pin 只是包装，随时能取回
    let mut n = 5i32;
    let p = Pin::new(&mut n);
    *p.get_mut() = 6;
    assert_eq!(n, 6);
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| `Pin<P>` | 指针包装，承诺被指的值在生命周期内不被移动。 |
| `std::pin::pin!` | 在栈上钉住一个值，返回 `Pin<&mut T>`。 |
| `Box::pin` | 把值钉在堆上，返回 `Pin<Box<T>>`。 |
| `Arc::pin` | 钉在堆上并共享，返回 `Pin<Arc<T>>`。 |
| `Pin::new` | 仅对 `Unpin` 类型可用的安全构造。 |
| `Pin::new_unchecked` | `unsafe` 构造，调用者承诺之后不移动被指值。 |
| `Pin::get_mut` / `get_unchecked_mut` | 取出 `&mut T`：前者要求 `Unpin`，后者是 `unsafe`。 |
| `Pin::into_inner` | 要求 `Unpin`，把包装拆掉拿回所有权。 |
| `Pin::as_ref` / `as_mut` | 重新借出一个更短生命周期的 `Pin`。 |
| `Pin::set` | 要求 `Unpin`，原地替换被钉住的值。 |
| `Pin::map_unchecked_mut` | `unsafe` 投影：把 `Pin<&mut T>` 变成某个字段的 `Pin<&mut Field>`。 |
| `Unpin` | 自动实现的标记 trait，表示移动无危害，绝大多数类型都是。 |
| `PhantomPinned` | 零大小类型，放进结构体就能让它变成 `!Unpin`。 |
| `UnsafePinned` | 更底层的类型：允许 `&mut` 不唯一的别名模型，供侵入式结构使用。 |
| `PinSafePointer` | 标记 trait：与 `Pin` 组合时行为规矩的指针类型。 |

## 注意事项

> [!warning] 先把「移动」这件事想清楚
> `Pin` 的几乎所有约束都是在防「把 `T` 从原地搬到别处」：`*pinned` 拷贝出来、`std::mem::swap`、`Vec::push` 都会触发移动。理解不了为什么 `Pin<&mut T>` 不能直接当 `&mut T` 用，先回看 [[20-智能指针|智能指针]] 里关于地址稳定性的讨论。

> [!danger] `Pin` 只约束安全代码
> `Pin` 是**安全抽象的地基**，不是「绝对禁止移动」的魔法。`unsafe` 代码依然可以违反约定，`&mut T` 与 `Pin<&mut T>` 之间转换时那些 `unchecked` 后缀的函数，就是在把保证责任交给你。写库时才需要这些，写业务代码不要碰。

> [!tip] 别自己实现结构化投影
> 把 `Pin<&mut 结构体>` 投影到某个字段，需要 `map_unchecked_mut` 加一堆「这个字段是否参与 pin」的纪律。这类代码只在实现自引用类型、异步运行时、侵入式容器时出现；普通业务里只需要 `pin!` 和 `Box::pin` 两个工具。

## 相关

- [[future.Future|Future]]：`poll` 为什么要求 `self: Pin<&mut Self>`。
- [[22-异步编程|异步编程]]：`async`/`await` 状态机与 `Pin` 的关系。
- [[future|std::future]]：异步 trait 的所在地。
- [[marker|std::marker]]：`Unpin`、`PhantomPinned` 都从这里导出。
- [[ptr|std::ptr]]：原始指针与地址层面的操作。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 4 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`Pin`](https://doc.rust-lang.org/std/pin/struct.Pin.html)
- [`UnsafePinned`](https://doc.rust-lang.org/std/pin/struct.UnsafePinned.html)

### 特质

- [`PinSafePointer`](https://doc.rust-lang.org/std/pin/trait.PinSafePointer.html)

### 宏

- [`pin`](https://doc.rust-lang.org/std/pin/macro.pin.html)

<!-- END AUTO ITEMS -->
