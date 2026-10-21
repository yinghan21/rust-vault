---
title: "std::option::Option"
type: std-条目
kind: 枚举
module: option
slug: option.Option
stable: "1.0.0"
tags:
  - std/类型
  - rust/基础
aliases:
  - Option
一句话: 表示「可能没有值」的枚举，用 Some(T) 或 None 替代 null，是 Rust 处理可缺失数据的主力类型。
---

# `Option<T>`

> [!abstract] 一句话
> `Option<T>` 只有两个变体：`Some(T)` 表示有值，`None` 表示没有值。把「缺失」写进类型里，编译器就能逼你在取值前处理 `None`。

## 简介

`Option<T>` 是 Rust 用来表达「可能缺失」的方式，其它语言里对应 `null`、`undefined` 或返回 `-1` 这类哨兵值。区别在于：`None` 是一个**独立的枚举变体**，而不是某个特殊值，所以任何 `T`（包括整数、指针）都能加一层 `Option` 而不会和合法值混淆；想拿到里面的 `T`，必须先显式处理 `None`。

它和相邻概念的区别：

- [[result.Result|Result]]：`Result<T, E>` 表示「成功或失败，且失败带原因」，`Option` 只说「有没有」，不解释为什么没有。需要错误信息时用 `Result`。
- `Option<T>` 与 `T` 的代价：因为空指针优化，`Option<&T>`、`Option<Box<T>>`、`Option<NonZeroU32>` 等类型和裸值**一样大**；其它情况会多一个标签字节（还要算对齐）。
- 泛型位置的约束：`Option<&T>` 支持 `Copy`，`Option<T>` 是否 `Copy`/`Clone` 取决于 `T`。

`Option` 用得极广：`Vec::pop`、`HashMap::get`、`Iterator::next`、`str::parse` 的可失败版本、`slice::first` 等都返回它。同时 `Option<T>` 实现了 `IntoIterator`，所以 `for x in option` 会走 0 次或 1 次。

## 变体

| 变体 | 含义 |
| --- | --- |
| `Some(T)` | 存在一个类型为 `T` 的值。 |
| `None` | 没有值，通常表示缺失、未初始化或查找失败。 |

## 常用方法

共 48 个稳定方法，按用途分成 9 组。

### 判断

| 方法 | 说明 |
| --- | --- |
| `is_some()` | 判断是否为 `Some`。 |
| `is_some_and()` | 判断是 `Some` 且值满足谓词。 |
| `is_none()` | 判断是否为 `None`。 |
| `is_none_or()` | 判断是 `None` 或值满足谓词。 |

### 借用与视图

| 方法 | 说明 |
| --- | --- |
| `as_ref()` | 从 `&Option<T>` 得到 `Option<&T>`。 |
| `as_mut()` | 从 `&mut Option<T>` 得到 `Option<&mut T>`。 |
| `as_pin_ref()` | 取钉住 `Option` 内部的钉住引用。 |
| `as_pin_mut()` | 取钉住 `Option` 内部的可变钉住引用。 |
| `as_slice()` | 有值时返回单元素切片，否则空切片。 |
| `as_mut_slice()` | 有值时返回可变单元素切片，否则空切片。 |

### 取值

| 方法 | 说明 |
| --- | --- |
| `expect()` | 取出值，为 `None` 时带信息 panic。 |
| `unwrap()` | 取出值，为 `None` 时 panic。 |
| `unwrap_or()` | 取出值，为 `None` 时返回默认值。 |
| `unwrap_or_else()` | 取出值，为 `None` 时调用闭包求值。 |
| `unwrap_or_default()` | 取出值，为 `None` 时返回类型的默认值。 |
| `unwrap_unchecked()` | 不检查直接取值，`None` 即 UB（unsafe）。 |

### 映射与错误转换

| 方法 | 说明 |
| --- | --- |
| `map()` | 对 `Some` 里的值应用函数，其余透传 `None`。 |
| `inspect()` | 有值时用引用调用闭包，原样返回自身。 |
| `map_or()` | 有值则映射，否则返回给定默认值。 |
| `map_or_else()` | 有值则映射，否则调用默认闭包。 |
| `map_or_default()` | 有值则映射，否则返回 `U::default()`。 |
| `as_deref()` | 经 `Deref` 得到 `Option<&T::Target>`。 |
| `as_deref_mut()` | 经 `DerefMut` 得到内部的可变引用。 |
| `ok_or()` | 转换为 `Result`，`None` 变成给定错误。 |
| `ok_or_else()` | 转换为 `Result`，错误由闭包生成。 |

### 迭代

| 方法 | 说明 |
| --- | --- |
| `iter()` | 迭代 0 或 1 个值的不可变迭代器。 |
| `iter_mut()` | 迭代 0 或 1 个值的可变迭代器。 |

### 组合

| 方法 | 说明 |
| --- | --- |
| `and()` | 有值时返回另一个 `Option`，否则 `None`。 |
| `and_then()` | 有值时调用返回 `Option` 的闭包。 |
| `filter()` | 值不满足谓词时转成 `None`。 |
| `or()` | 有值返回自身，否则返回另一个 `Option`。 |
| `or_else()` | 有值返回自身，否则调用闭包求值。 |
| `xor()` | 恰好一个为 `Some` 时返回值。 |

### 就地修改

| 方法 | 说明 |
| --- | --- |
| `insert()` | 写入值并返回其可变引用。 |
| `get_or_insert()` | 为空时写入给定值，返回可变引用。 |
| `get_or_insert_default()` | 为空时写入默认值，返回可变引用。 |
| `get_or_insert_with()` | 为空时用闭包生成值，返回可变引用。 |
| `take()` | 取出值，原位留下 `None`。 |
| `take_if()` | 谓词为真时才取出值。 |
| `replace()` | 换入新值，返回旧值。 |

### 元组与嵌套

| 方法 | 说明 |
| --- | --- |
| `zip()` | 两个都有值时合成元组 `Option`。 |
| `unzip()` | 把元组 `Option` 拆成两个 `Option`。 |
| `transpose()` | `Option<Result>` 与 `Result<Option>` 互转。 |
| `flatten()` | 把 `Option<Option<T>>` 压平成 `Option<T>`。 |

### 引用转值

| 方法 | 说明 |
| --- | --- |
| `copied()` | 把 `Option<&T>` 复制成 `Option<T>`。 |
| `cloned()` | 把 `Option<&T>` 克隆成 `Option<T>`。 |
| `copied()`（可变引用版） | 把 `Option<&mut T>` 复制成 `Option<T>`。 |
| `cloned()`（可变引用版） | 把 `Option<&mut T>` 克隆成 `Option<T>`。 |

## 示例

### 映射、取值与链式组合

```rust
fn main() {
    let some: Option<i32> = Some(3);
    let none: Option<i32> = None;

    assert_eq!(some.map(|v| v * 2), Some(6));
    assert_eq!(none.map(|v| v * 2), None);

    assert_eq!(none.unwrap_or(0), 0);
    assert_eq!(none.unwrap_or_else(|| 7), 7);

    assert!(some.is_some_and(|v| v > 2));
    assert!(none.is_none_or(|v| v > 2));

    // and_then 用来串联「可能失败」的步骤
    let odd_double = |v: i32| if v % 2 == 1 { Some(v * 10) } else { None };
    assert_eq!(some.and_then(odd_double), Some(30));
    assert_eq!(Some(4).and_then(odd_double), None);

    // None 时给出兜底值，短路语义与 and 相反
    assert_eq!(none.or(Some(9)), Some(9));
    assert_eq!(some.or(Some(9)), Some(3));
}
```

### 就地修改与 `take`

```rust
fn main() {
    let mut slot: Option<String> = None;

    // 为空时用闭包生成，并拿到可变引用
    let s = slot.get_or_insert_with(|| String::from("abc"));
    s.push('d');
    assert_eq!(slot.as_deref(), Some("abcd"));

    // replace 换入新值并返回旧值
    let old = slot.replace(String::from("xyz"));
    assert_eq!(old.as_deref(), Some("abcd"));

    // take 清空槽位，常见于状态机与选项字段
    let taken = slot.take();
    assert_eq!(taken, Some(String::from("xyz")));
    assert_eq!(slot, None);

    // transpose 把「可能失败的解析」整理成 Result<Option<_>>
    let parsed: Option<Result<i32, _>> = Some("12".parse::<i32>());
    assert_eq!(parsed.transpose(), Ok(Some(12)));
}
```

## 常见陷阱

1. **`unwrap()` 到处写**：`None` 时会 panic，等于把错误推迟到运行时；生产代码改用 `unwrap_or`、`ok_or` + `?` 或 `match`。
2. **`unwrap_or` 参数会被立即求值**：`unwrap_or(expensive())` 无论有没有值都会先算一遍；想惰性求值用 `unwrap_or_else`。
3. **`and` 与 `or` 容易搞反**：`and` 是「两边都要有」，`or` 是「第一个有就用」，和布尔运算的直觉一致，但返回值是 `Option` 而不是 `bool`。
4. **`unwrap_unchecked()` 不做检查**：对 `None` 调用是未定义行为，只能在已经证明非 `None` 的热路径上用，且必须写 `unsafe`。
5. **`take()` 之后忘记处理旧值**：`take` 会把 `Option` 清空，若在循环里反复 `take` 却没写回去，字段会一直是 `None`。

## 相关

- [[option|std::option 模块]]：`Iter`、`IntoIter` 等配套类型都在这里。
- [[result.Result|Result]]：需要携带错误原因时用它代替 `Option`。
- [[cmp.Ordering|Ordering]]：`Option` 与它常一起出现在排序比较里。
- [[08-枚举与模式匹配|模式匹配]]：`match` / `if let` 是处理 `Option` 最直接的方式。
- [[11-错误处理|错误处理]]：`ok_or` + `?` 是 `Option` 转错误的常用套路。
