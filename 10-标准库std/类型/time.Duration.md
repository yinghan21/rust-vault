---
title: "std::time::Duration"
type: std-条目
kind: 结构体
module: time
slug: time.Duration
stable: "1.3.0"
tags:
  - std/类型
  - std/时间
aliases:
  - Duration
一句话: 表示一段时长（整秒 + 纳秒），用于超时、间隔和耗时统计。
---

# `Duration`

> [!abstract] 一句话
> `Duration` 表示一段**时间长度**（不是时间点），内部由「整秒 `u64` + 纳秒 `u32`」组成，精度到纳秒。

## 简介

`Duration` 描述的是「多久」，例如「等待 5 秒」「超时 300 毫秒」；而 [[time.Instant|Instant]] 描述的是「某个时刻」。

- 内部表示：`secs: u64` + `nanos: u32`（`nanos < 1_000_000_000`），所以**不会出现浮点误差**。
- 实现了 `Add`、`Sub`、`Mul<u32>`、`Div<u32>`、`Ord`、`Hash`、`Debug`、`Default` 等常见 trait。
- 有意**没有实现 `Display`**：一段时长该怎么展示（`1.5s`？`1500ms`？）取决于场景，需要自己格式化。
- 计时请用 [[time.Instant|Instant]] 做差得到 `Duration`，不要用系统时间相减。

```rust
use std::time::Duration;

fn main() {
    let d = Duration::from_millis(1500);
    assert_eq!(d.as_secs(), 1);
    assert_eq!(d.subsec_millis(), 500);
    assert_eq!(d.as_millis(), 1500);
}
```

## 关联常量

| 常量 | 说明 |
| --- | --- |
| `Duration::ZERO` | 长度为 0 的时长。 |
| `Duration::MAX` | 可表示的最大时长（约 5849 亿年）。 |

## 构造

| 方法 | 说明 |
| --- | --- |
| `new(secs, nanos)` | 由整秒和纳秒构造；`nanos >= 1e9` 时会进位。 |
| `from_secs(secs)` | 由整秒构造。 |
| `from_millis(millis)` | 由毫秒构造。 |
| `from_micros(micros)` | 由微秒构造。 |
| `from_nanos(nanos)` | 由纳秒构造。 |
| `from_nanos_u128(nanos)` | 由 `u128` 纳秒构造，避免大数溢出。 |
| `from_hours(hours)` | 由小时构造。 |
| `from_mins(mins)` | 由分钟构造。 |
| `from_secs_f64(secs)` | 由 `f64` 秒构造；负数或 NaN 会 panic。 |
| `from_secs_f32(secs)` | 由 `f32` 秒构造；负数或 NaN 会 panic。 |
| `try_from_secs_f64(secs)` | 可失败版本，非法输入返回 `Err`。 |
| `try_from_secs_f32(secs)` | 可失败版本，非法输入返回 `Err`。 |

> [!tip] 用 `try_from_secs_*` 代替 `from_secs_*`
> 输入来自用户或外部数据时，`from_secs_f64` 遇到负数、NaN、无穷大都会 **panic**，应改用 `try_from_secs_f64`。

## 读取与转换

| 方法 | 说明 |
| --- | --- |
| `is_zero()` | 长度是否为 0。 |
| `as_secs()` | 总整秒数（`u64`）。 |
| `subsec_millis()` | 小数部分的毫秒数（`0..1000`）。 |
| `subsec_micros()` | 小数部分的微秒数（`0..1_000_000`）。 |
| `subsec_nanos()` | 小数部分的纳秒数（`0..1_000_000_000`）。 |
| `as_millis()` | 总毫秒数（`u128`）。 |
| `as_micros()` | 总微秒数（`u128`）。 |
| `as_nanos()` | 总纳秒数（`u128`）。 |
| `as_secs_f64()` | 以 `f64` 表示的秒数。 |
| `as_secs_f32()` | 以 `f32` 表示的秒数。 |

## 运算

| 方法 | 说明 |
| --- | --- |
| `abs_diff(other)` | 与另一时长的绝对差。 |
| `checked_add(rhs)` | 加法，溢出返回 `None`。 |
| `saturating_add(rhs)` | 加法，溢出封顶到 `Duration::MAX`。 |
| `checked_sub(rhs)` | 减法，下溢返回 `None`。 |
| `saturating_sub(rhs)` | 减法，下溢封底到 `ZERO`。 |
| `checked_mul(rhs)` | 乘以 `u32`，溢出返回 `None`。 |
| `saturating_mul(rhs)` | 乘以 `u32`，溢出封顶。 |
| `checked_div(rhs)` | 除以 `u32`，除数为 0 返回 `None`。 |
| `mul_f64(rhs)` | 乘以 `f64`（结果向零取整到纳秒）。 |
| `mul_f32(rhs)` | 乘以 `f32`。 |
| `div_f64(rhs)` | 除以 `f64`；除数为 0 或结果非法会 panic。 |
| `div_f32(rhs)` | 除以 `f32`。 |
| `div_duration_f64(rhs)` | 两个 `Duration` 相除，返回 `f64`。 |
| `div_duration_f32(rhs)` | 两个 `Duration` 相除，返回 `f32`。 |

> [!warning] `Duration + Duration` 会 panic
> `+`、`-`、`*` 等运算符实现在溢出时会 **panic**。处理外部数据或累加大量时长时，优先用 `checked_*` / `saturating_*`。

## 示例：给操作设置超时语义

```rust
use std::time::{Duration, Instant};

fn main() {
    let timeout = Duration::from_millis(200);
    let start = Instant::now();

    // 模拟一段工作
    let mut sum = 0u64;
    for i in 0..1_000u64 {
        sum = sum.wrapping_add(i);
    }

    let elapsed = start.elapsed();
    if elapsed > timeout {
        println!("超时：耗时 {:?}，预算 {:?}", elapsed, timeout);
    } else {
        println!("完成：耗时 {:?}，sum = {}", elapsed, sum);
    }
}
```

## 常见陷阱

1. **把 `Duration` 当时间点**：它不能告诉你「现在几点」，要用 [[time.SystemTime|SystemTime]]。
2. **`as_secs()` 会截断**：1500ms → `as_secs()` 是 1，不是 1.5；需要毫秒请用 `as_millis()`。
3. **`subsec_*` 只取小数部分**：`Duration::from_secs(61)` 的 `subsec_nanos()` 是 0，不是 61 秒。
4. **浮点构造会 panic**：`Duration::from_secs_f64(-1.0)` 直接 panic。
5. **`Duration` 的 `Debug` 输出带单位**（如 `1.5s`），可以直接用于日志，但不要依赖它的格式做解析。

## 相关

- [[time.Instant|Instant]]：单调时钟，用来测耗时、算超时。
- [[time.SystemTime|SystemTime]]：墙上时钟，用来读系统时间。
- [[time|std::time 模块]]：本模块全部条目。
- [[并发编程|并发编程]]、[[net|std::net]] 中的超时参数都是 `Duration`。
