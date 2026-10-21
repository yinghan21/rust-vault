---
title: 方法与 impl
type: 学习笔记
stage: 基础
order: 9
tags:
  - rust/基础
aliases:
  - 方法与 impl
  - impl
一句话: impl 块把方法与 trait 实现挂到类型上，self 决定方法是借用还是消耗值。
updated: 2025-06-01
---

# 方法与 impl

> [!abstract] 一句话
> `impl` 块给类型安装行为：第一个参数是 `self` 的成了**方法**，没有 `self` 的是**关联函数**；接收者是 `self`、`&self` 还是 `&mut self`，直接决定调用会不会转移所有权。

## 为什么需要它

C 里「结构体 + 一组 `foo_init`/`foo_free` 函数」靠命名约定绑在一起，指针传错谁也不知道；Java 把方法写进类里，但所有方法都隐含 `this`，想「消耗掉对象」做不到；Go 的方法可以定义在任何类型上，却无法表达可变性约束。

Rust 用 `impl` 把行为附着在类型上，并用接收者类型把「读」「改」「消耗」写成签名的一部分。再加上 trait，同一套语法既能加固有方法，也能实现标准库约定的接口（[[15-trait 基础|trait 基础]]）。

## 核心规则

### 方法 vs 关联函数

```rust
#[derive(Debug)]
struct Counter { count: u32, step: u32 }

impl Counter {
    // 关联函数：没有 self，用类型名调用，惯例用来构造
    fn new(step: u32) -> Self { Counter { count: 0, step } }

    // &self：只读借用，不取得所有权
    fn value(&self) -> u32 { self.count }

    // &mut self：可变借用，调用者必须是 mut 变量
    fn tick(&mut self) { self.count += self.step; }

    // self：消耗所有权，调用后原值不可再用
    fn into_total(self) -> u32 { self.count }
}

fn main() {
    let mut c = Counter::new(5);
    c.tick();
    c.tick();
    println!("{}", c.value());          // 10，自动借用 &c
    println!("{}", Counter::value(&c)); // 等价写法：把接收者写成参数
    println!("{}", c.into_total());     // c 被消耗
}
```

`Self` 指当前类型，`Self { .. }` 与 `Counter { .. }` 等价。

### 三种接收者

| 接收者 | 语义 | 调用要求 |
| --- | --- | --- |
| `self` | 取得所有权，方法结束时值被释放 | 调用后原变量不可用 |
| `&self` | 只读借用 | 变量不必 `mut`，可同时多次调用 |
| `&mut self` | 可变借用 | 变量必须 `mut`，同一时刻只能有一个 |

### 自动引用与自动解引用

- 写 `c.value()` 时编译器自动补成 `Counter::value(&c)`，`c.tick()` 补成 `Counter::tick(&mut c)`——**不需要像 C 那样手动取地址**。
- 自动解引用：在 `Box<Point>`、`&Point`、`Rc<Point>` 上调用方法，会沿 `Deref` 链找到 `Point` 的方法，不必写 `(*p).norm2()`。
- 这套待遇**只给方法调用**；普通函数调用不会自动加 `&`，所以 `fn f(p: &Point)` 必须显式传 `&p`。

### 多个 impl 块与 trait 实现

- 固有方法可以分散在多个 `impl Counter { .. }` 块里（按功能分组），但同名方法只能出现一次，否则报 `E0592`。
- trait 实现必须写在 `impl Trait for Type { .. }` 里，一个类型对同一个 trait 只能有一个实现；孤儿规则要求 trait 或类型至少有一个是本地定义的。
- 固有方法与 trait 方法同名时，`c.foo()` 调用固有方法；要调 trait 版本就写 `Trait::foo(&c)`。

### 构造器惯例 `new` / `Default`

- `fn new(...) -> Self` 不是语言特性，只是社区惯例：名字统一、便于 `Type::new` 阅读。
- 有「合理空值」的类型实现 `Default`，就能用 `Type::default()` 和 `..Default::default()`（[[07-结构体|结构体]]）；`new` 与 `Default` 同时提供很常见。
- 构造可能失败时返回 `Result<Self, E>` 或 `Option<Self>`，而不是 `panic!`（[[11-错误处理|错误处理]]）。

## 代码示例

```rust
use std::fmt;

#[derive(Debug, PartialEq)]
struct Point { x: i32, y: i32 }

// 多个 impl 块是合法的，按功能拆开便于阅读
impl Point {
    fn new(x: i32, y: i32) -> Self { Point { x, y } }
    fn norm2(&self) -> i32 { self.x * self.x + self.y * self.y }
}

impl Default for Point {
    fn default() -> Self { Point::new(0, 0) }
}

// 为自定义类型实现 trait：impl Trait for Type
impl fmt::Display for Point {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({}, {})", self.x, self.y)
    }
}

impl From<(i32, i32)> for Point {
    fn from((x, y): (i32, i32)) -> Self { Point::new(x, y) }
}

fn main() {
    let a = Point::new(3, 4);
    let b: Point = (1, 2).into(); // 走 From
    println!("{a} {b} 默认 {}", Point::default());
    println!("{a} 到原点距离平方 = {}", a.norm2());
    assert_eq!(a, Point { x: 3, y: 4 });
    // 同名时 ual 方法优先，trait 版本要显式写全路径
    println!("{}", Point::from((0, 1)));
}
```

## 常见错误与解决

| 错误 / 现象 | 原因 | 解决 |
| --- | --- | --- |
| `E0599: no method named 'area' found for struct 'Rect'` | 方法名拼错，或方法来自未导入的 trait | 修正拼写；用 `use` 把 trait 引入作用域 |
| `E0596: cannot borrow 'c' as mutable, as it is not declared as mutable` | 调用了 `&mut self` 方法但变量不是 `mut` | 声明成 `let mut c = ...` |
| `E0502: cannot borrow 'c' as immutable because it is also borrowed as mutable` | 只读借用未结束就调用可变方法 | 先把值取出来，缩短借用作用域 |
| `E0507: cannot move out of 'self.x' which is behind a shared reference` | 在 `&self` 方法里把字段移出去 | 用 `.clone()`、`mem::take`，或把接收者改成 `self` |
| `E0592: duplicate definitions with name 'new'` | 两个 `impl` 块定义了同名固有方法 | 合并到一个块，或改名 |
| `E0061: this function takes 2 arguments but 1 was supplied` | 关联函数被当成方法调用，少传接收者 | 写成 `Type::func(x)`，或把第一个参数改成 `&self` |

## 练习

1. 给 `struct Rectangle { w: f64, h: f64 }` 写 `new`、`area(&self)`、`scale(&mut self, k: f64)`，再实现 `Default`。
2. 给一个自定义类型同时实现 `Display` 和 `From<i32>`，解释为什么不能写 `impl Display for Vec<i32>`。
3. 同一类型写 `fn take(self)`、`fn read(&self)`、`fn write(&mut self)` 三个方法，分别用 `let` 与 `let mut` 的变量去调用，记录编译错误的差别。

## 相关

- [[07-结构体|结构体]]：方法的宿主类型与字段可见性。
- [[08-枚举与模式匹配|模式匹配]]：在方法里用 `match` 处理枚举状态。
- [[15-trait 基础|trait 基础]]：`impl Trait for Type` 的完整规则。
- [[06-借用与引用|借用]]：`&self`/`&mut self` 与借用检查的关系。
- 标准库条目：[[fmt.Display|Display]]、[[default.Default|Default]]、[[convert.From|From]]。
