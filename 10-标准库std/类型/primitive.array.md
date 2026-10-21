---
title: "std::primitive::array"
type: std-条目
kind: 原始类型
module: primitive
slug: primitive.array
stable: "1.0.0"
tags:
  - std/类型
aliases:
  - Type array
一句话: 定长数组 `[T; N]`，长度是类型的一部分、在编译期确定，数据直接内联在栈或结构体里。
---

# `[T; N]`

> [!abstract] 一句话
> `[T; N]` 是**定长数组**：元素类型 `T` 相同、长度 `N` 是编译期常量，长度属于类型的一部分，所以 `[i32; 3]` 和 `[i32; 4]` 是两个不同的类型。

## 简介

- 布局：元素连续、无额外头部，总大小为 `N * size_of::<T>()`（`N == 0` 时大小为 0）；默认分配在栈上或直接内联在结构体里，**没有堆分配**。
- 长度：`N` 必须是编译期常量，可以写成常量、字面量或 const 泛型参数；因此不能在运行时用变量决定长度，需要变长时改用 [[vec.Vec|Vec]]。
- 字面量：逐个列举写 `[1, 2, 3]`；重复写 `[0u8; 4]`（值必须实现 `Copy`，或是常量表达式）；`[expr; 0]` 合法但**仍会求值 `expr`** 并立刻丢弃，注意副作用。
- 越界：`a[i]` 会做边界检查，越界直接 panic；不确定时用 `a.get(i)` 拿 `Option<&T>`。
- trait：长度任意（不限 32）的数组在元素类型满足条件时都实现了 `Copy`、`Clone`、`Debug`、`PartialEq`、`Eq`、`Ord`、`Hash`、`IntoIterator` 等；`IntoIterator` 支持按值迭代（`for x in arr`）、`&arr` 与 `&mut arr`。

与相邻类型的区别：[[primitive.slice|Type slice]]（`[T]`）是**编译期未知长度**的视图，`&[T; N]` 可以零成本转成 `&[T]`；`Vec<T>` 是堆上可增长的数组，能随时 `push`，代价是一次指针间接与容量管理。需要固定大小的缓冲区、查表、FFI 传数组时用 `[T; N]`，需要动态数量时用 `Vec<T>`。

```rust
fn main() {
    let a: [i32; 3] = [0; 3]; // 全部初始化为 0
    let b = [1, 2, 3]; // 逐个列举
    assert_eq!(a.len(), 3);
    assert_eq!(std::mem::size_of_val(&b), 12); // 3 * 4 字节，无额外开销
}
```

## 常用方法

### 映射与借用

| 方法 | 说明 |
| --- | --- |
| `map(f)` | 按顺序对每个元素应用 `f`，返回同长新数组。 |
| `each_ref()` | 逐个不可变借用，返回 `[&T; N]`。 |
| `each_mut()` | 逐个可变借用，返回 `[&mut T; N]`。 |

### 切片视图

| 方法 | 说明 |
| --- | --- |
| `as_slice()` | 返回覆盖整个数组的 `&[T]`，等价 `&s[..]`。 |
| `as_mut_slice()` | 返回覆盖整个数组的 `&mut [T]`。 |

> [!tip] 签名
> `pub fn map<F, U>(self, f: F) -> [U; N] where F: FnMut(T) -> U`
> `pub const fn each_ref(&self) -> [&T; N]`、`pub const fn each_mut(&mut self) -> [&mut T; N]`
> `pub const fn as_slice(&self) -> &[T]`、`pub const fn as_mut_slice(&mut self) -> &mut [T]`

## 示例

```rust
fn main() {
    // 数组里的元素可以逐元素改写
    let mut a: [i32; 3] = [0; 3];
    a[1] = 1;
    a[2] = 2;
    assert_eq!(a, [0, 1, 2]);

    // map 按值消费（i32 是 Copy，所以 a 仍可用），返回同长新数组
    let doubled = a.map(|x| x * 2);
    assert_eq!(doubled, [0, 2, 4]);

    // each_ref 得到一组引用，适合把数组元素分别交给多个函数
    let refs: [&i32; 3] = doubled.each_ref();
    assert_eq!(*refs[1], 2);

    // each_mut 得到一组可变引用，逐个改写
    let m = a.each_mut();
    *m[0] = 100;
    assert_eq!(a[0], 100);

    // as_slice 之后可以调用任何切片方法
    let s: &[i32] = a.as_slice();
    assert_eq!(s.iter().sum::<i32>(), 103);
    let m: &mut [i32] = a.as_mut_slice();
    m[1] = 200;
    assert_eq!(a, [100, 200, 2]);
}
```

遍历与定长的边界：

```rust
fn sum<const N: usize>(data: [i32; N]) -> i32 {
    // 长度写在类型里，所以这层循环边界是编译期已知的
    let mut total = 0;
    for x in data {
        total += x;
    }
    total
}

fn main() {
    assert_eq!(sum([1, 2, 3]), 6);
    assert_eq!(sum([1, 2, 3, 4]), 10);
    assert_eq!(sum([]), 0); // 空数组是合法的，类型为 [i32; 0]

    // 按值迭代会移动/复制数组，按引用迭代则不消耗它
    let arr = ["a", "b"];
    let mut joined = String::new();
    for w in &arr {
        joined.push_str(w);
    }
    assert_eq!(joined, "ab");
    assert_eq!(arr.len(), 2); // arr 仍可用

    // 越界用 get 而不是下标
    assert_eq!(arr.get(5), None);
}
```

## 常见陷阱

1. **长度写进类型，函数无法通用**：`fn f(a: [i32; 3])` 只接受长度 3 的数组；要接受任意长度改用泛型 `fn f<const N: usize>(a: [i32; N])` 或直接收切片 `&[i32]`。
2. **大数组撑爆栈**：`[0u8; 1_000_000]` 默认在栈上分配，容易 stack overflow；改用 `Vec` 或 `Box<[T]>`。
3. **`[expr; N]` 要求 `Copy`**：非 `Copy` 类型不能用重复语法初始化，可以 `std::array::from_fn(|i| ...)` 逐个生成。
4. **`[expr; 0]` 仍会求值**：长度 0 也会执行一次 `expr` 再丢弃，带副作用时切勿依赖「不执行」。
5. **直接下标会 panic**：`a[5]` 越界即 panic，处理外部索引时用 `get` / `get_mut` 判断。

## 相关

- [[primitive|std::primitive 模块]]：`array`、`slice`、`tuple` 等原始类型页的入口。
- [[primitive.slice|Type slice]]：`[T; N]` 可以零成本借用为 `[T]`，方法表第二组就来自切片视图。
- [[primitive.tuple|Type tuple]]：另一种定长聚合，但允许多个不同类型。
- [[vec.Vec|Vec]]：长度在运行时可变时的替代方案。
- [[03-变量与数据类型|变量与数据类型]]：数组、切片、元组的语法对比。
