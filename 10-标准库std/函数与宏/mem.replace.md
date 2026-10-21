---
title: "std::mem::replace"
type: std-条目
kind: 函数
module: mem
slug: mem.replace
stable: "1.0.0"
tags:
  - std/类型
aliases:
  - "replace"
  - "mem::replace"
一句话: "把 src 放进 dest 指向的位置，返回原来的值；两个值都不会被析构，也不需要 Clone 或 Default。"
---

# `replace`

> [!abstract] 一句话
> `std::mem::replace(&mut dest, src)` 把 `src` 搬进 `dest` 的位置，同时把原来待在那儿的旧值返回给调用方。两个值都不会被 drop，`T` 不需要 `Clone`，也不需要 `Default`。

## 简介

Rust 不允许把一个值从 `&mut` 后面「偷走」再填回去——中间那一刻位置是未初始化的，编译器必须拦住。`mem::replace` 把「取旧 + 放新」合成一步完成：旧值从位置里移到返回值，新值从参数移进位置，全程没有空洞，所以是安全函数。

它比 [[mem.take|take]] 灵活的地方在于：新值由你提供，不必是 `T::default()`。状态机里「从 `Running` 切到 `Done` 并交出 `Running`」、替换数组某个元素并拿回旧的、把 `Option` 里的值换出来再塞 `None`，都是它的典型场景。

函数与返回值：`pub fn replace<T>(dest: &mut T, src: T) -> T`。第一个参数是目标位置的可变引用，第二个参数是要放进去的新值（按值传入，所有权随之转移），返回**原来的 `dest` 值**。注意 `dest` 和 `src` 是同一类型 `T`，不能拿一个 `String` 去替换 `i32`。

`replace` 不会 drop `src`，也不会 drop 旧值，两者的析构都交由调用方安排；如果想直接丢弃新值并取走旧值，那是 `replace(dest, T::default())`，也就是 [[mem.take|take]]。

## 签名与参数

```text
pub fn replace<T>(dest: &mut T, src: T) -> T
```

| 参数 | 说明 |
| --- | --- |
| `dest` | 目标位置的可变引用，函数返回后里面是 `src`。 |
| `src` | 要放进 `dest` 的新值，按值传入；与位置上的类型必须一致。 |
| 返回 `T` | 被换下来的旧值，所有权归调用方。 |

- `T` 无任何特质约束，不要求 `Clone`、`Default`、`Copy`。
- 不 panic、不分配；只有对同一位置同时取两次 `&mut` 才会在编译期被拒。
- 与 `slice::replace` 无关，那个是替换一段切片内容的方法。

## 示例

### 换掉集合与枚举状态

```rust
use std::mem;

#[derive(Debug, PartialEq)]
enum State {
    Idle,
    Running,
    Done,
}

fn main() {
    let mut v: Vec<i32> = vec![1, 2];
    let old = mem::replace(&mut v, vec![3, 4, 5]);
    assert_eq!(old, vec![1, 2]);
    assert_eq!(v, vec![3, 4, 5]);

    // 状态机：切到终态，同时把上一个状态取出来
    let mut st = State::Running;
    let prev = mem::replace(&mut st, State::Done);
    assert_eq!(prev, State::Running);
    assert_eq!(st, State::Done);

    // 已经结束就不重复切换
    assert_eq!(mem::replace(&mut st, State::Idle), State::Done);
    assert_eq!(st, State::Idle);

    println!("{st:?} {v:?}");
}
```

### 替换数组里的单个元素

```rust
use std::mem;

fn main() {
    let mut arr = [1, 2, 3];

    // 取出 arr[1] 并放入 20，旧值 2 被返回
    let taken = mem::replace(&mut arr[1], 20);
    assert_eq!(taken, 2);
    assert_eq!(arr, [1, 20, 3]);

    // Option 里取走值、换成 None：等价于 opt.take()
    let mut opt = Some(String::from("hi"));
    let inner = mem::replace(&mut opt, None);
    assert_eq!(inner, Some(String::from("hi")));
    assert_eq!(opt, None);

    println!("{arr:?} {inner:?} {opt:?}");
}
```

## 常见陷阱

1. **类型不匹配**：`mem::replace(&mut n, "text")` 里 `n` 是整数，编译器直接报类型错误，替换值必须与被替换位置同类型。
2. **换成 `Default` 却手写一遍**：`mem::replace(&mut x, T::default())` 就是 [[mem.take|take]]，直接调 `mem::take` 更清楚。
3. **对同一个 Vec 的两个下标取 `&mut`**：`mem::replace(&mut v[0], v[1])` 会同时需要可变与不可变借用而失败，先 `let t = v[1];`（`Copy` 类型）再替换。
4. **以为旧值会被顺手丢掉**：旧值在返回值里，直接写 `mem::replace(&mut x, y);` 会让它在语句结束时被 drop，想要就绑定。
5. **用 `replace` 做元素插入/删除**：它会保留长度与顺序，只是换内容；要增删改用 `Vec::insert` / `Vec::remove`。

## 相关

- [[mem|std::mem 模块]]：`replace` 与 `swap`、`take`、`drop` 同属内存操作工具。
- [[mem.take|take]]：`replace(dest, T::default())` 的专用版本，要求 `T: Default`。
- [[mem.swap|swap]]：两个位置互换，不牵涉新值。
- [[mem.drop|drop]]：显式丢弃一个值，常与 `replace` 配合处理旧值。
- [[option.Option|Option]]：`opt.replace(new)` 方法也是同一语义，返回旧值。
