---
title: "std::cell::Cell"
type: std-条目
kind: 结构体
module: cell
slug: cell.Cell
stable: "1.0.0"
tags:
  - std/类型
aliases:
  - Cell
一句话: 提供内部可变性的单元格，只能整体读（要求 Copy）或整体替换，没有任何运行时借用检查开销。
---

# `Cell`

> [!abstract] 一句话
> `Cell<T>` 让「只有不可变引用」的地方也能修改数据：`set` 换值、`get` 取一份拷贝，全程不需要运行时借用检查，因此也没有 panic 风险。

## 简介

`Cell<T>` 是最轻的内部可变性（interior mutability）容器。普通 Rust 规则是「有 `&T` 就不能改」，而 [[cell|std::cell 模块]] 里的类型绕开这条规则：`Cell<T>` 的 `set` / `replace` / `take` 都只要求 `&self`，因为它们不返回内部引用，只做整体读写。`Cell<T>` 与内部的 `T` 内存布局完全相同，没有额外标记位，开销可以忽略。

它之所以这么便宜，是因为它**拒绝出借引用**：你没法从 `Cell<T>` 拿到 `&T` 或 `&mut T`（`get` 靠 `T: Copy` 拷一份出来），所以不存在「一边持有引用一边被别人改掉」的风险，编译器不需要插入任何检查。需要真的借用内部数据（尤其是 `Vec`、`String` 这类非 `Copy` 类型）时，应该改用 [[cell.RefCell|RefCell]]，代价是运行时借用检查。

`Cell` 不是 `Sync`，不能跨线程共享；多线程做计数、开关这类整体读写请用 `std::sync::atomic` 里的原子类型。常见用法是给结构体加一个「可变计数器」字段，或给 `Rc` 树里的节点挂一个可改的标记，而不必把整棵树改成 `&mut`。

```rust
use std::cell::Cell;

fn main() {
    let c = Cell::new(1);
    c.set(10);
    assert_eq!(c.get(), 10);

    // 不可变的结构体里也能改 Cell 字段
    struct Counter {
        hits: Cell<u32>,
    }
    let counter = Counter { hits: Cell::new(0) };
    counter.hits.set(counter.hits.get() + 1);
    assert_eq!(counter.hits.get(), 1);

    // 切片视图：把 &Cell<[i32; 3]> 当成 &[Cell<i32>; 3] 用
    let array = Cell::new([1, 2, 3]);
    let cells = array.as_array_of_cells();
    cells[0].set(9);
    assert_eq!(array.into_inner(), [9, 2, 3]);
    println!("完成");
}
```

## 常用方法

### 构造与读写

| 方法 | 说明 |
| --- | --- |
| `new(value)` | 创建包含给定值的 `Cell`。 |
| `get()` | 返回内部值的一份拷贝，要求 `T: Copy`。 |
| `set(val)` | 替换内部值为 `val`。 |
| `replace(val)` | 替换内部值并返回被换掉的旧值。 |

### 交换、取走与更新

| 方法 | 说明 |
| --- | --- |
| `swap(other)` | 交换两个 `Cell` 的内部值。 |
| `take()` | 取走内部值，原地留下 `Default::default()`。 |
| `update(f)` | 用函数 `f` 就地更新内部值。 |

### 取出与借用

| 方法 | 说明 |
| --- | --- |
| `into_inner(self)` | 消耗 `Cell`，取出内部值。 |
| `get_mut(&mut self)` | 返回内部值的可变引用，无需拷贝。 |
| `from_mut(t)` | 转换 `&mut T` 为 `&Cell<T>`。 |

### 裸指针与批量视图

| 方法 | 说明 |
| --- | --- |
| `as_ptr()` | 返回指向内部数据的裸指针。 |
| `as_slice_of_cells()` | 返回 `&[Cell<T>]`，由 `&Cell<[T]>` 借出。 |
| `as_array_of_cells()` | 返回 `&[Cell<T>; N]`，由 `&Cell<[T; N]>` 借出。 |

> [!tip] 大批量元素要改时用切片视图
> 逐个 `Cell<T>` 访问很啰嗦，`as_slice_of_cells` / `as_array_of_cells` 让你在 `&[Cell<T>]` 上直接按下标 `set`，不必反复借出整个容器。

## 示例

```rust
use std::cell::Cell;

fn main() {
    let c = Cell::new(1);

    assert_eq!(c.replace(20), 1); // 返回旧值
    assert_eq!(c.get(), 20);
    assert_eq!(c.take(), 20); // 取走，留下 Default::default()
    assert_eq!(c.get(), 0);

    c.update(|v| v + 5);
    assert_eq!(c.get(), 5);

    let d = Cell::new(7);
    d.swap(&c);
    assert_eq!(c.get(), 7);
    assert_eq!(d.get(), 5);

    // get_mut 直接改，不需要 Copy
    let mut text = Cell::new(String::from("旧"));
    text.get_mut().push_str("值");
    assert_eq!(text.into_inner(), "旧值");

    // 从 &mut T 得到 &Cell<T>，给已有数据套上内部可变性
    let mut n = 0;
    let view: &Cell<i32> = Cell::from_mut(&mut n);
    view.set(42);
    assert_eq!(n, 42);

    // as_ptr 拿到裸指针，交给 FFI 或 unsafe 代码
    let raw = c.as_ptr();
    unsafe {
        assert_eq!(*raw, 7);
    }
}
```

## 常见陷阱

1. **对非 `Copy` 类型调用 `get()`**：编译不过，`get` 要求 `T: Copy`；改用 `replace` 配 `Default`，或 `take`。
2. **想从 `Cell` 借用内部数据**：它故意不提供 `&T` / `&mut T`，需要引用就用 [[cell.RefCell|RefCell]]。
3. **多线程共享 `Cell`**：`Cell` 不是 `Sync`，编译器会拒绝；多线程用 `AtomicUsize` 之类的原子类型。
4. **`take()` 遇上非 `Default` 类型**：`T` 必须实现 `Default`，否则只能用 `replace` 塞一个占位值。
5. **把 `as_ptr()` 的裸指针存起来长期使用**：`Cell` 一旦被移动或释放，指针立即失效，必须靠 `unsafe` 自己保证生命周期。

## 相关

- [[cell|std::cell 模块]]：本模块全部条目。
- [[cell.RefCell|RefCell]]：需要借用内部数据时的运行时检查版本。
- [[rc.Rc|Rc]]：与 `Cell` 组合成单线程可共享的可变状态。
- [[05-所有权|所有权]]、[[06-借用与引用|借用]]：内部可变性要绕开的那套规则。
- [[20-智能指针|智能指针]]：`Cell` / `RefCell` 与所有权模型的配合。
