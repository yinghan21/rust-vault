---
title: "std::convert::Into"
type: std-条目
kind: 特质
module: convert
slug: convert.Into
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - Into
一句话: 消耗 self 的值到值转换，通常不手写而由 From 的 blanket 实现免费提供。
---

# Into

> [!abstract] 一句话
> `Into<T>` 是「把自己变成 `T`」的消耗式转换：`.into()` 会吃掉原值。它几乎总是由 `From` 的 blanket 实现自动带来的，因此实践中应当实现 `From`，用 `Into` 只作调用侧和泛型边界。

## 简介

`Into` 只定义一件事：`fn into(self) -> T`。注意参数是 `self` 而不是 `&self` —— 转换会把原值用掉，调用之后原来的变量就不存在了。这与 [[convert.AsRef|AsRef]] 的「借出一份引用」形成鲜明对比。

它本身几乎没有「实现价值」。标准库里有一条 blanket 实现：

```text
impl<T, U> Into<U> for T where U: From<T>
```

任何 `U: From<T>` 都会自动获得 `T: Into<U>`。所以为一个自定义类型手写 `impl Into<...>` 除了少数历史原因，都是多余且有害的：手写 `Into` 会与这条 blanket 实现抢位，导致你再也无法为它实现 `From`（E0119）。

`Into` 的价值体现在三个地方：

- **调用侧**：`.into()` 是写起来最顺的转换写法，目标类型由上下文推断。
- **泛型边界**：`fn f(x: impl Into<String>)` 接受一切「能变成 `String`」的类型，比 `T: From<X>` 更宽松。
- **标准库签名**：`Iterator::collect` 之外的很多 API 都用 `impl Into<T>` 放宽入参，比如 `SocketAddr`、`Box<str>` 的构造。

编译器不会替你自动调用 `into`：它不像 `Deref` 那样隐式插入，也不像 `Copy` 那样隐式复制。`?` 运算符用的也是 `From` 而不是 `Into`，这点常被记反。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `into()` | 消耗 `self`，返回转换后的 `T`。 |

签名是 `fn into(self) -> T`。实际上你几乎不会实现它 —— 实现 [[convert.From|From]]，让标准库把 `Into` 送你。只有在「源类型在本 crate、目标类型在外部 crate、且老编译器不支持 `From`」这类遗留场景才考虑手写。

`Into` **不允许失败**：可能失败的转换要用 `TryInto`（由 `TryFrom` 免费带来）。

## 与相邻 trait 的关系

| 维度 | `From` | `Into` | `TryFrom` / `TryInto` |
| --- | --- | --- | --- |
| 方向 | 从 `T` 造 `Self` | 把自己变成 `T` | 同左，但可失败 |
| 推荐实现 | 是 | 否（自动获得） | 是 |
| 返回类型 | `Self` | `T` | `Result<Self, Error>` |
| 泛型边界首选 | 较少 | 更宽松，首选 | `TryInto` |

`From` 与 `Into` 是同一枚硬币的两面，标准库用 blanket 实现把它们锁在一起。这个设计的好处是「实现一次，两种写法都能用」；代价是你不能在两者之间自由选择 —— 已经 `impl From` 的类型再 `impl Into` 会冲突。

## 示例

### 目标类型由上下文推断

```rust
fn main() {
    // 标注了类型，编译器才知道要 into 成什么
    let s: String = "42".into();
    assert_eq!(s, "42");

    let n: u32 = 7u8.into();
    assert_eq!(n, 7);

    // 完全靠推断：collect 的目标类型决定元素要变成什么
    let chars: Vec<char> = "abc".chars().collect();
    let strings: Vec<String> = chars.into_iter().map(|c| c.to_string()).collect();
    assert_eq!(strings, ["a", "b", "c"]);
}
```

### 泛型边界：`impl Into<T>` 放宽入参

```rust
fn label(value: impl Into<String>) -> String {
    format!("[{}]", value.into())
}

// 消耗式迭代：Vec 通过 IntoIterator 被吃掉，不再保留所有权
fn sum_all(values: impl IntoIterator<Item = u32>) -> u32 {
    values.into_iter().sum()
}

fn main() {
    assert_eq!(label("ok"), "[ok]");
    assert_eq!(label(String::from("ok")), "[ok]");

    let parts = vec![1u32, 2, 3];
    assert_eq!(sum_all(parts), 6);
}
```

### 手写 `Into` 的代价

```rust
struct Wrapper(Vec<i32>);

// 直接实现 Into 是合法的，但从此无法再实现 From<Wrapper> for Vec<i32>，
// 也就失去了「一份代码、两个方向」的便利
impl Into<Vec<i32>> for Wrapper {
    fn into(self) -> Vec<i32> {
        self.0
    }
}

fn main() {
    let v: Vec<i32> = Wrapper(vec![1, 2, 3]).into();
    assert_eq!(v, [1, 2, 3]);
}
```

### 优先写 `From`，让 `Into` 免费到来

```rust
#[derive(Debug, PartialEq)]
struct Port(u16);

impl From<u16> for Port {
    fn from(value: u16) -> Self {
        Port(value)
    }
}

fn main() {
    // 左边用 From，右边用自动获得的 Into
    let a = Port::from(8080);
    let b: Port = 8080u16.into();
    assert_eq!(a, b);
}
```

## 常见陷阱

1. **同时实现 `From` 和 `Into`**：E0119 冲突。写了 `From` 就不要再碰 `Into`，否则两个实现会为同一对类型竞争。
2. **忘记 `.into()` 会消耗原值**：调用后原变量不可用；只想借用请用 `as_ref()`、`to_string()`、`to_owned()`。
3. **`.into()` 出现歧义**：目标类型无法推断时报 E0283，需要显式标注 `let x: T = v.into();` 或改用 `T::from(v)`。
4. **以为 `?` 用的是 `Into`**：`?` 内部走 `From::from`，所以只实现 `Into` 的错误类型无法参与自动转换。
5. **用 `Into` 表达可能失败的转换**：语义上它必须成功，失败要用 `TryInto`，否则只能 panic。
6. **给泛型写 `T: From<X>` 边界**：会挡住只实现了 `Into` 的类型，应该写 `T: Into<X>`。

## 相关

- [[convert|std::convert 模块]]：转换特质总览。
- [[convert.From|From]]：`Into` 的真正实现位置，优先实现它。
- [[convert.TryFrom|TryFrom]]、`TryInto`：可失败转换的对应物。
- [[convert.AsRef|AsRef]]：借用式转换，不消耗所有权。
- [[iter.IntoIterator|IntoIterator]]：名字相似但语义不同，同样靠 blanket 实现衔接。
- [[14-泛型|泛型]]：`impl Into<T>` 这类入参写法的背景。
