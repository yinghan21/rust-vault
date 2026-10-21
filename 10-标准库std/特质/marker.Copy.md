---
title: "std::marker::Copy"
type: std-条目
kind: 特质
module: marker
slug: marker.Copy
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - Copy
一句话: 标记特质，给类型打标后赋值与传参从移动变成按位复制，原变量继续可用。
---

# Copy

> [!abstract] 一句话
> `Copy` 是一个**标记特质**（marker trait）：给它打上标记后，类型的赋值、传参、返回从「移动」变成「按位复制」，原变量依然可用。

## 简介

默认情况下 Rust 的绑定拥有「移动语义」：`let y = x;` 之后 `x` 失效，因为所有权转给了 `y`。实现了 `Copy` 的类型改用「复制语义」：`let y = x;` 复制出一份等价的位模式，`x` 照旧可用。底层两种写法都可能只是把内存位抄一遍（很多时候还会被优化掉），真正的差别在于**编译器是否允许你在赋值后继续访问 `x`**。

`Copy` 没有任何方法，它只是给编译器的一句承诺：**按位复制就是合法的复制**。要作出这个承诺，必须满足 `trait Copy: Clone`，所以 `Copy` 类型一定同时也是 `Clone` —— 这就是 `#[derive(Copy, Clone)]` 总成对出现的原因。缺少 `Clone` 会直接编译失败（`the trait bound Foo: Clone is not satisfied`）。

它的使用完全由编译器驱动，源码里看不到任何调用痕迹：赋值、函数传参、返回值、数组与元组字面量、闭包按值捕获 `Copy` 变量、`match` 中按值绑定，凡需要保留原值的地方都会插入一次复制。

能实现 `Copy` 的类型：字段全部 `Copy` 的结构体/枚举/元组，以及整数、浮点、`bool`、`char`、共享引用 `&T`、函数指针、`Option<T>`（当 `T: Copy`）。不能实现的是管理堆资源或持有独占借用的类型：`String`、`Vec<T>`、`Box<T>`、`Rc<T>`、`&mut T`。

## 必须实现

无。`Copy` 是空特质，只带一个 supertrait：

```text
pub trait Copy: Clone {}
```

写法固定为 `#[derive(Copy, Clone)]` 或手写 `impl Copy for MyType {}`（此时 `Clone` 得另外实现）。它不是 `unsafe` trait —— 编译器无法验证「按位复制真的安全」，所以「类型内部没有独占资源」这条规则必须由实现者自觉遵守。

## 与相邻 trait 的关系

| 维度 | `Copy` | `Clone` |
| --- | --- | --- |
| 触发方式 | 编译器在赋值、传参时隐式插入 | 必须显式写 `.clone()` |
| 能否自定义 | 不能，空特质 | 能，`clone` 里可以写任意代码 |
| 代价 | 按位复制，必然便宜 | 任意，可能分配堆内存 |
| 关系 | `Copy: Clone`，subtrait | 更宽泛的父特质 |
| 示例类型 | `i32`、`bool`、`&T`、`Option<u8>` | `String`、`Vec<T>`、`Rc<T>` |

`Copy` 与 [[ops.Drop|Drop]] **互斥**：同一个类型不能既实现 `Copy` 又实现 `Drop`，否则编译器报 E0184（`the destructor cannot be implemented for type that implements Copy`）。原因是 `Copy` 会凭空造出多个「一模一样」的值，而 `Drop` 的语义是「这个值是它资源的唯一主人」；两者叠加就会导致同一份资源被析构多次。

`marker` 模块里的另外两个标记特质 [[marker.Send|Send]]、[[marker.Sync|Sync]] 由编译器自动推导（auto trait），而 `Copy` 必须显式声明 —— 这是它和它们最大的不同。

## 示例

### 移动与复制的差别

```rust
#[derive(Debug)]
struct NoCopy(u32);

#[derive(Debug, Copy, Clone)]
struct YesCopy(u32);

fn main() {
    let a = NoCopy(1);
    let b = a;
    // a 已被移进 b，取消下一行注释会编译失败
    // println!("{a:?}");
    assert_eq!(b.0, 1);

    let c = YesCopy(2);
    let d = c;
    // c 是复制而不是移动，仍然可用
    println!("{c:?} 与 {d:?}");
    assert_eq!(c.0, d.0);
}
```

### 传参、返回值与数组中的隐式复制

```rust
#[derive(Copy, Clone, Debug, PartialEq)]
struct Id(u32);

fn double(id: Id) -> Id {
    Id(id.0 * 2)
}

fn main() {
    let id = Id(21);

    // 传参是复制，id 没有被消耗
    let out = double(id);
    assert_eq!(out, Id(42));
    assert_eq!(id, Id(21));

    // 数组字面量同样复制
    let ids = [id; 3];
    assert_eq!(ids.len(), 3);
    assert_eq!(ids[2], Id(21));
}
```

### 为什么管理堆资源的类型不能 `Copy`

```rust
// 拥有堆缓冲区的类型：只能 Clone，不能 Copy
#[derive(Clone, Debug)]
struct MyBuf(Vec<u8>);

fn main() {
    let a = MyBuf(vec![1, 2, 3]);
    let b = a.clone();

    // 若允许按位复制，a 与 b 会各自认为自己独占同一个 Vec 缓冲区，
    // 离开作用域时对同一块内存释放两次
    assert_eq!(a.0, b.0);

    drop(b);
    assert_eq!(a.0.len(), 3);
}
```

## 常见陷阱

1. **只 derive `Copy` 不 derive `Clone`**：`Copy` 要求 `Clone`，编译报 `the trait bound ...: Clone is not satisfied`。
2. **结构体里混进一个非 `Copy` 字段**：`String`、`Vec<T>`、`Box<T>` 任一字段都会让整个类型失去 `Copy` 资格，编译器不会自动降级。
3. **给类型加了 `impl Drop` 再想 `Copy`**：E0184 直接拒绝；要么去掉 `Drop`（让字段自动析构），要么保留 `Drop` 并放弃 `Copy`。
4. **以为 `Copy` 能提速**：它只改变语义，不改变数据量。给含大数组的结构体实现 `Copy` 后，每次传参都会整块 memcpy，反而可能更慢 —— 这时该传引用。
5. **`&mut T` 不是 `Copy`**：只有共享引用 `&T` 是。否则一份可变借用会被复制成两份，别名规则当场失效。

## 相关

- [[marker|std::marker 模块]]：标记特质所在模块。
- [[clone.Clone|Clone]]：`Copy` 的 supertrait，复制语义的显式版本。
- [[ops.Drop|Drop]]：与 `Copy` 互斥的析构钩子。
- [[marker.Send|Send]]、[[marker.Sync|Sync]]：同模块的另两个自动推导标记特质。
- [[05-所有权|所有权]]：移动语义与复制语义的来龙去脉。
- [[06-借用与引用|借用]]：为什么 `&T` 可以 `Copy` 而 `&mut T` 不行。
