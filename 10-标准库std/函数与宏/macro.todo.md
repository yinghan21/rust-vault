---
title: "std::todo!"
type: std-条目
kind: 宏
module: std
slug: macro.todo
stable: "1.40.0"
tags:
  - std/宏
aliases:
  - "todo!"
  - "todo 宏"
一句话: "标记尚未实现的代码：一旦执行就 panic，消息为「not yet implemented」，类型是 ! 所以能顶替任何返回值。"
---

# `todo!`

> [!abstract] 一句话
> `todo!` 是「这里我还没写，但先把类型凑上」的占位符：调用它就 panic，消息以 `not yet implemented` 开头，可以附加自定义说明。它的类型是 `!`，因此能放进任何需要返回值的函数体。

## 简介

原型阶段经常遇到这种情况：`trait` 的十个方法只想先实现两个，其它方法必须有方法体才能编译。这时 `todo!()` 是最省事的占位——它满足类型检查，又不会让未实现的分支被悄悄当成「正常返回」。

它和 `unimplemented!` 的区别只在语义与消息：`todo!` 传达「打算以后实现」，panic 消息是 `not yet implemented`；`unimplemented!` 则表示「本来就不打算实现」，消息是 `not implemented`。不少 IDE 会把 `todo!` 单独标出来，方便收尾。

展开结果与返回值：`todo!()` 展开为一次带 `not yet implemented` 前缀的 [[macro.panic|panic!]] 调用，带消息时是 `panic!("not yet implemented: {你的消息}")`；返回类型为 `!`（never type），可以强制转换成任何类型。所以 `fn f() -> u64 { todo!() }`、`match x { A => 1, B => todo!() }` 都能编译。

正因为它是 panic 而不是编译期错误，**`todo!` 留在发布代码里就是一个定时炸弹**：只要执行路径走到这里，程序立刻崩溃。加 `#[deny(clippy::todo)]`、或在 CI 里 grep，能防止它溜进正式版本。

## 签名与参数

```text
todo!() -> !
todo!($msg:expr) -> !
todo!($fmt:expr, $($arg:tt)+) -> !
```

| 参数 | 说明 |
| --- | --- |
| （无参数） | 消息为固定的 `not yet implemented`。 |
| `$msg` | 追加在 `not yet implemented: ` 后面的说明，通常是 `&str`。 |
| `$fmt, $args...` | 与 `format!` 相同的格式化参数，消息里可带变量。 |
| 返回 `!` | never 类型，可当作任何类型使用，函数不会正常返回。 |

## 示例

### 只实现一部分 trait 方法

```rust
trait Foo {
    fn bar(&self) -> u8;
    fn baz(&self);
    fn qux(&self) -> Result<u64, ()>;
}

struct MyStruct;

impl Foo for MyStruct {
    fn bar(&self) -> u8 {
        1 + 1
    }

    fn baz(&self) {
        // 先把结构搭好，baz 的实现留到下一轮
        todo!();
    }

    fn qux(&self) -> Result<u64, ()> {
        // 附加消息会出现在 panic 输出里
        todo!("MyStruct 的 qux 还没实现")
    }
}

fn main() {
    let s = MyStruct;
    s.bar();

    // 只要不调用 baz() / qux()，程序就能正常跑
    println!("bar = {}", s.bar());
}
```

### 在 `match` 分支里占位

```rust
#[derive(Debug)]
enum Command {
    Add(i32, i32),
    Sub(i32, i32),
    Mul(i32, i32),
}

fn eval(cmd: Command) -> i32 {
    match cmd {
        Command::Add(a, b) => a + b,
        Command::Sub(a, b) => a - b,
        // 分支还没写，但类型已经对上了
        Command::Mul(_, _) => todo!("乘法分支待实现"),
    }
}

fn main() {
    assert_eq!(eval(Command::Add(2, 3)), 5);
    assert_eq!(eval(Command::Sub(9, 4)), 5);
    println!("加减分支可用");
}
```

## 常见陷阱

1. **`todo!` 漏到生产代码**：它只在运行时炸，不会编译报错，靠 CI 的 `grep -r "todo!"` 或 clippy 的 `todo` lint 兜底。
2. **以为它会返回 `Default`**：`todo!()` 返回 `!`，不会给你任何值，执行到就 panic。
3. **在 `Drop` 实现里写 `todo!()`**：析构期间的 panic 会导致 abort，比普通 panic 更糟。
4. **用 `todo!()` 顶替「输入校验失败」**：那是可恢复错误，应该返回 `Result`；`todo!` 只表示「代码还没写完」。
5. **`todo!` 与 `unimplemented!` 混用**：语义不同，前者是待办，后者是明确不做，搜索结果和注释含义要保持一致。

## 相关

- [[macro.panic|panic!]]：`todo!` 底层调用的宏，消息与展开方式都在这里。
- [[macro.assert|assert!]]：校验不变量，与占位用的 `todo!` 用途不同。
- [[panic|std::panic]]：panic 如何展开、如何被 `catch_unwind` 接住。
- [[15-trait 基础|trait 基础]]：给 trait 方法留占位实现时最常遇到 `todo!`。
- [[23-宏|宏]]：`todo!` 这类内置宏的展开机制。
