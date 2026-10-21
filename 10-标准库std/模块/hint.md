---
title: "std::hint"
type: std-模块
module: hint
stable: "1.27.0"
unstable: false
tags:
  - std/模块
aliases:
  - hint
一句话: 给编译器的优化提示：黑盒、自旋、不可达与分支概率，用它们写出更快的代码。
---

# std::hint

> [!abstract] 一句话
> `std::hint` 收集了编译器自己推断不出来的信息：哪些值要当成黑盒、哪个循环在自旋、哪个分支几乎不会走。

## 模块简介

`std::hint` 里的函数都是**提示（hint）**：语义上它们是恒等函数或空操作，不改变程序的可观察行为，只影响优化器的决策。编译器无法凭空知道「这个循环的出口几乎总走 `else`」或者「这段基准测试的参数其实是随机的」，hint 就是补上这块信息的接口。

使用频率最高的几个：

- `hint::black_box`：让优化器对这个值一无所知，基准测试必备，防止被测代码被常量折叠掉。
- `hint::spin_loop`：发出一条 `pause` / `yield` 指令，告诉 CPU 当前是忙等循环。
- `hint::unreachable_unchecked` / `hint::assert_unchecked`：把 `unsafe` 代码里「我保证不会发生」的承诺写成代码，换来更少的边界检查；承诺不成立即未定义行为。
- `hint::must_use`：反过来用，丢弃返回值会触发 `unused_must_use` 警告。

除上述稳定条目外，本模块还有一批 nightly 专属的实验性函数（`likely`、`unlikely`、`cold_path`、`select_unpredictable`、`prefetch_*`）和枚举 `Locality`，用于分支概率与缓存预取；它们会变，稳定前不要写进生产代码。

## 快速上手

```rust
use std::hint;

fn main() {
    // 1. black_box 对优化器不透明：即使参数是常量，也不会被折叠掉
    let v = hint::black_box(41) + 1;
    assert_eq!(v, 42);

    // 2. 自旋等待时提示 CPU 让出执行资源
    for _ in 0..3 {
        hint::spin_loop();
    }

    // 3. assert_unchecked 把 unsafe 前提告诉编译器；
    //    承诺不成立就是未定义行为，必须自己确保 x > 0
    let x = 5i32;
    let doubled = unsafe {
        hint::assert_unchecked(x > 0);
        x * 2
    };
    assert_eq!(doubled, 10);

    println!("black_box = {}", v);
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| `hint::black_box` | 恒等函数，让优化器无法看穿其输入输出。 |
| `hint::spin_loop` | 发出自旋等待指令，忙等时省电并让出资源。 |
| `hint::assert_unchecked` | 承诺条件恒成立，让编译器省掉检查（unsafe）。 |
| `hint::unreachable_unchecked` | 声明此处不可达，用于替代 `unreachable!`（unsafe）。 |
| `hint::must_use` | 返回值被丢弃时触发 `unused_must_use` 警告。 |
| `hint::likely` | 提示分支条件很可能为真（实验性）。 |
| `hint::unlikely` | 提示分支条件很可能为假（实验性）。 |
| `hint::cold_path` | 标记「几乎不会执行」的冷路径（实验性）。 |
| `hint::select_unpredictable` | 提示分支难以预测，倾向生成无分支代码（实验性）。 |
| `hint::prefetch_read` / `hint::prefetch_write` | 预取读 / 写方向的缓存行（实验性）。 |
| `hint::prefetch_read_instruction` | 把缓存行预取进指令缓存（实验性）。 |
| `hint::prefetch_read_non_temporal` / `prefetch_write_non_temporal` | 非临时预取，尽量不污染缓存（实验性）。 |
| `hint::Locality` | 预取操作期望的时间局部性枚举（实验性）。 |

## 注意事项

> [!warning] 提示不是保证
> 优化器可以无视 `likely` / `unlikely` / `cold_path`；`black_box` 也只保证「代码语义不变」，不保证一定不优化。想验证效果，只能看汇编或基准测试数据，不要凭直觉。

> [!danger] 两个 `unsafe` 条目的契约
> `assert_unchecked(cond)` 要求 `cond` 在运行时**一定**为真；`unreachable_unchecked()` 要求执行流永远不会到达该位置。违反任意一条都是 UB，编译器可能据此删掉整个分支——包括错误处理分支。

> [!tip] 先测量再提示
> `std::hint` 是手动微优化，适合热点路径。先写清晰的代码，用性能分析找到瓶颈后再加 hint，并保留基准测试作为回归依据，可参考 [[26-性能与优化|性能与优化]]。

## 相关

- [[26-性能与优化|性能与优化]]：什么时候值得用 hint、如何度量收益。
- [[24-unsafe 与 FFI|unsafe 与 FFI]]：`unsafe` 契约与未定义行为的边界。
- [[ptr|std::ptr 模块]]：裸指针，预取类 hint 的操作对象。
- [[sync|std::sync 模块]]：自旋锁场景里 `spin_loop` 的搭档。
- [[mem|std::mem 模块]]：布局、容量与「编译器可能做的假设」。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 15 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 枚举

- [`Locality`](https://doc.rust-lang.org/std/hint/enum.Locality.html)

### 函数

- [`assert_unchecked`](https://doc.rust-lang.org/std/hint/fn.assert_unchecked.html)
- [`black_box`](https://doc.rust-lang.org/std/hint/fn.black_box.html)
- [`cold_path`](https://doc.rust-lang.org/std/hint/fn.cold_path.html)
- [`select_unpredictable`](https://doc.rust-lang.org/std/hint/fn.select_unpredictable.html)
- [`spin_loop`](https://doc.rust-lang.org/std/hint/fn.spin_loop.html)
- [`unreachable_unchecked`](https://doc.rust-lang.org/std/hint/fn.unreachable_unchecked.html)
- [`likely`](https://doc.rust-lang.org/std/hint/fn.likely.html)
- [`must_use`](https://doc.rust-lang.org/std/hint/fn.must_use.html)
- [`prefetch_read`](https://doc.rust-lang.org/std/hint/fn.prefetch_read.html)
- [`prefetch_read_instruction`](https://doc.rust-lang.org/std/hint/fn.prefetch_read_instruction.html)
- [`prefetch_read_non_temporal`](https://doc.rust-lang.org/std/hint/fn.prefetch_read_non_temporal.html)
- [`prefetch_write`](https://doc.rust-lang.org/std/hint/fn.prefetch_write.html)
- [`prefetch_write_non_temporal`](https://doc.rust-lang.org/std/hint/fn.prefetch_write_non_temporal.html)
- [`unlikely`](https://doc.rust-lang.org/std/hint/fn.unlikely.html)

<!-- END AUTO ITEMS -->
