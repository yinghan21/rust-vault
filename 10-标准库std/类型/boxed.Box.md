---
title: "std::boxed::Box"
type: std-条目
kind: 结构体
module: boxed
slug: boxed.Box
stable: "1.0.0"
tags:
  - std/类型
aliases:
  - Box
一句话: 唯一拥有堆分配的指针类型，用来把大值挪到堆上、打破递归类型的无限大小、或装 trait 对象。
---

# `Box`

> [!abstract] 一句话
> `Box<T>` 是「独占的堆分配」：栈上只留一个指针，值放在堆里，离开作用域自动释放，所有权唯一、不能共享。

## 简介

`Box<T>` 是最简单的智能指针：`Box::new(x)` 把 `x` 从栈搬到堆上，返回指向它的指针。它的所有权语义和普通值一样——只有一个主人，可以 move，离开作用域时自动 drop 并释放堆内存。解引用 `*b` 直接访问堆上的值，`&*b` 得到 `&T`，`&mut *b` 得到 `&mut T`；`Box<T>` 还能被 move 出内部值（`let v = *b;`），这一点是它和 `&T` 的关键区别。

三种情况必须用它。第一，**递归类型**：`enum List { Cons(i32, List) }` 会被判定为无限大小，编译不过；改成 `Cons(i32, Box<List>)` 就有了确定大小。第二，**大对象**：把几 KB 的结构体搬到堆上，避免每次 move 都整块拷贝，也避免栈溢出。第三，**trait 对象**：`Box<dyn Trait>` 是拥有所有权的动态分发形式，`Vec<Box<dyn Trait>>` 可以装不同类型的实现。

`Box<T>` 还有专门的「胖指针」形式：`Box<[T]>`（装箱切片）和 `Box<str>`（装箱字符串），它们只占两个机器字，适合把 `Vec<T>` / `String` 收缩成不可增长的最终形态（`into_boxed_slice`、`into_boxed_str`）。需要多个所有者时换成 [[rc.Rc|Rc]] 或 [[sync.Arc|Arc]]；需要内部可变性则套 [[cell.RefCell|RefCell]] 或 [[sync.Mutex|Mutex]]。

```rust
use std::any::Any;

fn main() {
    let boxed = Box::new(5);
    assert_eq!(*boxed, 5);

    // Box<dyn Any> 可以向下转型回具体类型
    let any: Box<dyn Any> = Box::new(String::from("你好"));
    match any.downcast::<String>() {
        Ok(s) => assert_eq!(*s, "你好"),
        Err(_) => unreachable!(),
    }

    // leak：故意不释放，换来一个 'static 引用
    let leaked: &'static mut i32 = Box::leak(Box::new(7));
    *leaked += 1;
    assert_eq!(*leaked, 8);

    println!("boxed = {}", boxed);
}
```

## 常用方法

### 构造

| 方法 | 说明 |
| --- | --- |
| `new(x)` | 在堆上分配内存并把 `x` 放进去。 |
| `new_uninit()` | 创建内容未初始化的 `Box<MaybeUninit<T>>`。 |
| `new_zeroed()` | 创建内容按零字节填充的 `Box<MaybeUninit<T>>`。 |
| `pin(x)` | 创建 `Pin<Box<T>>`，`T` 不可 `Unpin` 时被钉住。 |
| `new_uninit_slice(len)` | 创建长度为 `len` 的未初始化装箱切片。 |
| `new_zeroed_slice(len)` | 创建长度为 `len` 的零填充装箱切片。 |

### 初始化未初始化内存

| 方法 | 说明 |
| --- | --- |
| `assume_init(self)` | 转成 `Box<T>`，调用者保证已初始化。 |
| `assume_init(self)` | 转成 `Box<[T]>`，调用者保证已初始化。 |
| `write(boxed, value)` | 写入 `value` 并转成 `Box<T>`。 |

### 向下转型

| 方法 | 说明 |
| --- | --- |
| `downcast<T>(self)` | 转成具体类型 `T`，用于 `dyn Any` 装箱。 |
| `downcast<T>(self)` | 转成具体类型 `T`，用于 `dyn Any + Send`。 |
| `downcast<T>(self)` | 转成具体类型 `T`，用于 `Any + Send + Sync`。 |

### 裸指针与内存泄漏

| 方法 | 说明 |
| --- | --- |
| `into_raw(b)` | 消耗 `Box`，返回裸指针且不释放内存。 |
| `from_raw(raw)` | 从 `into_raw` 得到的裸指针重建 `Box`。 |
| `as_ptr(b)` | 返回指向 `Box` 内容的裸指针。 |
| `as_mut_ptr(b)` | 返回指向 `Box` 内容的可变裸指针。 |
| `into_non_null(b)` | 消耗 `Box`，返回 `NonNull` 指针。 |
| `from_non_null(ptr)` | 从 `NonNull` 指针重建 `Box`。 |
| `leak(b)` | 泄漏堆内存，返回生命周期不限的 `&mut T`。 |

### 转换为 Pin

| 方法 | 说明 |
| --- | --- |
| `into_pin(boxed)` | 转成 `Pin<Box<T>>`，值被钉住不可移动。 |

> [!warning] `into_raw` 与 `from_raw` 必须配对
> `into_raw` 之后堆内存不会自动释放，忘记用 `from_raw` 接回来就是内存泄漏；反过来对不是由 `Box::into_raw` 产生的指针调用 `from_raw` 是未定义行为。

## 示例

递归类型必须靠 `Box` 打断无限大小：

```rust
#[derive(Debug)]
enum List {
    Cons(i32, Box<List>),
    Nil,
}

fn main() {
    let list = List::Cons(1, Box::new(List::Cons(2, Box::new(List::Nil))));
    assert_eq!(format!("{:?}", list), "Cons(1, Cons(2, Nil))");

    // 递归函数里用 Box::new 构造节点
    fn len(list: &List) -> usize {
        match list {
            List::Cons(_, tail) => 1 + len(tail),
            List::Nil => 0,
        }
    }
    assert_eq!(len(&list), 2);

    // Box<dyn Trait> 装不同类型的实现，统一遍历
    trait Shape {
        fn area(&self) -> f64;
    }
    struct Square(f64);
    struct Circle(f64);
    impl Shape for Square {
        fn area(&self) -> f64 {
            self.0 * self.0
        }
    }
    impl Shape for Circle {
        fn area(&self) -> f64 {
            std::f64::consts::PI * self.0 * self.0
        }
    }

    let shapes: Vec<Box<dyn Shape>> = vec![Box::new(Square(2.0)), Box::new(Circle(1.0))];
    let total: f64 = shapes.iter().map(|s| s.area()).sum();
    assert!(total > 7.0 && total < 7.2);
    println!("总面积 = {:.3}", total);
}
```

## 常见陷阱

1. **把 `Box` 当共享指针**：它只有一个所有者，`clone` 需要 `T: Clone` 且会深拷贝整块数据；要共享用 [[rc.Rc|Rc]] / [[sync.Arc|Arc]]。
2. **递归类型忘了加 `Box`**：`enum List { Cons(i32, List) }` 会报「recursive type has infinite size」，用 `Box<List>` 打断。
3. **`Box::leak` 用在普通场景**：泄漏的内存直到进程退出都不回收，只在确实需要 `'static` 引用时使用。
4. **`Box<dyn Trait>` 上做热点调用**：动态分发无法内联，性能敏感处改用泛型参数。
5. **忘记 `from_raw`**：`into_raw` 后必须有人接回所有权，否则泄漏；这段代码是 `unsafe`，编译器不会提醒。

## 相关

- [[boxed|std::boxed 模块]]：本模块全部条目。
- [[rc.Rc|Rc]]：单线程共享所有权。
- [[sync.Arc|Arc]]：跨线程共享所有权。
- [[16-trait 对象与动态分发|trait 对象]]：`Box<dyn Trait>` 背后的机制。
- [[pin|std::pin]]：`Pin<Box<T>>` 与自引用类型、异步状态机。
