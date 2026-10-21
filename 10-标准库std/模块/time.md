---
title: "std::time"
type: std-模块
module: time
stable: "1.3.0"
unstable: false
tags:
  - std/模块
aliases:
  - time
一句话: 时间量化：Duration 表示时长、Instant 测单调流逝、SystemTime 读墙上时钟。
---

# std::time

> [!abstract] 一句话
> `std::time` 把「时间」拆成三件东西：`Duration` 是一段长度，`Instant` 是单调时钟读数，`SystemTime` 是墙上时钟读数。

## 模块简介

`std::time` 要回答的其实只有两个问题：**过了多久**、**现在几点**。前者用 `Duration` 表示（秒 + 纳秒，可以为 0，与任何时钟无关），后者必须从某一种时钟读数得来 —— 标准库为此提供了两种性质完全不同的时钟。

[[time.Instant|Instant]] 是单调非减的时钟，专门用来测量耗时：开始处记一个 `Instant::now()`，结束时再取一次，相减或调用 `elapsed()` 就得到 `Duration`。它不携带任何日历含义，也不保证跨进程有意义 —— 把它序列化到文件、再和另一个进程的 `Instant` 比较是没意义的，标准库也没有提供 `Instant` 与 `SystemTime` 之间的稳定互转。

[[time.SystemTime|SystemTime]] 是操作系统的墙上时钟，可以和文件修改时间、日志、其他进程对齐；`UNIX_EPOCH` 是它的参照原点（1970-01-01 UTC）。代价是它会**倒退**：NTP 校时、用户手动改表、虚拟机快照恢复都会让它跳动，所以 `SystemTime::duration_since` 返回 `Result`，方向反了不是「负时长」而是一个 `SystemTimeError`。

于是分工很清晰：测性能、算超时时长用 `Duration` + `Instant`；打时间戳、比文件新旧用 `SystemTime`。`Duration` 本身还是标准库的统一时间单位 —— `thread::sleep`、`mpsc::recv_timeout`、`Instant::checked_add` 收发的都是它。

## 快速上手

```rust
use std::thread;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

fn main() {
    // Duration：只是一段长度，和哪个时钟无关
    let timeout = Duration::from_millis(250);
    assert_eq!(timeout.as_secs(), 0);
    assert_eq!(timeout.subsec_millis(), 250);
    assert_eq!(
        Duration::from_secs(2) + Duration::from_millis(500),
        Duration::from_millis(2500)
    );

    // Instant：单调时钟，只适合量「过了多久」
    let start = Instant::now();
    thread::sleep(timeout);
    let elapsed = start.elapsed();
    assert!(elapsed >= timeout);
    println!("实际等待 {:?}", elapsed);

    // SystemTime：墙上时钟，用来和外部世界对齐
    let now = SystemTime::now();
    let since_epoch: Duration = now.duration_since(UNIX_EPOCH).unwrap();
    assert!(since_epoch.as_secs() > 1_600_000_000);
    println!("距 UNIX_EPOCH 已过 {} 秒", since_epoch.as_secs());

    // 方向反了不会得到负时长，而是 Err
    let earlier = UNIX_EPOCH - Duration::from_secs(10);
    assert!(earlier.duration_since(UNIX_EPOCH).is_err());
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[time.Instant|Instant]] | 单调时钟读数，只适合测量流逝的时间。 |
| `Duration` | 一段时间长度（秒 + 纳秒），与具体时钟无关。 |
| [[time.SystemTime|SystemTime]] | 系统墙上时钟读数，可与文件和进程交换。 |
| `UNIX_EPOCH` | `SystemTime` 的参照原点，1970-01-01 UTC。 |
| `Duration::from_secs` / `from_millis` / `from_nanos` | 由整数秒 / 毫秒 / 纳秒构造时长。 |
| `Duration::from_secs_f64` | 由浮点秒构造，负值或 NaN 返回 `Err`。 |
| `Duration::as_secs` / `as_millis` / `as_nanos` | 换算成整秒 / 毫秒 / 纳秒，后两者是 `u128`。 |
| `Duration::as_secs_f64` | 换算成浮点秒，便于打印与序列化。 |
| `Duration::checked_add` / `checked_sub` | 溢出或结果为负时返回 `None`。 |
| `Instant::now` / `elapsed` | 取当前读数 / 距该读数已过多久。 |
| `Instant::duration_since` | 与更早读数的差值，顺序反了得 0。 |
| `Instant::checked_duration_since` | 顺序反了返回 `None`，不把错误吞掉。 |
| `SystemTime::now` / `duration_since` | 取当前系统时间 / 与另一时刻的差值。 |
| `SystemTimeError` | 方向相反时返回的错误，`.duration()` 给出差值。 |

## 注意事项

> [!warning] `Instant` 不能存、不能比
> `Instant` 是不透明的平台相关值，只保证同一进程内单调非减。它不能序列化后跨进程比较，也不能和 `SystemTime` 互相转换。需要「某个时间点」就存 `SystemTime`，需要「耗时」才算 `Duration`。

> [!danger] `SystemTime` 会倒退
> 校时或改表后，`duration_since` 可能返回 `Err`。判断文件新旧、算运行时长时不要 `.unwrap()`，用 `unwrap_or_default()` 或转到 `Instant`。另外 `Duration` 的 `+` / `-` 在溢出或结果为负时 panic，稳妥写法是 `checked_add` / `saturating_sub`。

> [!tip] 打印与精度
> `{:?}` 会自动挑单位（`250.1ms`、`1.5s`），调试足够；要固定格式就用 `as_secs` / `as_millis` 自己拼。精度上限看平台，`Duration` 本身是纳秒粒度。浮点秒转 `Duration` 失败会返回 `TryFromFloatSecsError`。

## 相关

- [[thread|std::thread 模块]]：`sleep` 的入参、线程等待都围绕 `Duration`。
- [[thread.sleep|sleep]]：按 `Duration` 阻塞当前线程。
- [[fs|std::fs 模块]]：`Metadata::modified` 等时间戳的类型是 `SystemTime`。
- [[sync|std::sync 模块]]：`mpsc::recv_timeout` 这类带超时的等待都用 `Duration`。
- [[26-性能与优化|性能与优化]]：给代码计时用 `Instant`。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 6 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [[time.Duration|`Duration`]]
- [[time.Instant|`Instant`]]
- [[time.SystemTime|`SystemTime`]]
- [`SystemTimeError`](https://doc.rust-lang.org/std/time/struct.SystemTimeError.html)
- [`TryFromFloatSecsError`](https://doc.rust-lang.org/std/time/struct.TryFromFloatSecsError.html)

### 常量

- [`UNIX_EPOCH`](https://doc.rust-lang.org/std/time/constant.UNIX_EPOCH.html)

<!-- END AUTO ITEMS -->
