---
title: "std::ptr"
type: std-模块
module: ptr
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - ptr
一句话: 手工操作内存：原始指针的读写、搬移、构造与比较，以及 NonNull 这个非空指针包装。
---

# std::ptr

> [!abstract] 一句话
> `std::ptr` 是绕过借用检查直接操作内存的工具箱：读写原始指针、批量搬移、手动析构、构造空/悬垂指针，全部要求调用者自己保证有效性。

## 模块简介

`*const T` 与 `*mut T` 是 Rust 的原始指针：可以为空、可以不对齐、可以悬垂、可以指向已经释放的内存，不参与借用检查，也没有生命周期参数。在安全代码里创建、比较、传递、转成整数都是合法的；**解引用**必须在 `unsafe` 块里，并且所有前置条件由你负责。

所以「这个指针有效吗」是个错误的问题——有效性是「指针 + 这一次访问」的属性：读还是写、访问几个字节、目标是否已经初始化、地址是否对齐、有没有别名冲突、对象在访问期间是否还活着。这个模块的函数文档几乎都在逐条列这些要求，读签名时顺手扫一眼前置条件，比事后对着 UB 调试便宜得多。

按用途可以分成几组。读写：`read` / `write` 针对单个值且不触发 Drop，`read_unaligned` / `write_unaligned` 放宽对齐要求，`*_volatile` 用于内存映射 IO 这类不能被优化掉的访问，`write_bytes` 是 memset 风格。搬移：`copy` 允许源与目标重叠，`copy_nonoverlapping` 不允许但更快，`swap` / `swap_nonoverlapping` 原地交换。生命周期：`drop_in_place` 手动执行析构。构造：`null`、`null_mut`、`dangling`、`from_ref`、`from_mut`，以及 `addr_of!` / `addr_of_mut!` 这对「取地址但不创建中间引用」的宏。最后是 `NonNull<T>`，一个非空、协变的 `*mut T` 包装，常用来做空指针优化和 FFI 签名。

较新的部分是 provenance（来源）：`without_provenance`、`with_exposed_provenance` 以及 `addr_of!` 系列，解决「指针 → 整数 → 指针」往返时不能凭空造出合法指针的问题；`Pointee` 与 `metadata` 则用来读取胖指针（`&dyn Trait`、`&[T]`）的元数据。日常业务代码基本碰不到这个模块，它的用户是手写容器、FFI、内联汇编和性能热点。

## 快速上手

```rust
use std::ptr::{self, NonNull};

fn main() {
    let mut value = 1u32;

    // 取地址：用 addr_of_mut! 而不是 &mut，避免创建中间引用
    let raw = ptr::addr_of_mut!(value);

    unsafe {
        // 读取但不移动：原值仍然归 value 所有
        assert_eq!(ptr::read(raw), 1);
        // 覆盖写入：不读取、也不 drop 旧值
        ptr::write(raw, 42);
        assert_eq!(*raw, 42);
    }
    assert_eq!(value, 42);

    // NonNull：非空、协变的指针包装
    let nn = NonNull::from(&mut value);
    unsafe {
        *nn.as_ptr() = 7;
    }
    assert_eq!(value, 7);

    // 空指针与悬垂指针都不允许解引用
    let null: *const u32 = ptr::null();
    assert!(null.is_null());

    let dangling: NonNull<u32> = NonNull::dangling();
    assert!(!dangling.as_ptr().is_null());
    assert_eq!(dangling.as_ptr() as usize % std::mem::align_of::<u32>(), 0);

    println!("全部通过");
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| `*const T` / `*mut T` | 原始指针类型本身，可空、可悬垂、不受借用检查约束。 |
| `ptr::addr_of!` / `addr_of_mut!` | 取字段地址而不创建中间引用，规避别名假设。 |
| `ptr::read` / `ptr::write` | 读 / 写单个值，都不触发目标位置旧值的 Drop。 |
| `ptr::read_unaligned` / `write_unaligned` | 允许地址未对齐的读写。 |
| `ptr::read_volatile` / `write_volatile` | 不会被优化器合并或删除的访问，用于内存映射 IO。 |
| `ptr::copy` / `copy_nonoverlapping` | 按字节块复制，前者允许重叠（memmove），后者更快（memcpy）。 |
| `ptr::swap` / `swap_nonoverlapping` | 原地交换两个值，不经过临时变量。 |
| `ptr::drop_in_place` | 手动执行析构，之后该内存视为未初始化。 |
| `ptr::write_bytes` | 把一块内存填成某个字节，类似 memset。 |
| `ptr::null` / `null_mut` | 空指针常量，只能比较、不能解引用。 |
| `ptr::dangling` / `dangling_mut` | 悬垂但非空且对齐的指针，给「空集合」当哨兵。 |
| `ptr::from_ref` / `from_mut` | 引用转原始指针，保留 provenance。 |
| `ptr::eq` / `addr_eq` | 比较指针是否相等，`addr_eq` 忽略胖指针的元数据。 |
| `NonNull<T>` | 非空且协变的 `*mut T` 包装，`Option<NonNull<T>>` 与指针同大小。 |
| `ptr::without_provenance` / `with_exposed_provenance` | 地址与指针互转时会用到的 provenance 接口。 |

## 注意事项

> [!danger] 创建无效指针不违规，解引用才违规
> `ptr::null()`、`NonNull::dangling()`、甚至指向已释放内存的指针，创建和比较它们都完全合法。真正触发未定义行为的是**解引用**，以及读写时违反对齐、初始化、别名或生命周期要求。空指针解引用永远是最直接的 UB。

> [!warning] `ptr::read` 是按位复制，不是移动
> `read` 拷贝一份返回，源位置的内存依然有效——同一个值于是有了两个所有者；如果 `T` 管着堆内存，两次 Drop 就是双重释放。真要搬移得配合 `ManuallyDrop` / `MaybeUninit` 保证源不再被 drop，日常场景直接用 [[mem|std::mem]] 的 `take` / `replace`。

> [!tip] 需要「可空」又要零开销就用 `NonNull`
> `Option<NonNull<T>>` 的大小和裸指针一样，空指针被当作 `None`，这是 `Vec`、`Box` 内部省内存的常用手法。另外 `Box::into_raw` 与 `Box::from_raw` 必须严格配对：只调前者是泄漏，重复调后者是双重释放。

## 相关

- [[mem|std::mem]]：`take`、`replace`、`swap`、`MaybeUninit`，比裸指针安全得多的替代品。
- [[24-unsafe 与 FFI|unsafe 与 FFI]]：原始指针出现的整体语境与安全契约写法。
- [[boxed.Box|Box]]：`into_raw` / `from_raw` 这组转换的另一半。
- [[slice|std::slice]]：`from_raw_parts` 构造切片时的长度与生命周期要求。
- [[ffi|std::ffi]]：跨语言边界上指针最常见的落点。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 39 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`NonNull`](https://doc.rust-lang.org/std/ptr/struct.NonNull.html)
- [`DynMetadata`](https://doc.rust-lang.org/std/ptr/struct.DynMetadata.html)

### 特质

- [`Pointee`](https://doc.rust-lang.org/std/ptr/trait.Pointee.html)

### 类型别名

- [`Alignment`](https://doc.rust-lang.org/std/ptr/type.Alignment.html)

### 函数

- [`addr_eq`](https://doc.rust-lang.org/std/ptr/fn.addr_eq.html)
- [`copy`](https://doc.rust-lang.org/std/ptr/fn.copy.html)
- [`copy_nonoverlapping`](https://doc.rust-lang.org/std/ptr/fn.copy_nonoverlapping.html)
- [`dangling`](https://doc.rust-lang.org/std/ptr/fn.dangling.html)
- [`dangling_mut`](https://doc.rust-lang.org/std/ptr/fn.dangling_mut.html)
- [`drop_in_place`](https://doc.rust-lang.org/std/ptr/fn.drop_in_place.html)
- [`eq`](https://doc.rust-lang.org/std/ptr/fn.eq.html)
- [`fn_addr_eq`](https://doc.rust-lang.org/std/ptr/fn.fn_addr_eq.html)
- [`from_mut`](https://doc.rust-lang.org/std/ptr/fn.from_mut.html)
- [`from_ref`](https://doc.rust-lang.org/std/ptr/fn.from_ref.html)
- [`hash`](https://doc.rust-lang.org/std/ptr/fn.hash.html)
- [`null`](https://doc.rust-lang.org/std/ptr/fn.null.html)
- [`null_mut`](https://doc.rust-lang.org/std/ptr/fn.null_mut.html)
- [`read`](https://doc.rust-lang.org/std/ptr/fn.read.html)
- [`read_unaligned`](https://doc.rust-lang.org/std/ptr/fn.read_unaligned.html)
- [`read_volatile`](https://doc.rust-lang.org/std/ptr/fn.read_volatile.html)
- [`replace`](https://doc.rust-lang.org/std/ptr/fn.replace.html)
- [`slice_from_raw_parts`](https://doc.rust-lang.org/std/ptr/fn.slice_from_raw_parts.html)
- [`slice_from_raw_parts_mut`](https://doc.rust-lang.org/std/ptr/fn.slice_from_raw_parts_mut.html)
- [`swap`](https://doc.rust-lang.org/std/ptr/fn.swap.html)
- [`swap_nonoverlapping`](https://doc.rust-lang.org/std/ptr/fn.swap_nonoverlapping.html)
- [`with_exposed_provenance`](https://doc.rust-lang.org/std/ptr/fn.with_exposed_provenance.html)
- [`with_exposed_provenance_mut`](https://doc.rust-lang.org/std/ptr/fn.with_exposed_provenance_mut.html)
- [`without_provenance`](https://doc.rust-lang.org/std/ptr/fn.without_provenance.html)
- [`without_provenance_mut`](https://doc.rust-lang.org/std/ptr/fn.without_provenance_mut.html)
- [`write`](https://doc.rust-lang.org/std/ptr/fn.write.html)
- [`write_bytes`](https://doc.rust-lang.org/std/ptr/fn.write_bytes.html)
- [`write_unaligned`](https://doc.rust-lang.org/std/ptr/fn.write_unaligned.html)
- [`write_volatile`](https://doc.rust-lang.org/std/ptr/fn.write_volatile.html)
- [`from_raw_parts`](https://doc.rust-lang.org/std/ptr/fn.from_raw_parts.html)
- [`from_raw_parts_mut`](https://doc.rust-lang.org/std/ptr/fn.from_raw_parts_mut.html)
- [`metadata`](https://doc.rust-lang.org/std/ptr/fn.metadata.html)

### 宏

- [`addr_of`](https://doc.rust-lang.org/std/ptr/macro.addr_of.html)
- [`addr_of_mut`](https://doc.rust-lang.org/std/ptr/macro.addr_of_mut.html)

### 其他

- [`Thin`](https://doc.rust-lang.org/std/ptr/traitalias.Thin.html)

<!-- END AUTO ITEMS -->
