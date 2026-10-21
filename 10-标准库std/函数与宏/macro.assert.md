---
title: "std::assert!"
type: std-条目
kind: 宏
module: std
slug: macro.assert
stable: "1.38.0"
tags:
  - std/宏
aliases:
  - "assert!"
  - "assert 宏"
一句话: "断言布尔表达式为真，为假就调用 panic!；release 下依然检查、无法关闭，展开成 if !cond { panic!(..) }。"
---

# `assert!`

> [!abstract] 一句话
> `assert!` 检查一个布尔表达式，为 `true` 就什么都不做，为 `false` 就调用 [[macro.panic|panic!]] 并带上「assertion failed」和你给的补充消息。它**在 debug 和 release 下都会执行**，没有开关能关掉。

## 简介

`assert!` 是「这里必须成立，否则程序已经错了」的表达方式。测试里的期望检查、函数入口的参数校验、`unsafe` 代码前面守住不变量，都用它。它和 `debug_assert!` 的分工很明确：`debug_assert!` 默认只在 debug 构建里生效，`assert!` 永远生效。

展开结果：`assert!(cond)` 展开为

```text
if !cond { ::std::panic!("assertion failed: {}", ::std::stringify!(cond)) }
```

所以失败时的消息默认就是条件的源码文本，比如 `assertion failed: a + b == 30`；带自定义消息的分支则展开为 `if !cond { ::std::panic!($($arg)+) }`。整条宏语句的值是 `()`，它不返回 `Result`，不能 `?`——要可恢复的错误请用 [[result.Result|Result]]。

返回值与「release 下是否还在」这两点经常被搞混：`assert!` 不产生任何值，副作用只有「可能 panic」；而它在 release 下仍然检查，编译器不会把它优化掉，所以不能拿 `assert!` 做有副作用的正经工作（比如 `assert!(queue.pop().is_some())` 这种「顺手弹一个」的写法虽然能用，但语义上是在用断言改变状态，非常容易在别人改成 `debug_assert!` 后失效）。

`unsafe` 代码可以依赖 `assert!` 来维持「一旦违反就会导致未定义行为」的运行时前提，因为它不会被释放版优化掉——这也是标准库文档特意强调的一点。

## 签名与参数

```text
assert!($cond:expr $(,)?) -> ()
assert!($cond:expr, $($arg:tt)+) -> ()
```

| 参数 | 说明 |
| --- | --- |
| `$cond` | 任意求值为 `bool` 的表达式；注意必须是 `bool`，`assert!(1)` 编译失败。 |
| `$arg...` | 可选的自定义 panic 消息，格式与 `format!` 相同（`{}` 占位符）。 |
| 返回 `()` | 成立时什么也不返回；不成立时 panic，因此后面的代码不会执行。 |

| 宏 | 说明 |
| --- | --- |
| `assert!` | 永远检查，release 下也生效。 |
| `assert_eq!` / `assert_ne!` | 失败时打印两边的 `Debug` 表示，比 `assert!(a == b)` 好排查。 |
| `debug_assert!` | 仅 debug 构建检查，release 下整段被移除。 |

## 示例

### 基本断言与自定义消息

```rust
fn main() {
    assert!(true);
    assert!(1 + 1 == 2);

    // 自定义消息里可以带参数，失败时原样格式化出来
    let x = 3;
    let y = 27;
    assert!(x + y == 30, "x = {x}, y = {y} 的和不对");

    let v = vec![1, 2, 3];
    assert!(!v.is_empty(), "向量不应为空");
    assert!(v.len() == 3);
    assert!(v.contains(&2));

    println!("全部断言通过: {v:?}");
}
```

### 在 `unsafe` 之前守住不变量

```rust
fn main() {
    let v = vec![10, 20, 30];
    let idx = 2;

    // unsafe 块前先断言，保证 get_unchecked 的下标合法
    assert!(idx < v.len(), "下标 {idx} 越界");
    let value = unsafe { *v.get_unchecked(idx) };
    assert_eq!(value, 30);

    // release 下也生效：换成 debug_assert! 就在 --release 里消失了
    assert!(v.capacity() >= v.len());
    println!("v[{idx}] = {value}");
}
```

## 常见陷阱

1. **以为 release 会关掉断言**：`assert!` 永远执行，想只在 debug 检查请用 `debug_assert!`，否则热点路径上的断言会成为 release 的性能负担。
2. **把有副作用的表达式塞进断言**：`assert!(counter.next().is_some())` 在改成 `debug_assert!` 后行为就变了，断言应保持无副作用。
3. **`assert!(1)` 编译失败**：条件必须是 `bool`，整数/指针不会隐式转换，写 `assert!(n != 0)`。
4. **用 `assert!` 代替错误处理**：输入错误应该返回 `Result`，只有「程序内部不变量被破坏」才 panic。
5. **比较浮点用 `assert!(a == b)`**：浮点相等几乎总是错的，写 `assert!((a - b).abs() < 1e-9)` 或直接用 `assert_eq!` 比较可精确表示的值。
6. **消息里的 `{}` 忘了参数**：`assert!(cond, "值 = {}")` 编译失败，占位符个数必须和参数对得上。

## 相关

- [[macro.panic|panic!]]：`assert!` 失败时实际调用的宏，决定消息与展开方式。
- [[macro.matches|matches!]]：常在 `assert!` 里搭配使用，判断「是否匹配某个模式」。
- [[panic|std::panic]]：panic 载荷、`catch_unwind`、unwind 与 abort 的选择。
- [[result.Result|Result]]：可恢复错误走这条路，不要用 `assert!` 顶替。
- [[25-测试与文档|测试与文档]]：断言在 `#[test]` 里的标准用法。
