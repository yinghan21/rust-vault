---
title: "std::ops::FnOnce"
type: std-条目
kind: 特质
module: ops
slug: ops.FnOnce
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - FnOnce
一句话: 按值接收者的调用运算契约，会移出捕获变量的闭包自动实现它，因此只能调用一次。
---

# `FnOnce`

> [!abstract] 一句话
> `FnOnce` 是三种调用特质里最宽松也最底层的一个：调用时拿走 `self`，所以闭包可以把捕获的值直接返回或移动出去——代价是同一个值只能被调用一次。

## 简介

`FnOnce` 是 `FnMut` 的超特质，`FnMut` 又是 `Fn` 的超特质，形成链 `Fn: FnMut: FnOnce`。这条链的读法是「能力递减、适用面递增」：要求 `Fn` 的地方只能收 `Fn`，要求 `FnOnce` 的地方三类都能收。

为什么需要它？因为「消耗捕获值」是合理需求：`move || s` 把 `String` 直接返回，`thread::spawn` 把数据搬进新线程，`Option::take` 式的「用掉就没了」操作。这些都无法用 `&self` 完成，必须允许调用方交出所有权。

实践中的规则很简单：**约束尽量写成能工作的最宽档位**。函数只调用一次回调，就写 `F: FnOnce(..)`，这样 `Fn` 和 `FnMut` 闭包都能传进来；写死 `F: Fn(..)` 反而会拒绝掉合法的调用者。

## 必须实现

无需也不能手动实现。`call_once` 尚未稳定，自定义类型写不出 `impl FnOnce<..>`；实现由编译器自动生成。

能做的只有写约束：`F: FnOnce(参数) -> 返回值`。

## 提供的方法

`FnOnce` 没有稳定的公开方法。调用 `f(args)` 会消耗 `f`，因此调用点之后 `f` 就不能再用了——这是编译器强制执行的，不依赖运行时检查。

## 与相邻 trait 的关系

| trait | 关系 |
| --- | --- |
| `FnMut` | 子特质：`FnMut` 值都能当 `FnOnce` 用（只调用一次当然合法）。 |
| `Fn` | 更深的子特质：`Fn` 也可当 `FnOnce` 用。 |
| `Send` | `thread::spawn` 同时要求 `FnOnce + Send + 'static`。 |
| `Drop` | `FnOnce` 的值通常持有资源，在作用域结束时按正常顺序析构。 |

## 示例

### 消耗捕获值的闭包

```rust
fn consume_with_relish<F>(func: F) -> String
where
    F: FnOnce() -> String,
{
    // func 会把捕获的 String 移出来，所以只能调用这一次
    let out = func();
    println!("Consumed: {out}");
    out
}

fn main() {
    let x = String::from("x");

    // move 让闭包拿走 x 的所有权，闭包体又把 x 返回 → FnOnce
    let consume_and_return_x = move || x;
    let out = consume_with_relish(consume_and_return_x);

    assert_eq!(out, "x");
    // 到这里 x 和闭包都已被消耗，无法再次调用
}
```

### `thread::spawn` 要求 `FnOnce`

```rust
use std::thread;

fn main() {
    let msg = String::from("from thread");

    // spawn 的约束是 FnOnce + Send + 'static：闭包把 msg 搬进新线程
    let handle = thread::spawn(move || msg);

    assert_eq!(handle.join().unwrap(), "from thread");
}
```

## 常见陷阱

1. **`FnOnce` 里调用两次**：报「use of moved value」。需要重复调用就得把约束改成 `FnMut`，并且避免移出捕获值。
2. **闭包被误判成 `FnOnce`**：只要体内有一次 `move` 出捕获变量（返回它、放进别的容器），整个闭包就降级为 `FnOnce`，即使只调用一次也会在复用处报错。
3. **约束写得过窄**：参数写成 `F: Fn()` 会拒绝带走所有权的闭包；只调用一次的回调应写 `F: FnOnce()`。
4. **`move` 之后还想用原变量**：`move` 闭包构造时就完成了移动，闭包创建之后原变量即失效。
5. **迭代器适配器不接受只 `FnOnce` 的闭包**：`map` 要求 `FnMut`，能消耗捕获值的闭包传不进去，得先 `Option::take` 或改用 `for_each` 外的显式循环。
6. **`Fn` 与 `FnOnce` 全写**：`F: Fn() + FnOnce()` 里的 `FnOnce` 是冗余的，Rust 不允许在同一个约束里同时写三个调用特质（`Fn` 已隐含）。

## 相关

- [[ops.Fn|Fn]]：只读、可重复调用的严格档位。
- [[ops.FnMut|FnMut]]：可累积状态、可重复调用的中间档位。
- [[19-闭包|闭包]]：捕获方式与调用特质的推导链。
- [[thread.spawn|spawn]]：要求 `FnOnce + Send + 'static` 的典型 API。
- [[marker.Send|Send]]：闭包跨线程传递的所有权前提。
- [[ops|std::ops 模块]]：运算符与调用特质总览。
