---
title: "std::time::SystemTime"
type: std-条目
kind: 结构体
module: time
slug: time.SystemTime
stable: "1.8.0"
tags:
  - std/类型
  - std/时间
aliases:
  - SystemTime
一句话: 系统墙上时钟的一个时间点，可能与 UNIX_EPOCH 相减换算成人类可读时间，与别的时刻比较会返回 Result。
---

# `SystemTime`

> [!abstract] 一句话
> `SystemTime` 是「系统墙上时钟的一个时间点」，用于和文件系统、其他进程、日志打交道；它**不单调**，所以两两相减返回的是 `Result<Duration, SystemTimeError>` 而不是 `Duration`。

## 简介

`SystemTime::now()` 读的是操作系统维护的墙上时钟，也就是你在桌面右下角看到的那个时间。它适合回答「这个文件是什么时候改的」「这条日志发生在哪一刻」这类需要和外部世界对齐的问题，也是 `std::fs::Metadata` 里时间戳的类型。

和 [[time.Instant|Instant]] 最大的区别是**它可能倒退**：NTP 校时、手动改系统时间、闰秒处理都可能让时钟往回跳。于是「后发生的操作反而有更早的时间戳」是完全可能的，标准库因此把两个 `SystemTime` 的差做成可失败操作——`duration_since` / `elapsed` 返回 `Result<Duration, SystemTimeError>`，提醒你必须处理时钟漂移。

`SystemTime` 本身同样是不透明的：读不出年月日。标准库提供的锚点是 `UNIX_EPOCH` 常量（1970-01-01 00:00:00 UTC），用 `now.duration_since(UNIX_EPOCH)` 得到自纪元起的 `Duration`，再自己换算成天、时、分、秒。格式化成本地日期时间不在标准库范围内，需要自己算或用第三方 crate。可表示的年份范围依赖平台，Windows 上通常比 Unix 窄，因此加减时长要用 `checked_add` / `checked_sub`。

```rust
use std::time::{Duration, SystemTime, UNIX_EPOCH};

fn main() {
    let now = SystemTime::now();
    let since_epoch = now.duration_since(UNIX_EPOCH).unwrap();
    let days = since_epoch.as_secs() / 86_400;
    println!("自 1970-01-01 起约 {} 天", days);
    assert!(since_epoch.as_secs() > 0);
    // 与 Instant 不同，相减拿到的是 Result
    let _ok: Result<Duration, _> = now.elapsed();
}
```

## 常用方法

### 读取当前时刻

| 方法 | 说明 |
| --- | --- |
| `now()` | 返回当前系统时间。 |

### 计算时间差

| 方法 | 说明 |
| --- | --- |
| `duration_since(earlier)` | 返回从 `earlier` 到自身的时长，时钟倒拨时报错。 |
| `elapsed()` | 返回从该时刻到现在的时长，时钟倒拨时报错。 |

### 加减时长

| 方法 | 说明 |
| --- | --- |
| `checked_add(duration)` | 加上一段时长，超出平台可表示范围返回 `None`。 |
| `checked_sub(duration)` | 减去一段时长，超出平台可表示范围返回 `None`。 |

> [!warning] 只有 `checked_*` 的加法是安全的
> `SystemTime + Duration` 的运算符实现在溢出时会 panic，而不同平台能表示的年份范围差别很大（有的只覆盖 1970 前后若干年）。处理用户输入或远端时间戳时一律用 `checked_add` / `checked_sub`。

## 示例

```rust
use std::time::{Duration, SystemTime, UNIX_EPOCH};

fn main() {
    let now = SystemTime::now();

    // 换算成自 UNIX 纪元经过的秒数
    let since_epoch = now.duration_since(UNIX_EPOCH).unwrap();
    println!("unix 时间戳约 {} 秒", since_epoch.as_secs());

    // 加一小时再减回来，差值应恰好是 3600 秒
    let later = now.checked_add(Duration::from_secs(3600)).unwrap();
    assert_eq!(later.duration_since(now).unwrap(), Duration::from_secs(3600));

    // 反过来减：时钟没有回拨时会报 SystemTimeError
    match now.duration_since(later) {
        Ok(d) => println!("差值 {:?}", d),
        Err(e) => println!("时钟被回拨了：{}", e),
    }

    // elapsed 同样是 Result，不能直接当 Duration 用
    match now.elapsed() {
        Ok(d) => println!("到现在已过 {:?}", d),
        Err(e) => println!("时钟倒拨：{:?}", e),
    }

    // 平台范围之外返回 None
    assert!(now.checked_add(Duration::MAX).is_none());
}
```

## 常见陷阱

1. **拿 `SystemTime` 测耗时**：校时会让差值变小甚至为负，基准测试结果不可信；测耗时用 [[time.Instant|Instant]]。
2. **把 `Result` 当 `Duration` 用**：`duration_since(...).unwrap()` 在时钟回拨的机器上会 panic，边界场景要显式处理 `Err`。
3. **以为标准库能格式化出「2025-01-01 08:00」**：标准库只给到自 `UNIX_EPOCH` 的时长，年月日换算要自己写或用第三方 crate。
4. **忽略平台年限**：可表示的年份范围随平台变化，跨平台代码不要假设能表示任意久远的时间。
5. **持久化后跨机器比较**：`SystemTime` 可以存盘和传输，但前提是两端时钟大致同步；需要严格顺序的场景改用递增序列号。

## 相关

- [[time|std::time 模块]]：本模块全部条目。
- [[time.Instant|Instant]]：单调时钟，测耗时的正确选择。
- [[time|std::time 模块]] 中的 `Duration`：与 `UNIX_EPOCH` 相减得到的结果类型。
- [[fs|std::fs]]：`Metadata` 的 `modified` / `created` 都是 `SystemTime`。
- [[11-错误处理|错误处理]]：如何优雅地处理 `SystemTimeError` 这类可失败操作。
