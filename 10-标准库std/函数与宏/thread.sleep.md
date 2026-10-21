---
title: "std::thread::sleep"
type: std-条目
kind: 函数
module: thread
slug: thread.sleep
stable: "1.4.0"
tags:
  - std/并发
  - std/时间
aliases:
  - sleep
一句话: 让当前线程至少睡眠指定时长，会阻塞本线程，绝不会少睡但可能多睡。
---

# `sleep`

> [!abstract] 一句话
> `std::thread::sleep(dur)` 把**当前线程**挂起至少 `dur` 这么久。它只影响本线程，期间 CPU 让给别人；醒来时间可能比要求的长，但不会短。

## 简介

`sleep` 是最简单的「等一会儿」：限流、重试退避、轮询间隔、给日志一点刷盘时间，都用它。它接受 `Duration`，所以时长表达很直观：`Duration::from_millis(10)`、`Duration::from_secs(1)`。

它的语义是「**至少**」而不是「恰好」：操作系统调度、时钟精度、Unix 上被信号打断都会让实际睡眠变长。因此 `sleep` 适合做「别太频繁」，不适合做「精确定时」——测时间请用 [[time.Instant|Instant]] 做差。

`sleep` 是**阻塞**调用，会占住整个线程。在 async 函数里直接调它会把执行器卡住，其他任务全部停摆；异步代码应该用运行时的定时器（例如异步运行时的 `sleep`）而不是这个函数。

## 签名与参数

```text
pub fn sleep(dur: Duration)
```

| 参数 | 说明 |
| --- | --- |
| `dur` | 要睡眠的时长，`Duration::ZERO` 表示只让出一次。 |
| 返回 `()` | 没有返回值，也不会失败。 |

- 没有返回值也不报错：睡眠不会「失败」，最多是被打断后重新睡够。
- 不精确：传入的时长是下界。平台不支持纳秒精度时，会向上取整到能表达的最小粒度。
- 不可取消：睡下去之后没有外部手段提前唤醒，需要可中止的等待请用 channel 的 `recv_timeout` 或条件变量。

## 示例

```rust
use std::time::{Duration, Instant};

fn main() {
    let pause = Duration::from_millis(10);
    let start = Instant::now();

    std::thread::sleep(pause);

    // 只会睡得更久，不会更短
    assert!(start.elapsed() >= pause);
    println!("实际等待: {:?}", start.elapsed());
}
```

用 `sleep` 做重试退避时，时长往往随失败次数增长：

```rust
use std::time::Duration;

fn main() {
    let mut delay = Duration::from_millis(10);
    let mut attempts = 0;

    while attempts < 3 {
        attempts += 1;
        println!("第 {attempts} 次尝试失败，等待 {:?}", delay);
        std::thread::sleep(delay);
        // 下次等更久，但设个上限，避免指数爆炸
        delay = std::cmp::min(delay * 2, Duration::from_millis(100));
    }

    assert_eq!(attempts, 3);
}
```

## 常见陷阱

1. **在 async 函数里调用它**：`sleep` 会阻塞整个执行器线程，其他任务全部卡住，对策是改用异步运行时的定时器。
2. **把它当精确计时器**：实际睡眠只会更长，用 `sleep` 控制节奏时不要把间隔算进业务耗时，对策是用 [[time.Instant|Instant]] 测量真实耗时。
3. **期望能被提前唤醒**：`sleep` 无法取消，线程只能睡满，对策是用带超时的 channel 接收或条件变量等待。
4. **以为 `sleep(Duration::ZERO)` 是空操作**：它仍会触发一次让出与调度，对策是别把它放进高频热路径。
5. **在持锁时睡眠**：锁会被一直占着，其他线程全被拖住，对策是先释放锁再睡。

## 相关

- [[thread|std::thread 模块]]：线程相关的内容都在这里。
- [[thread.spawn|spawn]]：开一个线程去睡，主线程继续干活。
- [[time|std::time 模块]]：`Duration` 与 `Instant` 都定义在这里。
- [[time.Instant|Instant]]：验证「至少睡够」时的计时工具。
- [[21-并发编程|并发编程]]：限流、退避与线程调度的整体视角。
