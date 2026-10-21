---
title: "std::cell::RefCell"
type: std-条目
kind: 结构体
module: cell
slug: cell.RefCell
stable: "1.0.0"
tags:
  - std/类型
aliases:
  - RefCell
一句话: 把借用规则从编译期推迟到运行期的容器，违规借用会 panic，用 try_borrow 系列可以拿到 Err。
---

# `RefCell`

> [!abstract] 一句话
> `RefCell<T>` 允许在只有 `&self` 的情况下拿到 `&mut T`，借用规则不变但检查搬到运行时：同时存在可变借用和任何其他借用就 **panic**。

## 简介

`RefCell` 是「动态检查借用规则的可变内存位置」。它和 [[cell.Cell|Cell]] 都提供内部可变性，区别在于 `RefCell` **真的出借引用**：`borrow()` 给你 `Ref<T>`，`borrow_mut()` 给你 `RefMut<T>`，两者都实现 `Deref`，用起来和 `&T` / `&mut T` 几乎一样。代价是它内部维护一个借用计数器，运行期判断「现在有没有冲突」。

规则与编译期完全一致：任意时刻要么多个不可变借用，要么一个可变借用。区别只在违规后果——编译期是编译错误，运行期是 **panic**（错误信息形如 `already borrowed: BorrowMutError` 或 `already mutably borrowed: BorrowError`）。不想 panic 就用 `try_borrow` / `try_borrow_mut`，它们返回 `Result<_, BorrowError>` / `Result<_, BorrowMutError>`。

它的经典搭档是 [[rc.Rc|Rc]]：`Rc<RefCell<T>>` 让多个所有者共享一份可改数据，这是单线程下实现图、双向链表、观察者模式的常用套路。注意 `RefCell` 不是 `Sync`，不能跨线程共享，多线程版本是 [[sync.RwLock|RwLock]] 或 [[sync.Mutex|Mutex]]。另外借用守卫 `Ref` / `RefMut` 只要还活着，单元格就处于「已借用」状态，忘记 drop（比如用 `std::mem::forget`）会让它永久被借出。

```rust
use std::cell::RefCell;

fn main() {
    let cell = RefCell::new(10);
    assert_eq!(*cell.borrow(), 10);

    *cell.borrow_mut() += 5;
    assert_eq!(cell.replace(100), 15);
    assert_eq!(cell.replace_with(|v| *v + 1), 100);
    assert_eq!(cell.take(), 101);
    assert_eq!(*cell.borrow(), 0);
    println!("完成");
}
```

## 常用方法

### 构造与取出

| 方法 | 说明 |
| --- | --- |
| `new(value)` | 创建包含 `value` 的 `RefCell`。 |
| `into_inner(self)` | 消耗 `RefCell`，返回被包裹的值。 |
| `take()` | 取走内部值，原地留下 `Default::default()`。 |

### 替换与交换

| 方法 | 说明 |
| --- | --- |
| `replace(t)` | 用新值替换并返回旧值，不析构任何一个。 |
| `replace_with(f)` | 用 `f` 算出的新值替换，返回旧值。 |
| `swap(other)` | 交换两个 `RefCell` 的内部值。 |

### 借用

| 方法 | 说明 |
| --- | --- |
| `borrow()` | 不可变借用，已被可变借用时 panic。 |
| `borrow_mut()` | 可变借用，已有任何借用时 panic。 |
| `try_borrow()` | 不可变借用的可失败版本，冲突返回 `Err`。 |
| `try_borrow_mut()` | 可变借用的可失败版本，冲突返回 `Err`。 |

### 独占访问与裸指针

| 方法 | 说明 |
| --- | --- |
| `get_mut(&mut self)` | 独占引用下直接返回 `&mut T`，不做检查。 |
| `try_borrow_unguarded()` | `unsafe` 版本，返回 `&T` 且不登记借用。 |
| `as_ptr()` | 返回指向内部数据的裸指针。 |

> [!danger] `try_borrow_unguarded` 会绕过安全网
> 它返回的 `&T` 不会被借用计数器记录，调用者必须自己保证在整个生命周期内没有可变借用存在，否则就是未定义行为。

## 示例

```rust
use std::cell::RefCell;

fn main() {
    let cell = RefCell::new(vec![1, 2, 3]);

    // 正常借用：守卫离开作用域后立即归还
    {
        let mut guard = cell.borrow_mut();
        guard.push(4);
    }
    assert_eq!(cell.borrow().len(), 4);

    // 违规借用会 panic，这里用 catch_unwind 把它抓出来演示
    let mut guard = cell.borrow_mut();
    let caught = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        let _ = cell.borrow(); // 运行时 panic：already mutably borrowed
    }));
    assert!(caught.is_err());
    drop(guard);

    // 不想 panic 就用 try_borrow 系列
    let mut guard = cell.borrow_mut();
    assert!(cell.try_borrow().is_err());
    assert!(cell.try_borrow_mut().is_err());
    drop(guard);
    assert!(cell.try_borrow().is_ok());

    // 独占引用下 get_mut 直接给 &mut T
    let mut owned = RefCell::new(String::from("a"));
    owned.get_mut().push('b');
    assert_eq!(owned.into_inner(), "ab");

    println!("最终内容 = {:?}", cell.borrow());
}
```

## 常见陷阱

1. **守卫还没 drop 就再借**：`let g = c.borrow_mut();` 之后任何 `borrow()` / `borrow_mut()` 都会 panic，用花括号把守卫作用域收紧。
2. **把 `borrow()` 写在长表达式里**：临时守卫的生命周期可能延续到语句结束，`*c.borrow_mut() + *c.borrow()` 这类写法会 panic；先取值到变量。
3. **用 `RefCell` 替代编译期借用**：它把错误从编译期推到运行期，只在确实需要内部可变性（如 `Rc<RefCell<T>>`）时才用。
4. **跨线程共享 `RefCell`**：它不是 `Sync`，编译不过；多线程用 [[sync.Mutex|Mutex]] / [[sync.RwLock|RwLock]]。
5. **泄漏借用守卫**：`std::mem::forget(c.borrow_mut())` 会让单元格永久处于可变借用状态，之后所有借用都失败。

## 相关

- [[cell|std::cell 模块]]：本模块全部条目。
- [[cell.Cell|Cell]]：无运行时检查、只能整体读写的更轻版本。
- [[rc.Rc|Rc]]：`Rc<RefCell<T>>` 是单线程共享可变状态的经典组合。
- [[sync.RwLock|RwLock]]：多线程版的「读共享、写独占」。
- [[06-借用与引用|借用]]：`RefCell` 在运行时模拟的那套规则。
