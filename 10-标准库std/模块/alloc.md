---
title: "std::alloc"
type: std-模块
module: alloc
stable: "1.28.0"
unstable: false
tags:
  - std/模块
aliases:
  - alloc
一句话: 底层内存分配接口：用 `Layout` 描述布局，直接向全局分配器申请与释放内存。
---

# std::alloc

> [!abstract] 一句话
> `std::alloc` 是标准库最底层的分配入口：`Box`、`Vec`、`String` 背后的内存申请与释放，最终都落在这里。

## 模块简介

`std::alloc` 提供的是**手工内存管理**能力。它不做任何类型检查，只认一块「多大、怎么对齐」的内存，因此绝大多数业务代码不需要直接使用它，`Box<T>`、`Vec<T>` 已经把这些调用包好了。真正需要它的场景通常是：实现自定义容器、给 C 库交接缓冲区、写内存池或全局分配器。

模块可以分成三部分。第一部分是 `Layout`：用「大小 + 对齐」描述一块内存，`Layout::from_size_align` 会校验参数是否合法，不合法返回 `LayoutError`。第二部分是全局分配器上的裸操作函数：`alloc`、`alloc_zeroed`、`realloc`、`dealloc`，它们全是 `unsafe`，调用者要自己保证参数一致、只释放一次。第三部分是替换全局分配器的机制：`GlobalAlloc` trait 配合 crate 根上的 `#[global_allocator]` 属性，`System` 则是操作系统提供的默认实现。

它和 [[boxed|std::boxed]]、[[vec|std::vec]] 的关系是「地基与房子」：`Box::new` 会按 `Layout` 申请堆内存，`Vec` 扩容时就是一次 `realloc`。也正因为直接跨越了 safe Rust 的边界，这个模块的每个 `unsafe` 承诺都必须逐条遵守，否则就是未定义行为。

## 快速上手

```rust
use std::alloc::{alloc, dealloc, handle_alloc_error, Layout};

fn main() {
    // 用 Layout 描述一块内存：大小 4 字节、对齐 4 字节
    let layout = Layout::from_size_align(4, 4).expect("非法的布局参数");
    assert_eq!(layout.size(), 4);

    // 向全局分配器申请内存，失败返回空指针
    let p = unsafe { alloc(layout) } as *mut u32;
    if p.is_null() {
        handle_alloc_error(layout);
    }

    unsafe {
        p.write(42);
        assert_eq!(p.read(), 42);
        // 必须用与分配时完全相同的 layout 释放，且只能释放一次
        dealloc(p as *mut u8, layout);
    }

    println!("申请、读写、释放一块 4 字节内存完成");
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| `Layout` | 描述一块内存的大小与对齐，是所有分配函数的参数。 |
| `Layout::from_size_align` | 构造 `Layout`，参数非法时返回 `LayoutError`。 |
| `LayoutError` | 布局参数不合法时的错误类型。 |
| `alloc` | 向全局分配器申请未初始化内存（`unsafe`）。 |
| `alloc_zeroed` | 申请内存并把每个字节清零。 |
| `realloc` | 按新的 `Layout` 扩容或缩容已有内存块。 |
| `dealloc` | 释放内存，必须传入分配时的同一个 `Layout`。 |
| `handle_alloc_error` | 分配失败时的标准处理，默认直接终止进程，不返回。 |
| `GlobalAlloc` | 可注册为全局分配器的 trait，方法是 `alloc`/`dealloc`/`realloc`。 |
| `System` | 操作系统提供的默认分配器，可直接用作全局分配器。 |
| `#[global_allocator]` | 写在 crate 根上的属性，用来指定全局分配器类型。 |
| `Allocator` | 可增长、收缩任意内存块的扩展 trait，仍属未稳定的前沿接口。 |
| `set_alloc_error_hook` / `take_alloc_error_hook` | 注册 / 注销分配失败时的自定义钩子。 |

## 注意事项

> [!danger] `unsafe` 契约必须逐条满足
> `alloc` 拿到指针后要自己保证不越界写；`dealloc` 必须使用**与分配时完全相同**的 `Layout`，且每块内存只能释放一次。违反任何一条都是未定义行为，编译器不会替你检查。

> [!warning] 全局分配器全程序只能有一个
> `#[global_allocator]` 写在 crate 根，且一个程序只能注册一个分配器实现。分配器代码本身不能 panic、不能再申请内存，否则会在异常路径上递归或直接崩溃。

> [!tip] 日常优先用封装好的类型
> 需要一块字节缓冲区时可以先用 `Vec<u8>` 配合 `with_capacity`，需要单值堆分配时用 `Box`。只有在确实要控制分配时机、或对接 C 的内存所有权时，才值得手写这一层的 `unsafe` 代码。

## 相关

- [[模块索引]]
- [[boxed|std::boxed 模块]]：`Box<T>` 是对本模块的一次封装。
- [[vec|std::vec 模块]]：`Vec<T>` 的扩容就对应 `realloc`。
- [[ptr|std::ptr 模块]]：拿到的裸指针要靠它读写与转换。
- [[24-unsafe 与 FFI|unsafe 与 FFI]]：理解 `unsafe` 契约的前提。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 18 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`Layout`](https://doc.rust-lang.org/std/alloc/struct.Layout.html)
- [`LayoutError`](https://doc.rust-lang.org/std/alloc/struct.LayoutError.html)
- [`System`](https://doc.rust-lang.org/std/alloc/struct.System.html)
- [`AllocError`](https://doc.rust-lang.org/std/alloc/struct.AllocError.html)
- [`Global`](https://doc.rust-lang.org/std/alloc/struct.Global.html)

### 特质

- [`GlobalAlloc`](https://doc.rust-lang.org/std/alloc/trait.GlobalAlloc.html)
- [`Allocator`](https://doc.rust-lang.org/std/alloc/trait.Allocator.html)
- [`AllocatorClone`](https://doc.rust-lang.org/std/alloc/trait.AllocatorClone.html)
- [`GlobalAllocator`](https://doc.rust-lang.org/std/alloc/trait.GlobalAllocator.html)
- [`StaticAllocator`](https://doc.rust-lang.org/std/alloc/trait.StaticAllocator.html)

### 类型别名

- [`LayoutErr`](https://doc.rust-lang.org/std/alloc/type.LayoutErr.html)

### 函数

- [`alloc`](https://doc.rust-lang.org/std/alloc/fn.alloc.html)
- [`alloc_zeroed`](https://doc.rust-lang.org/std/alloc/fn.alloc_zeroed.html)
- [`dealloc`](https://doc.rust-lang.org/std/alloc/fn.dealloc.html)
- [`handle_alloc_error`](https://doc.rust-lang.org/std/alloc/fn.handle_alloc_error.html)
- [`realloc`](https://doc.rust-lang.org/std/alloc/fn.realloc.html)
- [`set_alloc_error_hook`](https://doc.rust-lang.org/std/alloc/fn.set_alloc_error_hook.html)
- [`take_alloc_error_hook`](https://doc.rust-lang.org/std/alloc/fn.take_alloc_error_hook.html)

<!-- END AUTO ITEMS -->
