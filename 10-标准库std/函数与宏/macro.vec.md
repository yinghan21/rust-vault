---
title: "std::vec!"
type: std-条目
kind: 宏
module: std
slug: macro.vec
stable: "1.0.0"
tags:
  - std/宏
aliases:
  - "vec!"
  - "vec 宏"
一句话: "用类似数组字面量的语法构造 Vec，两种形式分别对应逐个列举与「值 + 个数」，返回 Vec<T>。"
---

# `vec!`

> [!abstract] 一句话
> `vec!` 用数组字面量那样的写法直接造一个 `Vec`：`vec![1, 2, 3]` 逐个列举元素，`vec![0u8; 3]` 把同一个值复制若干份。两种形式都返回堆上的 `Vec<T>`。

## 简介

`vec!` 是 `Vec::new()` 加一串 `push` 的语法糖。`Vec::new()` 需要可变的绑定、还要逐行 `push`，`vec!` 一行就把「容量 + 长度 + 元素」一次备好，是日常造 `Vec` 的首选写法。

它有两种形式。列表形式 `vec![a, b, c]` 等价于先把元素建成数组 `[a, b, c]` 再 `into_vec`，所以**不要求 `T: Clone`**，每个元素都可以是不同的表达式。重复形式 `vec![expr; n]` 由内部 `from_elem` 实现，要求 `T: Clone`：它把 `expr` 求值一次，再 `clone` 出 `n - 1` 份，`n` 可以是运行时变量，不必是常量——这一点比数组的 `[expr; N]`（`N` 必须是常量）宽松。

展开结果与返回值：列表形式先建一个栈上数组 `[$($x),*]`，再用 `<[_]>::into_vec` 把这块内存整体转成 `Vec`，所以元素是「搬进去」而不是「clone 进去」；重复形式展开为 `std::vec::from_elem($elem, $n)`。两者返回类型都是 `Vec<T>`，元素类型由元素表达式或显式标注推断。

因为重复形式走 `Clone`，对自定义 `Clone` 的类型要小心：`vec![Rc::new(1); 5]` 得到的是 5 个指向**同一份**数据的 `Rc` 克隆，而不是 5 个独立装箱的整数。

## 签名与参数

```text
vec![$elem:expr; $n:expr] -> Vec<T>     // 重复形式，要求 T: Clone
vec![$($x:expr),* $(,)?]  -> Vec<T>     // 列表形式，不要求 Clone
```

| 参数 | 说明 |
| --- | --- |
| `$x...` | 列表形式：逗号分隔的元素表达式，允许尾逗号，也可以是零个元素（`vec![]`，需标注类型）。 |
| `$elem` | 重复形式：被复制的值，只求值一次。 |
| `$n` | 重复次数，类型 `usize`，可以是变量或表达式。 |
| 返回 `Vec<T>` | 拥有全部元素所有权、元素连续存放在堆上的动态数组。 |

## 示例

### 两种形式

```rust
fn main() {
    let v = vec![1, 2, 3];
    assert_eq!(v[0], 1);
    assert_eq!(v[1], 2);
    assert_eq!(v.len(), 3);

    // 重复形式：n 可以是运行时变量，这是数组 [0u8; n] 做不到的
    let n = 3;
    let zeros = vec![0u8; n];
    assert_eq!(zeros, [0, 0, 0]);

    // 空 vec 与尾逗号
    let empty: Vec<i32> = vec![];
    assert!(empty.is_empty());
    let tail = vec!["a", "b",];
    assert_eq!(tail, ["a", "b"]);

    // 嵌套：外层是 Vec<Vec<i32>>
    let nested = vec![vec![1, 2], vec![3]];
    assert_eq!(nested[0][1], 2);

    println!("{nested:?}");
}
```

### 重复形式复制的是 `Clone` 结果

```rust
use std::rc::Rc;

fn main() {
    // 五个元素都是同一个 Rc 的克隆：强引用计数变成 5
    let shared = vec![Rc::new(1); 5];
    assert_eq!(Rc::strong_count(&shared[0]), 5);
    assert_eq!(*shared[4], 1);

    // 需要五个独立的值，就用列表形式或 map
    let independent: Vec<Rc<i32>> = (0..5).map(Rc::new).collect();
    assert_eq!(Rc::strong_count(&independent[0]), 1);

    println!("{:?}", shared.len() + independent.len());
}
```

## 常见陷阱

1. **重复形式用在非 `Clone` 类型上**：`vec![String::new(); 3]` 可以（`String: Clone`），但 `vec![Mutex::new(0); 3]` 编译失败，`Mutex` 不实现 `Clone`，改用列表形式或 `(0..3).map(..).collect()`。
2. **以为重复形式会跑 `n` 次构造**：`$elem` 只求值一次，其余都是 `clone`，像 `vec![rand_like(); 3]` 得到三个相同的值。
3. **`vec![Rc::new(1); 5]` 当成五个独立对象**：`Rc` 的 `Clone` 只加计数，要独立对象就逐个 `Rc::new`。
4. **`vec!()` 写成了 `()`**：宏必须有方括号/圆括号/花括号包裹，`vec!()` 合法但常被误写成函数调用形式后忘了元素类型，此时需要 `let v: Vec<i32> = vec![];` 标注。
5. **在循环里 `vec![0; n]` 再 `push`**：重复形式已经把长度定成 `n`，再 `push` 会变成 `2n` 长，需要预留空间应该用 `Vec::with_capacity(n)`。

## 相关

- [[vec.Vec|Vec]]：`vec!` 造出来的类型，`push`、`len`、`capacity` 等都在这里。
- [[vec|std::vec 模块]]：`Vec` 的迭代器与 `vec!` 的归属模块。
- [[primitive.array|Type array]]：定长数组，`vec!` 的语法就是从它借鉴来的。
- [[iter.Iterator|Iterator]]：`map` + `collect` 是构造非 `Clone` 元素的替代方案。
- [[12-集合类型|集合类型]]：`Vec`、`VecDeque`、`HashMap` 的选型对比。
