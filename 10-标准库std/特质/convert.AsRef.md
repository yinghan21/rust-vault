---
title: "std::convert::AsRef"
type: std-条目
kind: 特质
module: convert
slug: convert.AsRef
stable: "1.0.0"
tags:
  - std/特质
aliases:
  - AsRef
一句话: 一次廉价的引用到引用转换，让函数参数能同时接受 String、&str 与 PathBuf。
---

# AsRef

> [!abstract] 一句话
> `AsRef<T>` 表示「可以廉价地把自己当成 `&T` 看」：`as_ref` 只做引用转换，不分配、不做 I/O、不会失败。函数签名里写 `impl AsRef<Path>`，就能同时接受 `&str`、`String`、`PathBuf`。

## 简介

定义是 `pub trait AsRef<T: ?Sized> where T: ?Sized { fn as_ref(&self) -> &T; }`。注意 `T` 允许 `?Sized`，因为最常见的目标都是动态大小类型：`str`、`[u8]`、`Path`、`OsStr`。

它解决的问题是**参数宽容度**。`std::fs::File::open` 的签名是 `fn open<P: AsRef<Path>>(path: P) -> io::Result<File>`，所以下面几种写法都不用你手动转换、也不产生额外分配：

```text
open("config.toml")          // &str
open(String::from("a.txt"))  // String
open(Path::new("b.txt"))     // &Path
open(PathBuf::from("c.txt")) // PathBuf
```

契约有两条：**必须廉价**，**必须不失败**。前者意味着不能做格式化、解析或分配；后者意味着不能返回 `Option`/`Result`，若转换可能失败，就该另写一个返回 `Result` 的专用方法。`AsRef` 与 `AsMut` 成对，后者给的是 `&mut T`。

一个类型可以有多个 `AsRef` 目标，这正是歧义的来源：`String` 同时实现 `AsRef<str>`、`AsRef<[u8]>`、`AsRef<Path>`、`AsRef<OsStr>`；`str` 也实现 `AsRef<[u8]>` 与 `AsRef<Path>`。所以 `s.as_ref()` 单独出现时编译器常常不知道要哪一个，需要类型标注。

与 `Deref` 的分工：解引用强制转换（`let r: &i32 = &boxed;`）由 `Deref` 驱动，是编译器自动插入的；`AsRef` 是显式调用，用于泛型 API 里表达「你可以给我任何能变成 `&T` 的东西」。标准库对 `Box<T>` 两者都提供，所以 `&x` 往往比 `x.as_ref()` 更简洁。

## 必须实现

| 方法 | 说明 |
| --- | --- |
| `as_ref()` | 借出内部的 `&T`，不做转换、不分配。 |

签名是 `fn as_ref(&self) -> &T`。实现必须直接返回内部那个 `T` 的引用，返回的生命周期绑定在 `&self` 上。

## 提供的方法

无。`AsRef` 只有 `as_ref` 一个关联函数，没有默认实现，也没有其他辅助方法。

## 与相邻 trait 的关系

`AsRef` 与 [[borrow.Borrow|Borrow]] 的签名一模一样，区别在**语义**：

| 维度 | `AsRef<T>` | `Borrow<T>` |
| --- | --- | --- |
| 含义 | 可以「当作」`&T` 使用 | 就是同一份数据的另一种规范形态 |
| 行为契约 | 只要求廉价、不失败 | 还要求 `Eq`/`Ord`/`Hash` 与借出形式一致 |
| 目标数量 | 可以有多个互不相干的目标 | 通常只有一个规范目标 |
| 自反实现 | 没有 `impl<T> AsRef<T> for T`，靠 `&T` 转发 | 有 `impl<T: ?Sized> Borrow<T> for T` |
| 典型用途 | 放宽函数参数 | 容器键查找、写时克隆 |
| 用于 `HashMap::get` | 不行，缺少一致性保证 | 正确，`K: Borrow<Q>` 就是为它设计的 |

一句话记忆：`AsRef` 说「我能给你一个 `&T`」，`Borrow` 说「我就是那个 `T` 的另一种形态，连哈希和相等都一致」。所以 `HashMap<String, V>` 能用 `&str` 查找靠的是 `Borrow`，不是 `AsRef`。

与 [[convert.From|From]] 相比：`From<&T> for U` 可以分配、可以失败（用 `TryFrom`），而 `AsRef` 只借不建，返回的是引用而非新值。若转换有成本，官方建议实现 `From<&T>` 或写专用函数，而不是塞进 `AsRef`。

## 示例

### 用泛型参数接受多种输入

```rust
fn print_bytes<B: AsRef<[u8]>>(data: B) {
    // 无论传进来的是 &str、String 还是 Vec<u8>，这里都拿到 &[u8]
    println!("{:?}", data.as_ref());
}

fn main() {
    print_bytes("hello");
    print_bytes(String::from("hi"));
    print_bytes(vec![1u8, 2, 3]);
    print_bytes([9u8; 2]);
}
```

### 多个目标需要类型标注

```rust
fn main() {
    let s = String::from("rust");

    let as_str: &str = s.as_ref();
    let as_bytes: &[u8] = s.as_ref();

    assert_eq!(as_str, "rust");
    assert_eq!(as_bytes, b"rust");

    // 不标注就报错：String 同时实现 AsRef<str>、AsRef<[u8]> 等多个目标
    // let ambiguous = s.as_ref();
}
```

### 自定义实现与泛型边界

```rust
struct Name(String);

impl AsRef<str> for Name {
    fn as_ref(&self) -> &str {
        &self.0
    }
}

fn greet<N: AsRef<str>>(name: N) -> String {
    format!("你好，{}", name.as_ref())
}

fn main() {
    assert_eq!(greet(Name("小明".to_string())), "你好，小明");
    assert_eq!(greet("世界"), "你好，世界");
}
```

### Box 上 as_ref 与 & 等价

```rust
fn main() {
    let boxed = Box::new(5i32);

    // 解引用强制转换，通常这样写就够了
    let by_ref: &i32 = &boxed;
    // 显式调用 AsRef
    let by_as_ref: &i32 = boxed.as_ref();

    assert_eq!(*by_ref, *by_as_ref);
}
```

## 常见陷阱

1. **`x.as_ref()` 类型推断失败**：`String`、`PathBuf` 都有多个 `AsRef` 目标。标注 `let s: &str = ...`，或写全 `AsRef::<str>::as_ref(&x)`，或干脆用 `&x`。
2. **在 `AsRef` 里做昂贵操作**：格式化、拼接、加锁都违反「cheap」约定；调用方以为它免费却在热循环里付出代价。
3. **拿 `AsRef` 去做容器键查找**：`HashMap::get` 的边界是 `K: Borrow<Q>`，写 `AsRef` 编译不过；就算自定义一个查找函数，也缺少哈希一致性保证。
4. **误以为存在自反实现**：`AsRef` 没有 `impl<T> AsRef<T> for T`，泛型里不能假设 `T: AsRef<T>`；只有 `&T` 会通过 `impl<T, U> AsRef<U> for &T where T: AsRef<U>` 逐层转发。
5. **实现目标写错导致孤儿规则/重复实现**：同一类型对同一目标只能实现一次 `AsRef`，`impl AsRef<str>` 与 `impl AsRef<[u8]>` 可以共存，重复则冲突。
6. **以为 `as_ref` 能改值**：它只给 `&T`，要可变借用得用 `AsMut` 与 `as_mut`。

## 相关

- [[convert|std::convert 模块]]：`AsRef` 所属模块。
- [[borrow.Borrow|Borrow]]：签名相同、语义更强的「按另一种形态借用」。
- [[convert.From|From]]：可能产生新值的转换，与只借不建的 `AsRef` 相对。
- [[string.String|String]]：同时实现多个 `AsRef` 目标的典型。
- [[primitive.str|str]]：最常见的 `AsRef` 目标类型。
- [[path.Path|Path]]：`File::open` 一类 API 用它做参数边界。
