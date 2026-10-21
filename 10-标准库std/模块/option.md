---
title: "std::option"
type: std-模块
module: option
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - option
一句话: "可选值 Option<T>：用类型显式表示「可能没有值」，替代可空引用。"
---

# std::option

> [!abstract] 一句话
> `std::option` 只定义了一个枚举 `Option<T>`——`Some(T)` 或 `None`——它是 Rust 用来替代 `null` 的全部答案：没有值的可能性被写进类型，忘了处理就编译不过。

## 模块简介

`Option<T>` 存在的理由就是「不要 null」。C、C++、Java 里的引用可能为空，空指针解引用是几十年来最常见的崩溃来源；Rust 干脆规定：**指针必须指向合法位置，没有 null 引用**。想表达「可能没有值」，就把 `T` 包进 `Option<T>`，此时类型系统会一直提醒你还有 `None` 这个分支。这比「约定 + 文档 + if (p != null)」强的地方在于：遗漏分支是编译错误，而不是线上故障。

第二个理由是不必付出运行时成本。手写 `(bool, T)` 要额外存一个标志位，而 `Option<T>` 在 `T` 有空位（niche）时能直接复用：`Option<&T>`、`Option<Box<T>>`、`Option<NonZeroU32>` 与不带 `Option` 的版本大小完全相同，`None` 用全零（无效指针/零值）表示。所以「用 `Option` 更安全」并不意味着「更慢」。

与 [[result.Result|Result]] 的分工要记清：`Option` 表示「没有就是没有，不需要解释」，`Result` 表示「失败了，这是原因」。从 `HashMap` 里 `get` 一个键、字符串 `find` 一个子串、`Vec::last` 取末尾，都返回 `Option`——没找到不需要理由。真正需要错误信息时，用 `ok_or` / `ok_or_else` 把它升级成 `Result`。

日常写法有两套：模式匹配（`match`、`if let`、`while let`）用来「有值才做事」，方法组合（`map`、`and_then`、`filter`、`or_else`、`unwrap_or`、`?`）用来把多层判断压成线性调用。二者混着用，比一层层嵌套 `match` 可读得多。

## 快速上手

```rust
fn divide(a: f64, b: f64) -> Option<f64> {
    if b == 0.0 { None } else { Some(a / b) }
}

fn first_word_len(text: &str) -> Option<usize> {
    text.split_whitespace().next().map(str::len)
}

// 返回 Option 的函数里，? 可以直接短路 None
fn parse_pair(s: &str) -> Option<(i32, i32)> {
    let (left, right) = s.split_once(',')?;
    Some((left.trim().parse().ok()?, right.trim().parse().ok()?))
}

fn main() {
    assert_eq!(divide(10.0, 4.0), Some(2.5));
    assert_eq!(divide(1.0, 0.0), None);

    // 模式匹配：两个分支都必须写
    match divide(1.0, 0.0) {
        Some(v) => println!("结果 = {v}"),
        None => println!("除数为 0，没有结果"),
    }

    // if let 只关心有值的情况
    if let Some(len) = first_word_len("  hello world  ") {
        assert_eq!(len, 5);
    }

    // 组合子把分支拉平
    assert_eq!(divide(9.0, 3.0).map(|v| v * 2.0), Some(6.0));
    assert_eq!(divide(9.0, 0.0).unwrap_or(0.0), 0.0);
    assert_eq!(parse_pair("1, 2"), Some((1, 2)));
    assert_eq!(parse_pair("1"), None);

    // Option 与 Result 互转
    let missing: Option<i32> = None;
    let err: Result<i32, &str> = missing.ok_or("缺少数值");
    assert!(err.is_err());

    // 空指针优化：Option<&T> 与 &T 同样大
    assert_eq!(
        std::mem::size_of::<Option<&i32>>(),
        std::mem::size_of::<&i32>()
    );
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[option.Option\|Option]] | 可选值枚举：`Some(T)` 或 `None`。 |
| `Option::Some` / `Option::None` | 两个变体，通常直接构造或匹配。 |
| `Option::map` | 有值时映射，`None` 原样传递。 |
| `Option::and_then` | 串联返回 `Option` 的操作，避免嵌套。 |
| `Option::unwrap_or` / `unwrap_or_else` | 提供默认值 / 延迟计算默认值。 |
| `Option::ok_or` / `ok_or_else` | 转成 `Result` 并附上错误值。 |
| `Option::filter` | 有值时再判断条件，不满足转 `None`。 |
| `Option::as_ref` / `as_mut` | 借用内部值而不消耗 `Option`。 |
| `Option::take` / `replace` | 取出值，留下 `None` 或新值。 |
| `Option::iter` | 当作 0 或 1 个元素的迭代器。 |
| `option::Iter` / `option::IterMut` | `iter()` / `iter_mut()` 返回的迭代器。 |
| `option::IntoIter` | `into_iter()` 返回的按值迭代器。 |
| [[result.Result\|Result]] | 「失败并带原因」的对应类型，二者常互转。 |

## 注意事项

> [!warning] `Option` 不承担错误信息
> 需要知道「为什么没有」时用 `Result`。另外 `unwrap()` 在 `None` 上会 panic，只适合测试与逻辑上不可能为空的场合；生产代码优先 `unwrap_or`、`ok_or` 或 `expect("说明原因")`。

> [!tip] 优先用组合子，而不是多层 `match`
> 一层 `match` 最清楚，三层就该改成 `map`/`and_then`/`?`。`and_then` 专用于串联「每一步都可能没有值」的操作，返回值仍是 `Option`，不会出现 `Option<Option<T>>`。

> [!danger] `Option<&T>` 和 `&Option<T>` 不是一回事
> 前者是「可能有、也可能没有的引用」，后者是「指向一个可能为空的容器的引用」，后者几乎总是设计错误。函数签名里想放宽参数，用 `Option<&T>` 或 `impl Into<Option<&T>>`。

## 相关

- [[option.Option|Option]]：枚举本体、全部方法与示例。
- [[result|std::result]]：`Result` 模块页，错误处理的主入口。
- [[result.Result|Result]]：`Ok`/`Err` 与 `?` 的完整语义。
- [[08-枚举与模式匹配|模式匹配]]：`match`、`if let` 与穷尽性检查。
- [[11-错误处理|错误处理]]：何时用 `Option`、何时升级成 `Result`。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 5 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`IntoIter`](https://doc.rust-lang.org/std/option/struct.IntoIter.html)
- [`Iter`](https://doc.rust-lang.org/std/option/struct.Iter.html)
- [`IterMut`](https://doc.rust-lang.org/std/option/struct.IterMut.html)
- [`OptionFlatten`](https://doc.rust-lang.org/std/option/struct.OptionFlatten.html)

### 枚举

- [[option.Option|`Option`]]

<!-- END AUTO ITEMS -->
