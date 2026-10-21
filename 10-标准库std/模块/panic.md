---
title: "std::panic"
type: std-模块
module: panic
stable: "1.9.0"
unstable: false
tags:
  - std/模块
  - std/错误
aliases:
  - panic
一句话: panic 的运行时支持：捕获展开、换掉 panic hook、读取 panic 位置与 payload、选择 unwind 还是 abort。
---

# std::panic

> [!abstract] 一句话
> `std::panic` 管的是 panic 发生**之后**的运行时行为：跑不跑 hook、能不能被 `catch_unwind` 抓住、payload 里装了什么、以及要不要干脆直接 abort。

## 模块简介

Rust 把错误分成两条路：可恢复的走 `Result`，不可恢复的走 `panic!`。`Result` 怎么处理大家都知道，但 panic 之后到底发生了什么，很多人只停留在「打印一行红字然后退出」。实际上 panic 的流程是固定的三步：

1. 先跑 **panic hook**，默认 hook 把消息、文件、行号和可选的 backtrace 打到 stderr；
2. 然后 **展开栈**（unwind），沿途执行局部变量的析构函数；如果编译时选了 `panic = "abort"`，这一步换成直接终止进程；
3. 如果这层 panic 被 `catch_unwind` 接住，进程继续跑；否则一路展开到 `main` 之外，进程以非零码退出。

这个模块把上面每一环都开了口子。`set_hook` / `take_hook` / `update_hook` 改第 1 步，最典型的用法是把 panic 压成一行结构化日志，测试框架和服务端兜底都是这么干的。`catch_unwind` 与 `resume_unwind` 控制第 3 步：前者在边界处接住 panic 并交回 `Err`，后者把已捕获的 payload 重新抛出。`panic_any` 允许抛出任意 `'static` 类型的 payload，`PanicHookInfo` 与 `Location` 则让 hook 读到位置、消息和「这次能不能展开」。

还有一组偏底层的开关：`always_abort` 让之后所有 panic 直接 abort，`abort_on_unwind` 包一个闭包、它一旦展开就 abort，`set_backtrace_style` / `get_backtrace_style` 决定默认 hook 要不要抓 backtrace。`UnwindSafe` / `RefUnwindSafe` 是编译器用来判断「跨过 `catch_unwind` 边界安不安全」的标记 trait，`AssertUnwindSafe` 是你手工签的保证书。

日常业务代码基本碰不到这个模块，它的真实用户是：测试框架（接住用例失败）、FFI 与插件边界（绝不能让 panic 穿过去）、线程池（一个任务 panic 不该拖垮整个池）、以及需要自定义崩溃输出的服务端。

## 快速上手

```rust
use std::panic::{self, AssertUnwindSafe};

fn main() {
    // 1. 换掉默认 hook：把 panic 信息压成一行，方便日志系统收集
    let default_hook = panic::take_hook();
    panic::set_hook(Box::new(|info| {
        let place = info
            .location()
            .map(|loc| loc.to_string())
            .unwrap_or_else(|| "未知位置".to_string());
        let message = if let Some(s) = info.payload().downcast_ref::<&str>() {
            (*s).to_string()
        } else if let Some(s) = info.payload().downcast_ref::<String>() {
            s.clone()
        } else {
            "非字符串 payload".to_string()
        };
        eprintln!("[panic] {place}: {message}");
    }));

    // 2. 捕获展开：这次 panic 不再终止进程
    let caught = panic::catch_unwind(|| {
        panic!("演示用的 panic");
    });
    assert!(caught.is_err());

    // 3. 借用了局部可变状态时，要显式承诺「即使 panic 也不会破坏它」
    let mut counter = 0;
    let caught = panic::catch_unwind(AssertUnwindSafe(|| {
        counter += 1;
        counter
    }));
    assert_eq!(caught.unwrap(), 1);

    // 4. 自定义 payload：类型随意，只要是 'static + Send
    let caught = panic::catch_unwind(|| panic::panic_any(42u32));
    let payload = caught.unwrap_err();
    assert_eq!(*payload.downcast::<u32>().unwrap(), 42);

    // 5. 收工，把默认 hook 装回去
    panic::set_hook(default_hook);

    println!("counter = {counter}");
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| `catch_unwind` | 在边界处接住展开，捕获成功时返回 `Err(payload)`。 |
| `resume_unwind` | 重新抛出已捕获的 payload，且不触发 hook。 |
| `panic_any` | 抛出一个任意 `'static` 类型的 payload。 |
| `set_hook` | 注册自定义 panic hook，替换当前已有的 hook。 |
| `take_hook` | 取走当前 hook 并装回默认 hook。 |
| `update_hook` | 原子地「先做自己的事、再调用旧 hook」，适合链式包装。 |
| `PanicHookInfo` | hook 拿到的信息：位置、payload、能否展开。 |
| `Location` | panic 发生的文件、行号、列号。 |
| `AssertUnwindSafe` | 手工声明某个值跨 `catch_unwind` 是安全的。 |
| `UnwindSafe` / `RefUnwindSafe` | 标记 trait，描述类型能否安全跨展开边界。 |
| `always_abort` | 之后所有 panic 直接 abort，不跑 hook 也不展开。 |
| `abort_on_unwind` | 闭包一旦展开就 abort，不让 panic 往回传播。 |
| `get_backtrace_style` / `set_backtrace_style` | 读取 / 配置默认 hook 是否打印 backtrace。 |
| `BacktraceStyle` | 上面两个函数的配置枚举。 |
| `PanicInfo` | `PanicHookInfo` 的旧名别名，新代码不要用。 |

## 注意事项

> [!warning] panic 之后内存安全，逻辑状态不一定安全
> 展开会正常执行析构，不会泄漏到 `unsafe` 意义上，但**业务状态**可能已经改了一半：字段写了一个、消息发了一条、锁处于半更新状态。`catch_unwind` 接住之后继续使用这些状态，需要你自己判断能否恢复——这也正是 `UnwindSafe` 存在的原因。

> [!danger] 不要让 panic 穿过 FFI 边界
> 默认 `extern "C"` 函数里发生 panic 会直接 abort 进程（旧版本上是未定义行为）。跨语言边界前用 `catch_unwind` 包住，把结果翻译成错误码返回。另外，在 `panic = "abort"` 的 profile 下 `catch_unwind` 抓不到任何东西：panic 会直接终止进程。

> [!tip] payload 要按类型试探，别假定是 `&str`
> payload 的类型是 `Box<dyn Any + Send>`：`panic!("文本")` 得到 `&str`，`panic!("{}", s)` 得到 `String`，`panic_any(x)` 得到 `x` 的类型。统一处理时依次 `downcast_ref` 试探，最后再兜底。

## 相关

- [[11-错误处理|错误处理]]：`Result` 与 panic 的分工，什么时候该用哪个。
- [[macro.panic|panic!]]：触发 panic 的宏本体，含格式化参数。
- [[backtrace|std::backtrace]]：手动捕获 backtrace。
- [[thread|std::thread]]：子线程 panic 只会影响该线程，`join` 会拿到 `Err`。
- [[process|std::process]]：`abort` 与 `exit` 才是终止进程的另外两条路。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 17 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`AssertUnwindSafe`](https://doc.rust-lang.org/std/panic/struct.AssertUnwindSafe.html)
- [`Location`](https://doc.rust-lang.org/std/panic/struct.Location.html)
- [`PanicHookInfo`](https://doc.rust-lang.org/std/panic/struct.PanicHookInfo.html)

### 枚举

- [`BacktraceStyle`](https://doc.rust-lang.org/std/panic/enum.BacktraceStyle.html)

### 特质

- [`RefUnwindSafe`](https://doc.rust-lang.org/std/panic/trait.RefUnwindSafe.html)
- [`UnwindSafe`](https://doc.rust-lang.org/std/panic/trait.UnwindSafe.html)

### 类型别名

- [`PanicInfo`](https://doc.rust-lang.org/std/panic/type.PanicInfo.html)

### 函数

- [`catch_unwind`](https://doc.rust-lang.org/std/panic/fn.catch_unwind.html)
- [`panic_any`](https://doc.rust-lang.org/std/panic/fn.panic_any.html)
- [`resume_unwind`](https://doc.rust-lang.org/std/panic/fn.resume_unwind.html)
- [`set_hook`](https://doc.rust-lang.org/std/panic/fn.set_hook.html)
- [`take_hook`](https://doc.rust-lang.org/std/panic/fn.take_hook.html)
- [`abort_on_unwind`](https://doc.rust-lang.org/std/panic/fn.abort_on_unwind.html)
- [`always_abort`](https://doc.rust-lang.org/std/panic/fn.always_abort.html)
- [`get_backtrace_style`](https://doc.rust-lang.org/std/panic/fn.get_backtrace_style.html)
- [`set_backtrace_style`](https://doc.rust-lang.org/std/panic/fn.set_backtrace_style.html)
- [`update_hook`](https://doc.rust-lang.org/std/panic/fn.update_hook.html)

<!-- END AUTO ITEMS -->
