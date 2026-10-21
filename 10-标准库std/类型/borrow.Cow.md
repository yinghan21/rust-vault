---
title: "std::borrow::Cow"
type: std-条目
kind: 枚举
module: borrow
slug: borrow.Cow
stable: "1.0.0"
tags:
  - std/类型
aliases:
  - Cow
一句话: 写时克隆（clone-on-write）智能指针，能借就借、必须改才克隆。
---

# `Cow<'a, B>`

> [!abstract] 一句话
> `Cow` 是**写时克隆**的智能指针：它要么借用别人的数据（`Cow::Borrowed`），要么自己持有一份（`Cow::Owned`）；只有在你真正需要修改时才把借用的数据克隆成自有数据。

## 简介

`Cow<'a, B>`（Clone-on-Write）解决的是「函数既想接受借用，又偶尔需要自己造数据」的问题。参数写 `&str` 时调用方必须提供生命周期足够长的借用；参数写 `String` 时调用方必须交出所有权。用 `Cow<'a, str>` 就能两者通吃：能借就借（零分配、零克隆），确实需要改动时才 `to_mut` 克隆一份。

名字里的 `B` 是被包裹的「借用形态」类型，由 `Borrow` 与 `ToOwned` 两个 trait 联系起来：`B: ToOwned`，`Borrowed(&'a B)` 里是借用，`Owned(B::Owned)` 里是对应的拥有型。常见组合是 `Cow<'a, str>`（`&str` ↔ `String`）、`Cow<'a, [T]>`（`&[T]` ↔ `Vec<T>`）以及 `Cow<'a, Path>`（`&Path` ↔ `PathBuf`）。

`Cow` 实现了 `Deref`，所以 `.len()`、`.split()` 等只读方法可以直接调用，像用 `&B` 一样用它；`ToOwned`、`Clone`、`PartialEq`、`Hash`、`Debug` 等也都有实现，在容器里当键或做比较都没问题。它**不是**引用计数指针：需要共享所有权时用 [[rc.Rc|Rc]] 或 [[sync.Arc|Arc]]，它们的 `make_mut` 也提供写时克隆语义。

## 变体

| 变体 | 含义 |
| --- | --- |
| `Borrowed(&'a B)` | 借用了外部数据，不拥有、不释放；只用 `&self` 的方法直接读它。 |
| `Owned(<B as ToOwned>::Owned)` | 自己持有数据（如 `String`）；`to_mut` 时不需要再克隆。 |

变体可以直接匹配，用来判断当前是借用还是自有；`Cow` 没有提供稳定的 `is_borrowed()` 查询方法（相关方法尚未稳定）。

## 常用方法

| 方法 | 说明 |
| --- | --- |
| `to_mut()` | 取得自有数据的可变引用，必要时先克隆。 |
| `into_owned()` | 取出自有数据，借用时克隆一份。 |

> [!tip] 签名
> `pub fn to_mut(&mut self) -> &mut <B as ToOwned>::Owned`
> `pub fn into_owned(self) -> <B as ToOwned>::Owned`

## 示例

```rust
use std::borrow::Cow;

// 输入本来合法就不克隆，需要修补时才克隆
fn shout(input: Cow<'_, str>) -> Cow<'_, str> {
    if input.contains('!') {
        input
    } else {
        let mut owned = input.into_owned();
        owned.push('!');
        Cow::Owned(owned)
    }
}

fn main() {
    // 已经带感叹号：全程借用，没有分配
    let borrowed = shout(Cow::Borrowed("hi!"));
    assert!(matches!(borrowed, Cow::Borrowed(_)));
    assert_eq!(&*borrowed, "hi!");

    // 没有感叹号：into_owned 克隆后追加
    let owned = shout(Cow::Borrowed("hi"));
    assert!(matches!(owned, Cow::Owned(_)));
    assert_eq!(&*owned, "hi!");
}
```

下面演示 `to_mut`：前几次调用只读，第一次写时才发生克隆。

```rust
use std::borrow::Cow;

fn abs_all(input: &mut Cow<'_, [i32]>) {
    for i in 0..input.len() {
        if input[i] < 0 {
            // 第一次进这里才会把借用克隆成 Vec
            input.to_mut()[i] = -input[i];
        }
    }
}

fn main() {
    let slice = [0, 1, 2];
    let mut cow = Cow::from(&slice[..]);
    abs_all(&mut cow); // 无需修改，仍是 Borrowed
    assert!(matches!(cow, Cow::Borrowed(_)));
    assert_eq!(&*cow, [0, 1, 2]);

    let slice = [-1, 0, 1];
    let mut cow = Cow::from(&slice[..]);
    abs_all(&mut cow); // 触发克隆
    assert!(matches!(cow, Cow::Owned(_)));
    assert_eq!(&*cow, [1, 0, 1]);
}
```

## 常见陷阱

1. **以为 `Cow` 一定不分配**：`Borrowed` 分支不分配，但 `to_mut` / `into_owned` 在借用态下会克隆；写在热路径前先确认分支。
2. **`to_mut` 之后还留着旧的不可变引用**：`to_mut` 需要 `&mut self`，会与仍存活的借用冲突，借用应在调用前结束。
3. **把 `Cow` 当 `Rc` 用**：`Cow::clone` 是深拷贝（借用时复制），不共享同一份数据；要共享请用 `Rc` / `Arc`。
4. **类型标注漏掉生命周期**：`Cow<'_, str>` 中的 `'a` 必须能覆盖借用来源，返回 `Cow<'_, str>` 的函数里别凭空造出比输入更长的借用。
5. **在公开 API 里到处用 `Cow`**：它会让签名变复杂，只在「多数调用不需要分配」时使用，内部实现通常直接用 `String`。

## 相关

- [[borrow|std::borrow 模块]]：`Cow`、`Borrow`、`ToOwned` 都在这里。
- [[borrow.Borrow|Borrow]]：让 `Cow` 能统一处理 `&str` 与 `String` 的关键 trait。
- [[string.String|String]]：`Cow<'a, str>` 的拥有型。
- [[rc.Rc|Rc]] / [[sync.Arc|Arc]]：`make_mut` 也能实现写时克隆，但用于共享所有权。
