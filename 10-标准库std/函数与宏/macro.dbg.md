---
title: "std::dbg!"
type: std-条目
kind: 宏
module: std
slug: macro.dbg
stable: "1.32.0"
tags:
  - std/宏
aliases:
  - "dbg!"
  - "dbg 宏"
一句话: "把表达式以 Debug 形式连文件名、行号一起打到 stderr，然后把表达式原值返回，取其值不打断写代码。"
---

# `dbg!`

> [!abstract] 一句话
> `dbg!(expr)` 把 `expr` 的 `Debug` 表示连同文件名、行号、列号和表达式源码一起打到 **stderr**，再把 `expr` 的值原样返回。它在调试时可以插进任何表达式中间，不必把语句拆开重写。

## 简介

普通调试要写 `eprintln!("x = {:?}", x);`，而且只能在语句层面插入。`dbg!` 是表达式，返回值就是被打印的值本身，所以能直接塞进链路里：`let b = dbg!(a * 2) + 1;` 既不改变语义，又能看到中间值。

输出格式是这样的：`[src/main.rs:2:13] a * 2 = 4`——方括号里是 `file!()`、`line!()`、`column!()` 展开的位置，等号左边是 `stringify!` 得到的表达式原文，右边是 `{:#?}` 的漂亮打印。因为多了列号，同一行的两个 `dbg!` 也能分清。

展开结果与返回值：宏展开成一个 `match`：

```text
match $val {
    tmp => {
        eprintln!("[{}:{}:{}] {} = {:#?}", file!(), line!(), column!(), stringify!($val), &tmp);
        tmp
    }
}
```

所以它**按值取走 `$val`**——非 `Copy` 类型会被 move 进去再还回来，`dbg!(s)` 之后 `s` 就失效了。想只看不交所有权，写 `dbg!(&s)`。`dbg!(a, b)` 这种多参数形式会把多个值打成一行并以元组返回；`dbg!()` 只在 stderr 打一个位置标记，返回 `()`。

它输出到 stderr 而不是 stdout，这一点是刻意的：stdout 干净地留给程序真正的输出，`dbg!` 的调试信息不会污染管道里的数据。

## 签名与参数

```text
dbg!() -> ()
dbg!($val:expr $(,)?) -> 与 $val 同类型
dbg!($($val:expr),+ $(,)?) -> 与各个 $val 组成的元组同类型
```

| 参数 | 说明 |
| --- | --- |
| （无参数） | 在 stderr 打一行 `[文件:行:列]`，返回 `()`。 |
| `$val` | 任意实现 `Debug` 的表达式；按值取走，返回同一个值。 |
| 多个 `$val` | 逗号分隔，逐个打印，整体返回元组。 |
| 返回 | 就是被打印的值（或元组），所以能嵌套在表达式里。 |

## 示例

### 插在表达式中间

```rust
fn main() {
    let a = 2;
    // 打印 [src/main.rs:..] a * 2 = 4，然后把 4 交回表达式
    let b = dbg!(a * 2) + 1;
    assert_eq!(b, 5);

    // 链式调用里也能插：每一步的中间值都能看到
    let total: i32 = vec![1, 2, 3]
        .iter()
        .map(|x| x * 2)
        .inspect(|x| println!("inspect: {x}"))
        .sum();
    assert_eq!(total, 12);

    println!("b = {b}, total = {total}");
}
```

### 不交出所有权：`dbg!(&expr)`

```rust
fn main() {
    let name = String::from("小明");

    // 借用形式：只打印，name 之后还能用
    dbg!(&name);
    assert_eq!(name.len(), 6);

    // 按值形式会把 name move 走，所以这里用返回值的绑定接住
    let owned = dbg!(name);
    assert_eq!(owned, "小明");

    // 组合表达式也可以整体丢进去看
    let checked: Option<usize> = dbg!(owned.len().checked_sub(4));
    assert_eq!(checked, Some(2));

    println!("{owned:?} {checked:?}");
}
```

## 常见陷阱

1. **以为 `dbg!` 只读不取**：它按值取走表达式，`dbg!(s)` 之后 `s` 已被移动，加 `&` 才是只读。
2. **在 `--release` 里指望它消失**：`dbg!` 是普通宏，release 下照常执行并打到 stderr，正式版本务必删干净。
3. **把调试输出写进管道数据**：`dbg!` 走 stderr，`println!` 走 stdout，用 `2>/dev/null` 可以单独关掉调试信息；反过来，如果把 `dbg!` 改成 `println!` 就会污染程序输出。
4. **在热点路径里留着 `dbg!`**：每次调用都要格式化并写一次 stderr，比想象中慢很多。
5. **打印的类型没实现 `Debug`**：`dbg!` 要求 `Debug`，没有 derive 就会编译失败，这时只能手写 `Display` 或临时加 `#[derive(Debug)]`。

## 相关

- [[macro.println|println!]]：输出到 stdout 的正式打印，与 `dbg!` 的 stderr 调试输出互补。
- [[fmt.Debug|Debug]]：`dbg!` 依赖的特质，`{:#?}` 的漂亮打印由它决定。
- [[macro.format|format!]]：需要自己拼调试字符串时的通用工具。
- [[25-测试与文档|测试与文档]]：测试里临时排查值的常见手法。
- [[macro.assert|assert!]]：测试中断言不变量，通常和 `dbg!` 搭配定位失败原因。
