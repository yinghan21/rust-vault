---
title: "std::matches!"
type: std-条目
kind: 宏
module: std
slug: macro.matches
stable: "1.42.0"
tags:
  - std/宏
aliases:
  - "matches!"
  - "matches 宏"
一句话: "判断表达式是否匹配某个模式，返回 bool；展开成只有 true/false 两个分支的 match，可带 if 守卫。"
---

# `matches!`

> [!abstract] 一句话
> `matches!(值, 模式)` 返回一个 `bool`：匹配就是 `true`，不匹配就是 `false`。它展开成一个只有两个分支的 `match`，模式语法与 `match` 分支完全一致，还能在后面加 `if` 守卫。

## 简介

只想问「是不是这个形状」而完全不关心绑定的字段时，写完整的 `match` 很啰嗦：

```text
match value { Some(x) if x > 2 => true, _ => false }
```

`matches!` 把这七行压成一行，还省掉「漏写 `_` 分支」的可能。它的模式语法就是 `match` 里的模式：字面量、范围、`|` 或模式、`Some(x)`、`Enum { field, .. }`、`&` 引用、`..` 忽略剩余字段，全都能用。

展开结果与返回值：`matches!($expression, $pattern)` 展开为

```text
match $expression { $pattern => true, _ => false }
```

带守卫时是 `$pattern if $guard => true`。所以它的返回值类型是 `bool`，永远不会 panic；守卫里如果写错类型才会编译失败。**注意 `$expression` 会被 move 进这个 `match`**：对非 `Copy` 类型，`matches!(v, ...)` 之后 `v` 就被消耗掉了，想保留所有权就传引用 `matches!(&v, ...)` 并在模式里用 `&`。

和 `assert_matches!` 的关系：测试里想知道失败时值长什么样，标准库 nightly 的 `assert_matches!` 更好用（失败时打印 `Debug`）；稳定版可以自己写 `assert!(matches!(..), "{v:?}")` 达到类似效果。

## 签名与参数

```text
matches!($expression:expr, $pattern:pat $(if $guard:expr)? $(,)?) -> bool
```

| 参数 | 说明 |
| --- | --- |
| `$expression` | 被检查的值，按值传入并交给内部 `match`（非 `Copy` 类型会被移动）。 |
| `$pattern` | 与 `match` 分支相同的模式，可用 `|`、范围、`..`、`ref` 等。 |
| `if $guard` | 可选的守卫表达式，必须求值为 `bool`；守卫为假时整个宏返回 `false`。 |
| 返回 `bool` | 匹配为 `true`，否则 `false`，不会 panic，也不返回 `Result`。 |

## 示例

### 基本判断

```rust
fn main() {
    let foo = 'f';
    assert!(matches!(foo, 'A'..='Z' | 'a'..='z'));

    let bar = Some(4);
    assert!(matches!(bar, Some(x) if x > 2));
    assert!(!matches!(bar, None));

    // 守卫为假只是返回 false，不会 panic
    assert!(!matches!(bar, Some(x) if x > 10));

    // 忽略剩余字段，只判断变体
    assert!(matches!(bar, Some(_)));
    println!("{bar:?}");
}
```

### 用在枚举与借用上

```rust
#[derive(Debug, Clone)]
enum Message {
    Quit,
    Move { x: i32, y: i32 },
    Write(String),
}

fn main() {
    let msgs = vec![
        Message::Quit,
        Message::Move { x: 1, y: 2 },
        Message::Write(String::from("hi")),
    ];

    let quit_count = msgs.iter().filter(|m| matches!(m, Message::Quit)).count();
    assert_eq!(quit_count, 1);

    // 传引用，避免把 String 字段 move 出去
    let has_write = msgs
        .iter()
        .any(|m| matches!(m, Message::Write(s) if s.len() == 2));
    assert!(has_write);

    // 借用也可以配 if let 使用，效果与 matches! 类似，但只关心一个分支
    if let Message::Move { x, y } = msgs[1] {
        assert_eq!(x + y, 3);
    }

    println!("{msgs:?}");
}
```

## 常见陷阱

1. **忘了它会移动值**：`matches!(owned_string_option, Some(_))` 之后 `owned_string_option` 不能再用；改成 `matches!(&opt, Some(_))`。
2. **引用模式的层级对不上**：`matches!(&opt, Some(_))` 能匹配，因为模式匹配会自动穿透一层 `&`；但 `matches!(opt, &Some(_))` 里 `opt` 是 `Option<T>` 不是引用，编译失败，模式要与值的类型对齐。
3. **以为守卫能替代 `match`**：守卫里不能借用被移动的字段，复杂条件还是写 `match` 更清楚。
4. **在断言里丢掉上下文**：`assert!(matches!(x, Foo::Bar))` 失败时看不到 `x` 的内容，加消息 `assert!(matches!(x, Foo::Bar), "实际是 {x:?}")`。
5. **用 `matches!` 接 `Result` 的 `Ok` 却想取值**：它只给 `bool`，要值就用 `if let Ok(v) = r` 或 `r.ok()`。

## 相关

- [[option.Option|Option]]：`matches!(opt, Some(..))` 最常见的搭档。
- [[result.Result|Result]]：`matches!(r, Ok(_))` 只判断成功与失败。
- [[08-枚举与模式匹配|模式匹配]]：模式语法、`|`、范围与 `if` 守卫的完整讲法。
- [[macro.assert|assert!]]：把 `matches!` 的结果变成断言。
- [[cmp.Ordering|Ordering]]：`matches!(ord, Ordering::Less | Ordering::Equal)` 这类比较判断。
