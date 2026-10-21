---
title: "std::thread::spawn"
type: std-条目
kind: 函数
module: thread
slug: thread.spawn
stable: "1.0.0"
tags:
  - std/并发
aliases:
  - spawn
一句话: 新建一个线程执行闭包，返回可 join 的 JoinHandle；闭包必须 move 且为 'static。
---

# `spawn`

> [!abstract] 一句话
> `std::thread::spawn` 把一个闭包丢到新线程里运行，立刻返回 `JoinHandle<T>`。这个句柄既能用 `join` 等它结束并取回返回值，也能直接丢掉，让线程「放飞」（detach）。

## 简介

线程是「并行执行一段代码」的最小单位。`spawn` 的用法只有一句：传一个闭包，拿一个句柄。新线程与你当前的代码同时跑，谁先谁后由操作系统调度决定。

关键在闭包的两个约束。其一是 `move`：闭包按值捕获它用到的变量，把所有权整体搬进新线程，这样两个线程不会同时引用同一份数据。其二是 `'static`：线程的生命周期不受栈帧约束，所以不能捕获一个马上就要销毁的借用（比如 `&local_string`），必须让闭包拥有数据本身——要共享就用 [[sync.Arc|Arc]] 再配 [[sync.Mutex|Mutex]]。

`JoinHandle::join` 返回 `Result<T, Box<dyn Any + Send>>`：正常结束是 `Ok(闭包返回值)`，子线程 panic 过就是 `Err(panic 载荷)`。把 `JoinHandle` 直接 drop 会隐式 detach，线程继续跑但你再也没法等它——程序结束也不会为它等待，所以「要么 join，要么明确 detach」。

## 签名与参数

```text
pub fn spawn<F, T>(f: F) -> JoinHandle<T>
where
    F: FnOnce() -> T + Send + 'static,
    T: Send + 'static,
```

| 参数 | 说明 |
| --- | --- |
| `f` | 线程要执行的闭包，实现 `FnOnce() -> T`。 |
| 返回 `JoinHandle<T>` | 线程句柄，`join()` 等待结束并取回 `T`。 |

- `FnOnce()`：闭包只需能被调用一次，所以可以把捕获的值 `move` 进线程。
- `Send`：闭包捕获的数据必须能安全地跨线程转移；`Rc`、裸指针不行，[[sync.Arc|Arc]]、`String`、`Vec` 可以。
- `'static`：捕获的东西不能含短生命周期借用，否则编译器会报 `may not live long enough`。
- `T: Send`：闭包的返回值也要能跨线程送回 `join` 那一侧。

想设置线程名或栈大小，用 `std::thread::Builder::new().name(..).stack_size(..).spawn(..)`；`spawn` 等价于用默认参数的 `Builder`。

## 示例

### 最基本的用法：join 取回结果

```rust
use std::thread;

fn main() {
    let handle = thread::spawn(|| {
        let mut sum = 0u64;
        for i in 1..=100 {
            sum += i;
        }
        sum
    });

    // join 返回 Result：子线程 panic 时是 Err
    let total = handle.join().unwrap();
    assert_eq!(total, 5050);
    println!("子线程计算结果: {total}");
}
```

### move 闭包：把所有权搬进线程

```rust
use std::thread;

fn main() {
    let data = vec![1, 2, 3];

    // move 让闭包拥有 data，主线程之后不能再用它
    let handle = thread::spawn(move || data.iter().sum::<i32>());
    let sum = handle.join().unwrap();
    assert_eq!(sum, 6);
    println!("sum = {sum}");

    // 不以 move 捕获借用会编译失败；共享数据请用 Arc
    let shared = std::sync::Arc::new(String::from("hello"));
    let h2 = {
        let shared = std::sync::Arc::clone(&shared);
        thread::spawn(move || shared.len())
    };
    assert_eq!(h2.join().unwrap(), 5);
    println!("主线程仍可用: {shared}");
}
```

## 常见陷阱

1. **不加 `move` 就借用局部变量**：闭包按引用捕获会让线程活过栈帧，编译报 `may not live long enough`，对策是加 `move` 并交出所有权。
2. **用 `Rc` 跨线程**：`Rc` 不是 `Send`，会直接编译失败，对策是换 [[sync.Arc|Arc]]。
3. **drop 了 `JoinHandle` 还指望线程被等**：drop 只是 detach，主线程结束进程就退出，对策是显式 `join`。
4. **忽略 `join` 的 `Err`**：子线程 panic 不会传播到主线程，只会体现在 `Err` 里，对策是至少记录一下。
5. **以为 `spawn` 会排队执行**：线程是立即并发启动的，共享可变状态必须加锁，顺序要靠 channel 或 join 保证。

## 相关

- [[thread|std::thread 模块]]：`JoinHandle`、`Builder`、`scope` 都在这里。
- [[thread.sleep|sleep]]：让当前线程睡一会儿，常与线程一起演示调度。
- [[21-并发编程|并发编程]]：线程、消息传递与共享状态的完整讲法。
- [[sync.Arc|Arc]]、[[sync.Mutex|Mutex]]：跨线程共享数据的标准组合。
- [[marker.Send|Send]]：`spawn` 要求闭包与返回值满足这个标记特质。
