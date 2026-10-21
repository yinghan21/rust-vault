---
title: "std::time::Instant"
type: std-条目
kind: 结构体
module: time
slug: time.Instant
stable: "1.8.0"
tags:
  - std/类型
  - std/时间
aliases:
  - Instant
一句话: 单调不减的时钟读数，不透明、只能互相比较或相减得到 Duration，用来测耗时和算超时。
---

# `Instant`

> [!abstract] 一句话
> `Instant` 是「单调时钟上的一个时刻」：它只会前进不会后退，但你读不出它「是几点」，只能拿两个 `Instant` 相减得到一段 `Duration`。

## 简介

`Instant` 回答的是「过了多久」，不是「现在几点」。官方保证（除平台 bug 外）后创建的 `Instant` 不会小于先创建的；因此它非常适合给代码计时、做 benchmark、实现超时判断。与之相对，[[time.SystemTime|SystemTime]] 读的是系统墙上时钟，可能被 NTP 或手动校时往回拨，测耗时会出现负数。

它同时**不是「稳定时钟」**：每次 tick（时钟跳一次）代表的真实时长不保证相同，某些秒可能更长或更短，`Instant` 也可能突然向前跳或经历时间膨胀，但绝不会倒退。系统挂起（睡眠）算不算经过的时间，标准库明确不作保证，各平台和各版本的 Rust 行为可能不同。

`Instant` 是**不透明类型**：没有任何方法能取出「内部秒数」，它只支持与另一个 `Instant` 比较大小（实现了 `Ord`）或相减。它还实现了 `Copy`、`Clone`、`Eq`、`Hash`、`Debug`，可以与 `Duration` 做 `+` / `-` 运算（溢出会 panic），也可以存进集合里当时间戳。因为语义只在一台机器、一次开机内成立，它不能被序列化，也不适合持久化。

```rust
use std::time::{Duration, Instant};

fn main() {
    let start = Instant::now();
    let sum: u64 = (0..100_000u64).sum();
    let elapsed = start.elapsed();
    println!("sum = {}，耗时 {:?}", sum, elapsed);
    // 两个时刻的顺序可以比较
    assert!(Instant::now() > start);
}
```

## 常用方法

### 读取与耗时

| 方法 | 说明 |
| --- | --- |
| `now()` | 返回当前时刻的 `Instant`。 |
| `elapsed()` | 返回从该时刻到现在经过的时长。 |
| `duration_since(earlier)` | 返回从 `earlier` 到自身的时长。 |
| `checked_duration_since(earlier)` | 同上，但 `earlier` 更晚时返回 `None`。 |
| `saturating_duration_since(earlier)` | 同上，但 `earlier` 更晚时返回零时长。 |

### 加减时长

| 方法 | 说明 |
| --- | --- |
| `checked_add(duration)` | 加上一段时长，超出可表示范围返回 `None`。 |
| `checked_sub(duration)` | 减去一段时长，超出可表示范围返回 `None`。 |

> [!tip] 为什么还有「更早 vs 更晚」两种版本
> `duration_since` 在参数比自身更晚时**返回零**而不报错，这是历史行为；想要区分「恰好零」和「时钟反向」，用 `checked_duration_since` 拿 `Option`，或 `saturating_duration_since` 明确表达「不小于零」。

## 示例

```rust
use std::time::{Duration, Instant};

fn main() {
    let now = Instant::now();

    // 加法：得到一个「未来」的时刻；减法回到过去
    let later = now.checked_add(Duration::from_secs(60)).unwrap();
    let earlier = later.checked_sub(Duration::from_secs(60)).unwrap();
    assert_eq!(later.duration_since(now), Duration::from_secs(60));

    // 参数比自身更晚时，三者行为不同
    assert_eq!(earlier.duration_since(later), Duration::ZERO);
    assert_eq!(earlier.checked_duration_since(later), None);
    assert_eq!(earlier.saturating_duration_since(later), Duration::ZERO);

    // 超出可表示范围时返回 None，而不是 panic
    assert!(now.checked_add(Duration::MAX).is_none());

    // 计时：从创建到读 elapsed 一定不会为负
    let start = Instant::now();
    let mut acc = 0u64;
    for i in 0..10_000u64 {
        acc = acc.wrapping_add(i);
    }
    let spent = start.elapsed();
    println!("acc = {}，耗时 {:?}", acc, spent);
    assert!(spent >= Duration::ZERO);
}
```

## 常见陷阱

1. **用 `SystemTime` 测耗时**：系统时钟会被校时回拨，算出来可能是负数或巨大跳变；测耗时统一用 `Instant`。
2. **把 `Instant` 当「稳定时钟」做校准**：tick 长度不保证一致，不能用「差了几个 tick」反推精确的物理时间。
3. **想从 `Instant` 取出秒数**：它是不可读的，没有 `as_secs` 之类的入口，只能两个时刻相减。
4. **跨进程或持久化**：`Instant` 的零点由平台决定（如开机时刻），不能存盘后到下次运行再比较，也不能跨机器比较。
5. **直接用 `+` / `-` 运算符**：`Instant + Duration` 溢出会 panic，不确定范围时改用 `checked_add` / `checked_sub`。

## 相关

- [[time|std::time 模块]]：本模块全部条目。
- [[time|std::time 模块]] 中的 `Duration`：`Instant` 相减得到的结果类型。
- [[time.SystemTime|SystemTime]]：墙上时钟，用于读写「年月日」意义上的时间。
- [[thread.sleep|sleep]]：配合 `Instant` 做等待与超时的最小工具。
- [[26-性能与优化|性能与优化]]：基准测试中如何正确计时。
