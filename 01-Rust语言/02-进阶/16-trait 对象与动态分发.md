---
title: "trait 对象与动态分发"
type: 学习笔记
stage: 进阶
order: 16
tags:
  - rust/进阶
aliases:
  - trait 对象
  - dyn Trait
  - 动态分发
一句话: dyn Trait 把不同类型塞进同一个容器，代价是虚表跳转与一层间接寻址。
updated: 2025-06-10
---

# trait 对象与动态分发

> [!abstract] 一句话
> `dyn Trait` 是「只知道实现了哪个 trait、不知道具体类型」的值，通过虚表在运行时找到方法——这是 Rust 里做异构集合的方式。

## 为什么需要它

泛型是静态分发，`Vec<T>` 里只能放同一种类型；但插件、GUI 控件列表、错误链这类场景需要「一个容器里放多种实现」：

| 需求 | 泛型 | trait 对象 |
| --- | --- | --- |
| 一个 `Vec` 放多种类型 | ❌ 不行 | ✅ `Vec<Box<dyn Trait>>` |
| 编译期就知道具体类型 | ✅ | ❌ 运行时才知道 |

## `Box<dyn Trait>` 与 `&dyn Trait`

```rust
trait Shape {
    fn area(&self) -> f64;
    fn name(&self) -> &'static str { "形状" }
}

struct Circle(f64);
struct Square(f64);

impl Shape for Circle {
    fn area(&self) -> f64 { std::f64::consts::PI * self.0 * self.0 }
    fn name(&self) -> &'static str { "圆" }
}
impl Shape for Square {
    fn area(&self) -> f64 { self.0 * self.0 }
    fn name(&self) -> &'static str { "正方形" }
}

// 静态分发：每种 T 生成一份代码，可内联
fn total_static<T: Shape>(shapes: &[T]) -> f64 { shapes.iter().map(|s| s.area()).sum() }
// 动态分发：只有一份代码，运行时查虚表
fn total_dyn(shapes: &[&dyn Shape]) -> f64 { shapes.iter().map(|s| s.area()).sum() }

fn main() {
    // 拥有所有权的 trait 对象：放在堆上，容器里可以混放不同类型
    let shapes: Vec<Box<dyn Shape>> = vec![Box::new(Circle(1.0)), Box::new(Square(2.0))];
    let total: f64 = shapes.iter().map(|s| s.area()).sum();
    assert!((total - (std::f64::consts::PI + 4.0)).abs() < 1e-9);
    assert_eq!(shapes[0].name(), "圆");

    // 借用 trait 对象：零堆分配，&Square 自动转换为 &dyn Shape
    let mixed: [&dyn Shape; 1] = [&Square(2.0)];
    assert_eq!(total_dyn(&mixed), 4.0);
    assert!((total_static(&[Circle(1.0), Circle(2.0)]) - 15.707_963).abs() < 1e-4);
}
```

`dyn Shape` 是**未定大小类型**（unsized），不能直接当局部变量，必须套一层指针：

| 写法 | 拥有 | 堆分配 | 场景 |
| --- | --- | --- | --- |
| `Box<dyn Trait>` | 是 | 有 | 返回值、集合元素 |
| `&dyn Trait` | 否 | 无 | 函数参数，借用调用 |
| `&mut dyn Trait` | 否 | 无 | 需要调用 `&mut self` 方法 |

## 对象安全规则

不是所有 trait 都能变成 `dyn`，**对象安全**（object safety）要求：

```text
trait NotSafe {
    fn clone_me(&self) -> Self;      // ❌ 返回 Self，大小未知
    fn make<T: Default>(&self) -> T; // ❌ 泛型方法，虚表放不下无限多实例
    const ID: u32;                    // ❌ 关联常量
    fn new() -> Self;                 // ❌ 没有 self 的关联函数
}
```

规则：返回类型只能是 `&Self`、`Box<Self>` 这类不暴露大小的形式；方法不能带泛型参数；关联常量不被允许；没有 `self` 的关联函数可以写，但无法通过 `dyn` 调用。经典例子：`Clone` 有 `fn clone(&self) -> Self`，所以写不出 `Box<dyn Clone>`；而 `dyn Iterator<Item = u8>` 合法，因为关联类型已经写明。

## 静态分发 vs 动态分发

| 维度 | 静态分发 `T: Trait` | 动态分发 `&dyn Trait` |
| --- | --- | --- |
| 绑定时机 | 编译期 | 运行时查 vtable |
| 开销 | 零，可内联 | 一次间接调用，阻止内联 |
| 代码体积 | 每类型一份 | 一份 |
| 异构容器 | 不支持 | 支持 |

trait 对象的布局是「数据指针 + 虚表指针」，`&dyn Trait` 因此是 16 字节，比 `&T` 多一倍；`Box<dyn Trait>` 还多一次堆分配。

## 用枚举替代 trait 对象

类型集合封闭、且希望穷尽匹配时，枚举更合适：

```rust
enum ShapeKind {
    Circle(f64),
    Square(f64),
}

impl ShapeKind {
    fn area(&self) -> f64 {
        match self {
            ShapeKind::Circle(r) => std::f64::consts::PI * r * r,
            ShapeKind::Square(s) => s * s,
        }
    }
}

fn main() {
    let shapes = vec![ShapeKind::Circle(1.0), ShapeKind::Square(2.0)];
    let total: f64 = shapes.iter().map(|s| s.area()).sum();
    assert!((total - (std::f64::consts::PI + 4.0)).abs() < 1e-9);
}
```

枚举没有堆分配、大小固定，但**加新变体要改所有 `match`**；`Box<dyn Trait>` 加一个 `impl` 即可扩展，代价是每个值一次堆分配。写库时倾向 `enum`（可穷尽、无分配），需要让使用者自己实现行为时用 `dyn`。

## 常见错误与解决

| 错误 | 原因 | 解决 |
| --- | --- | --- |
| `E0038: the trait cannot be made into an object` | trait 不对象安全 | 改签名（返回 `Box<Self>`）、移走泛型方法，或改用泛型 |
| `E0277: size ... unknown at compile time` | 直接写了 `dyn Trait` 局部变量 | 套 `Box` / `&` / `Rc` |
| 想从 `dyn Trait` 取回具体类型 | trait 对象已擦除类型 | 用 `std::any::Any` + `downcast_ref` |

## 练习

1. 用 `Vec<Box<dyn Shape>>` 写函数，返回面积最大的那个 `Box`。
2. 解释 `fn clone_all(v: &[Box<dyn Clone>])` 为什么编译不过，给两种修法。

## 相关

- [[15-trait 基础|trait 基础]]：trait 的定义、默认方法与孤儿规则。
- [[14-泛型|泛型]]：静态分发与单态化带来的代码膨胀。
- [[20-智能指针|智能指针]]：`Box`、`Rc`、`Arc` 如何承载 trait 对象。
- 常用条目：[[boxed.Box|Box]]、[[error.Error|Error]]。
