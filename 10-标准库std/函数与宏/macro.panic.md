---
title: "std::panic!"
type: std-条目
kind: 宏
module: std
slug: macro.panic
stable: "1.0.0"
tags:
  - std/宏
aliases:
  - "panic!"
  - "panic 宏"
一句话: "立刻让当前线程 panic，带上自定义消息并沿栈展开；返回类型是 !，可以放进任何需要表达式的位置。"
---

# `panic!`

> [!abstract] 一句话
> `panic!` 立刻中止当前线程：打印一条 `thread ... panicked at ...` 消息，然后按 `panic = "unwind"` 展开栈（或按 `abort` 直接终止进程）。它的类型是 `!`，所以能塞进任何要求返回值的分支。

## 简介

`panic!` 表示「程序遇到了无法继续的状态」。它不同于 [[result.Result|Result]]：`Result` 是把错误交给调用者决定，`panic!` 是当场把这个线程拆掉。标准库自己的 `Option::unwrap`、`Result::unwrap`、`assert!`、下标越界、整数除零，内部都是 `panic!`。

展开过程分两步：先构造 panic 载荷（默认是一个 `&'static str` 或 `String`，即你给的格式化消息），交给 panic 钩子打印位置信息与消息，然后开始 unwind——沿途每个栈帧的析构函数都会执行（所以在 `Vec` 或锁保护下的代码 panic 不会泄漏，`Mutex` 会被标记为 poisoned）。如果 `Cargo.toml` 里设了 `panic = "abort"`，最后这一步换成直接终止进程。

返回类型是 `!`（never type）。这意味着 `panic!` 可以放在 `match` 的某个分支、`if` 的 else 分支里，而不必凑出和另一分支相同的类型；`fn f() -> u8 { panic!("...") }` 也合法。消息部分支持完整的 `format!` 语法：`panic!("值 = {}", x)`、`panic!("{a} 和 {b}", a = 1, b = 2)`。

想拿到 panic 的值而不是让它终止线程，用 `std::panic::catch_unwind` 接住 `Box<dyn Any + Send>`；想把任意类型的值当载荷，用 `std::panic::panic_any`。

## 签名与参数

```text
panic!() -> !
panic!($msg:expr) -> !
panic!($fmt:expr, $($arg:tt)+) -> !
```

| 参数 | 说明 |
| --- | --- |
| （无参数） | 载荷是固定文本 `explicit panic`，只带位置信息。 |
| `$msg` | 一个字符串表达式，作为 `&'static str` 载荷（`panic!(s)` 里 `s` 须是 `&str`）。 |
| `$fmt, $args...` | 与 `format!` 相同的格式化参数，载荷是 `String`。 |
| 返回 `!` | never 类型，可强制转换成任何类型；函数不会正常返回。 |

## 示例

### 用消息表达不变量

```rust
fn divide(a: i32, b: i32) -> i32 {
    if b == 0 {
        // 带格式化参数的消息，载荷是一个 String
        panic!("除数不能为 0，a = {a}");
    }
    a / b
}

fn main() {
    assert_eq!(divide(6, 3), 2);
    println!("divide(6, 3) = {}", divide(6, 3));
}
```

### 用 `catch_unwind` 观察载荷

```rust
use std::panic;

fn divide(a: i32, b: i32) -> i32 {
    if b == 0 {
        panic!("除数不能为 0");
    }
    a / b
}

fn main() {
    let result = panic::catch_unwind(|| divide(1, 0));
    let payload = result.unwrap_err();

    // 默认载荷是 &str 或 String，两种都试一下
    let msg = payload
        .downcast_ref::<&str>()
        .copied()
        .or_else(|| payload.downcast_ref::<String>().map(String::as_str))
        .unwrap_or("<非字符串载荷>");

    assert_eq!(msg, "除数不能为 0");
    println!("捕获到 panic: {msg}");
}
```

## 常见陷阱

1. **用 `panic!` 处理用户输入错误**：库和 CLI 都应返回 `Result`，panic 留给「程序自身逻辑已损坏」的情况，否则调用方没法恢复。
2. **`panic!(s)` 传了 `String`**：这个位置只接受 `&str`（或格式化参数），`String` 要么 `panic!("{s}")`，要么用 `panic_any`。
3. **以为 panic 会终止整个进程**：默认只终止当前线程，其它线程照跑；主线程 panic 才让进程以非零码退出。
4. **在 `Drop` 里 panic**：unwind 过程中再次 panic 会直接 abort，析构函数里只该记录日志，不该 panic。
5. **依赖 panic 做控制流**：`catch_unwind` 有开销，而且被 panic 打断的结构可能处于半更新状态，别把它当 `try/catch` 用。
6. **改了 `panic = "abort"` 还指望析构函数跑**：abort 下不 unwind，栈上资源的析构与 `Mutex` 解锁都不会发生，需要显式清理。

## 相关

- [[macro.assert|assert!]]：条件不成立时调用 `panic!` 的断言宏。
- [[macro.todo|todo!]] / `unimplemented!`：占位用的 panic，消息固定为「not yet implemented」。
- [[panic|std::panic]]：`catch_unwind`、`panic_any`、`set_hook` 与 unwind 语义。
- [[result.Result|Result]]：可恢复错误的正规通道，与 panic 分工。
- [[11-错误处理|错误处理]]：什么时候 `Result`、什么时候 panic 的判断标准。
