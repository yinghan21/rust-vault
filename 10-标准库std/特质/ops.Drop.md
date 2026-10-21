---
title: "std::ops::Drop"
type: std-条目
kind: 特质
module: ops
slug: ops.Drop
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - Drop
一句话: 自定义析构逻辑的唯一入口，值离开作用域时由编译器自动调用，与 Copy 互斥。
---

# Drop

> [!abstract] 一句话
> `Drop` 是析构函数的钩子：值被销毁前，编译器自动调用 `drop(&mut self)`，让你释放文件描述符、socket、锁、堆内存这类外部资源。

## 简介

Rust 没有手动 `free`，也没有析构规则分散在各处 —— 一切资源的释放都挂在 `Drop` 上。当值不再需要时（最常见的是离开作用域），编译器生成一个「析构」步骤：**先调用类型自己的 `Drop::drop`，再按字段声明顺序递归析构每个字段**。整个过程由编译器插入，无法忘记，也很难写错。

绝大多数类型**不需要**实现 `Drop`：`String`、`Vec<T>` 已经替你管理好了堆内存，你的结构体只要持有它们，字段自动析构就够了。真正需要 `Drop` 的场合是「直接管理一个外部资源」—— 手写的文件包装、数据库连接的归还、互斥锁的自动解锁、临时目录的清理、统计代码里的耗时打点。

编译器在以下情形自动触发析构：作用域结束、显式调用 `std::mem::drop(x)`、变量被新值覆盖（`*slot = new`）、`?` 提前返回、panic 展开栈。注意 `Drop::drop` 只能被编译器调用，**不能手写** `x.drop()`（E0040）。

`Drop` 与 [[marker.Copy|Copy]] 互斥，这是它最重要的类型级约束；它也解释了为什么「实现了 `Drop` 的类型不能把字段移出去」（E0509）—— 值一旦实现 `Drop`，编译器必须保证它在析构前始终完整，否则 `drop` 里访问到的是被搬空的字段。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `drop()` | 销毁前释放该值持有的资源。 |

签名是 `fn drop(&mut self)`。参数是 `&mut self` 而非 `self`：析构发生在原地，值的内存随后由编译器回收，你只负责「清理它引用的东西」。

## 与相邻 trait 的关系

| 关系 | 说明 |
| --- | --- |
| 与 `Copy` | **互斥**。`Copy` 会造出多份等价的值，`Drop` 要求唯一主人，同时实现报 E0184。 |
| 与 `Clone` | 可以共存。`clone` 造出的新值同样会在自己离开作用域时被析构，因此 `clone` 必须给出独立的资源（深拷贝），否则会双重释放。 |
| 与 `Default` | 无直接关系，但 `std::mem::take` 会用 `Default` 造一个占位值，让原值在被析构前先被移走。 |

要绕开「实现 `Drop` 就不能部分移动」的限制，标准库给了两条路：用 `Option<T>` 字段配合 `take()` 把值换出来；或用 `ManuallyDrop<T>` 声明「这块内容我自己负责，编译器不要自动析构」。

## 示例

### 析构顺序

```rust
struct Noisy(&'static str);

impl Drop for Noisy {
    fn drop(&mut self) {
        println!("销毁 {}", self.0);
    }
}

struct Pair {
    first: Noisy,
    second: Noisy,
}

impl Drop for Pair {
    fn drop(&mut self) {
        println!("销毁 Pair 本身");
    }
}

fn main() {
    let _p = Pair {
        first: Noisy("first"),
        second: Noisy("second"),
    };
    println!("main 结束前");
    // 输出顺序：main 结束前 → 销毁 Pair 本身 → 销毁 first → 销毁 second
}
```

### 用 `Drop` 做资源守卫

```rust
use std::cell::Cell;

// 作用域结束时自动置位，相当于一个「退出即执行」的钩子
struct Guard<'a> {
    fired: &'a Cell<bool>,
}

impl Drop for Guard<'_> {
    fn drop(&mut self) {
        self.fired.set(true);
    }
}

fn main() {
    let fired = Cell::new(false);

    {
        let _guard = Guard { fired: &fired };
        assert!(!fired.get());
    }

    // 离开内层作用域，守卫已析构
    assert!(fired.get());
}
```

### 提前返回与显式析构

```rust
struct Noisy(&'static str);

impl Drop for Noisy {
    fn drop(&mut self) {
        println!("清理 {}", self.0);
    }
}

fn run(fail: bool) -> Result<(), &'static str> {
    let _guard = Noisy("guard");
    if fail {
        // 提前返回也会正常析构 _guard
        return Err("失败了");
    }
    Ok(())
}

fn main() {
    assert!(run(true).is_err());

    let a = Noisy("a");
    // 用 mem::drop 提前结束生命周期，而不是手写 a.drop()
    drop(a);
    println!("a 已清理");

    // 这个值在 main 结束时才析构
    let _end = Noisy("end");
}
```

## 常见陷阱

1. **手写 `x.drop()`**：E0040（`explicit destructor calls not allowed`）；要提前析构就 `drop(x)` 交给 [[mem.drop|drop]] 函数。
2. **给实现了 `Drop` 的类型做部分移动**：`let f = self.field;` 报 E0509；对策是把字段包成 `Option<T>` 再用 `take()`，或用 `ManuallyDrop`。
3. **`Drop` 与 `Copy` 同时实现**：E0184 直接拒绝；二者语义冲突，只能选一个。
4. **在 `drop` 里 panic**：panic 展开期间再次 panic 会直接 abort 进程；清理逻辑里要么吞掉错误，要么显式记录。
5. **以为 `Drop` 一定会运行**：`std::process::exit`、`std::mem::forget`、`Rc`/`Arc` 的引用环都会让析构被跳过，资源泄漏而不是 UB。
6. **把 `drop` 当成 `Drop` 的方法名**：`Drop::drop` 是 trait 方法，`std::mem::drop` 是普通函数，二者同名不同物。

## 相关

- [[ops|std::ops 模块]]：`Drop` 所属模块，运算符重载特质都在这里。
- [[mem.drop|drop]]：把值提前析构的普通函数，替代手动调用 `Drop::drop`。
- [[marker.Copy|Copy]]：与 `Drop` 互斥的标记特质。
- [[clone.Clone|Clone]]：造出多个所有者时必须保证资源独立。
- [[boxed.Box|Box]]：最常见的「堆分配 + 自动析构」组合。
- [[20-智能指针|智能指针]]：`Drop` 型 API 的设计讲法。
