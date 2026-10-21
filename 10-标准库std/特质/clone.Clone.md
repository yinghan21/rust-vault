---
title: "std::clone::Clone"
type: std-条目
kind: 特质
module: clone
slug: clone.Clone
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - Clone
一句话: 定义显式复制值的契约，用 clone 拿到一个新值，代价由实现者决定。
---

# Clone

> [!abstract] 一句话
> `Clone` 给类型一个「显式复制自己」的入口 `.clone()`：它总是产出新值，但新值内部可能只是共享指针，因此既可能非常便宜，也可能非常昂贵。

## 简介

`Clone` 只规定一件事：`fn clone(&self) -> Self` —— 借来一个 `self`，交出一个类型相同的新值。它并不承诺新值与旧值在内存上互不相干：复制 `Rc<T>`、`Arc<T>`、`&T` 时得到的仍是同一份底层数据，只是多了一个持有者。

编译器**不会**自动调用 `clone`。需要复制的地方必须写出来：`.clone()`、`to_vec()`、`#[derive(Clone)]` 生成的代码。这一点与 [[marker.Copy|Copy]] 正相反 —— `Copy` 类型的赋值和传参由编译器隐式完成。所以「代码里出现的 `.clone()`」本身就是一句性能与语义的声明。

标准库在几处依赖它：`#[derive(Clone)]` 为每个字段生成 `field.clone()`；容器的 `clone` 要求元素 `T: Clone`（如 `impl<T: Clone> Clone for Vec<T>`）；`slice::to_vec`、`Vec::to_vec`、`str::to_owned` 也以 `Clone`/`ToOwned` 为前提。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `clone()` | 返回 `self` 的一个副本。 |

签名是 `fn clone(&self) -> Self`。注意它**借用** `&self` 而不是消耗 `self`：调用之后原值仍然可用，这与 `Into::into` 一类的消耗式转换完全不同。

## 提供的方法

| 方法 | 说明 |
| --- | --- |
| `clone_from(source)` | 用 `source` 的内容覆盖自身，尽量复用已有分配。 |

签名是 `fn clone_from(&mut self, source: &Self)`。默认实现等价于 `*self = source.clone()`：扔掉旧值，再改造一份新的。`String`、`Vec<T>` 等容器覆写了它，得以清空后重填并保留原有堆缓冲区，因此在「反复用新数据刷新同一个变量」的循环里，`clone_from` 通常比 `a = b.clone()` 更省。

## 与相邻 trait 的关系

`Copy` 与 `Clone` 常被混为一谈，区别全在「谁发起」和「能否自定义」：

| 维度 | `Clone` | `Copy` |
| --- | --- | --- |
| 触发方式 | 显式调用 `.clone()` | 赋值、传参、构造数组时隐式发生 |
| 有无方法 | 有 `clone`、`clone_from`，可写任意代码 | 空特质，没有方法可覆写 |
| 代价 | 任意，可能分配堆内存 | 按位复制，必然便宜 |
| 约束关系 | 最底层，无 supertrait | `trait Copy: Clone`，是 `Clone` 的 subtrait |
| 与 `Drop` | 可以共存 | 互斥，不能同时实现 |

因为 `Copy: Clone`，「能 `Copy` 就一定 `Clone`」；反过来不成立，`String`、`Vec<T>` 就是反例 —— 它们管理堆内存，无法按位复制。对 `T: Copy` 的类型调用 `.clone()` 合法但毫无意义，`clippy::clone_on_copy` 会给出警告。

另一个容易混淆的是 `ToOwned`：`Clone` 要求 `Self: Sized`，而 `ToOwned` 可以把 `&str` 这类 `?Sized` 类型「克隆」成拥有所有权的 `String`。

## 示例

### derive 与手写实现

```rust
#[derive(Clone, Debug)]
struct Point {
    x: i32,
    y: i32,
}

#[derive(Debug)]
struct Meter(f64);

// 手写实现：clone 里的行为完全由自己决定
impl Clone for Meter {
    fn clone(&self) -> Self {
        Meter(self.0)
    }
}

fn main() {
    let a = Point { x: 1, y: 2 };
    let b = a.clone();

    // a 没有被移动，clone 只借用了它
    assert_eq!((a.x, a.y), (b.x, b.y));
    println!("{a:?} / {b:?}");

    let m = Meter(1.5);
    let n = m.clone();
    assert_eq!(n.0, 1.5);
}
```

### 克隆智能指针只复制指针

```rust
use std::cell::Cell;
use std::rc::Rc;

#[derive(Clone)]
struct Counter {
    value: Rc<Cell<i32>>,
}

fn main() {
    let a = Counter { value: Rc::new(Cell::new(0)) };
    let b = a.clone();

    b.value.set(7);
    // 两份 Counter 共享同一个 Cell，改一处两处都变
    assert_eq!(a.value.get(), 7);
    assert_eq!(Rc::strong_count(&a.value), 2);
}
```

### 用 `clone_from` 复用缓冲区

```rust
fn main() {
    let mut buf = Vec::with_capacity(100);
    buf.extend([1, 2, 3]);

    let fresh = vec![9, 8, 7, 6, 5];
    buf.clone_from(&fresh);

    assert_eq!(buf, fresh);
    // 容量被复用，没有按新长度重新分配
    assert_eq!(buf.capacity(), 100);
}
```

## 常见陷阱

1. **以为 `clone` 一定是深拷贝**：`Rc`/`Arc`/`&T` 的 `clone` 只复制指针或增加引用计数，改一处会影响另一处；要真正隔离数据，得手写深拷贝或先解开共享。
2. **在热循环里克隆大容器**：`v.clone()` 每次都要分配并逐元素复制；只需读就传 `&v`，只需遍历一次就 `into_iter()` 拿走所有权。
3. **对 `Copy` 类型写 `.clone()`**：语义上多余，删掉即可，编译器会隐式复制。
4. **用 `a = b.clone()` 刷新同一变量**：旧缓冲被丢弃、重新分配；改用 `a.clone_from(&b)`。
5. **误判 `#[derive(Clone)]` 的约束**：它为泛型结构体生成的是 `impl<T: Clone> Clone for Wrapper<T>`；若希望「外层 `Clone` 而 `T` 不必 `Clone`」，必须手写 `impl<T> Clone for Wrapper<T>`（例如内部存 `Rc<T>` 时）。

## 相关

- [[clone|std::clone 模块]]：`Clone` 所属模块。
- [[marker.Copy|Copy]]：隐式按位复制，与 `Clone` 互补。
- [[vec.Vec|Vec]]、[[string.String|String]]：最常被克隆的容器，也是必须手写 `clone` 的典型。
- [[rc.Rc|Rc]]、[[sync.Arc|Arc]]：`clone` 只增加引用计数的共享指针。
- [[borrow.Cow|Cow]]：写时克隆，用来避免不必要的 `clone`。
- [[15-trait 基础|trait 基础]]：派生宏与 trait 约束的基础。
