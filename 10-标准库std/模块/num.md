---
title: "std::num"
type: std-模块
module: num
stable: "1.0.0"
unstable: false
tags:
  - std/模块
aliases:
  - num
一句话: "数值类型补充：NonZero 非零整数、Saturating/Wrapping 算术包装与解析错误类型。"
---

# std::num

> [!abstract] 一句话
> `std::num` 不是数学库，而是给内建数值类型补的类型：保证非零的 `NonZero` 系列、把溢出策略写进类型的 `Saturating`/`Wrapping`，以及解析与转换的错误类型。

## 模块简介

数学函数（`powf`、`sin`、`gcd`、`checked_add`……）都在内建类型自己身上，不在这个模块里。`std::num` 提供的是一批**独立类型**，用来在类型层面表达数值的性质。

其中最重要的是 `NonZero` 系列：`NonZeroU8` … `NonZeroUsize`、`NonZeroI8` … `NonZeroIsize`，共十二个类型别名，底层是 `NonZero<T>`。它们保证值不为零，因此只能通过 `NonZeroU32::new(x) -> Option<NonZeroU32>` 构造（`0` 得到 `None`），`get()` 零成本取回底层整数。价值有两点：一是把「这个数不会当分母 / 不会是零地址」写进签名，省掉重复检查；二是**空指针优化**——`Option<NonZeroU32>` 与 `u32` 一样大，编译器用全零位表示 `None`，所以 `fn f() -> Option<NonZeroU32>` 不花额外空间。

第二类是算术包装：`Saturating<T>` 让溢出时钳到类型边界（`250u8 + 10u8` 得 `255`），`Wrapping<T>` 让溢出时回绕（得 `4`）。它们的意义是把溢出策略从「取决于编译模式」变成「写在类型里」，适合哈希、计数器、加密这类必须精确控制溢出的算法。

剩下的都是错误与分类类型：`ParseIntError` / `ParseFloatError` 是 `parse` 失败的错误，`IntErrorKind` 进一步区分空串、非法字符、上溢、下溢；`TryFromIntError` 是 `try_from` 转换溢出的错误；`FpCategory` 是 `f64::classify()` 的返回值，用来判断一个浮点是 `NaN`、`Infinite`、`Zero`、`Subnormal` 还是 `Normal`。

## 快速上手

```rust
use std::num::{IntErrorKind, NonZeroU32, ParseIntError, Saturating, Wrapping};

fn divide(total: u32, count: NonZeroU32) -> u32 {
    // 参数类型已经保证了 count 不为 0，不用再判断
    total / count.get()
}

fn main() {
    // 只能通过 new 构造，0 会得到 None
    let n = NonZeroU32::new(5).expect("5 不是 0");
    assert_eq!(n.get(), 5);
    assert!(NonZeroU32::new(0).is_none());
    assert_eq!(divide(100, n), 20);

    // 空指针优化：Option<NonZeroU32> 与 u32 同样大
    assert_eq!(
        std::mem::size_of::<Option<NonZeroU32>>(),
        std::mem::size_of::<u32>()
    );

    // 饱和算术：溢出就停在边界
    let s = Saturating(250u8) + Saturating(10u8);
    assert_eq!(s.0, 255);
    assert_eq!((Saturating(0u8) - Saturating(1u8)).0, 0);

    // 回绕算术：溢出从头开始
    let w = Wrapping(250u8) + Wrapping(10u8);
    assert_eq!(w.0, 4);

    // 解析失败的具体原因
    let err: ParseIntError = "99999999999999999999".parse::<i32>().unwrap_err();
    assert_eq!(*err.kind(), IntErrorKind::PosOverflow);
    let err: ParseIntError = "12x".parse::<i32>().unwrap_err();
    assert_eq!(*err.kind(), IntErrorKind::InvalidDigit);

    // 浮点分类
    assert_eq!(f64::NAN.classify(), std::num::FpCategory::Nan);
    assert_eq!(0.0f64.classify(), std::num::FpCategory::Zero);
}
```

## 常用条目

| 条目 | 说明 |
| --- | --- |
| [[num.NonZeroU32\|NonZeroU32]] | 不为零的 `u32`，`new` 返回 `Option`。 |
| `num::NonZero<T>` | 泛型版本，`NonZero<u32>` 即 `NonZeroU32`。 |
| `num::NonZeroU8` … `NonZeroUsize` | 各无符号整数的非零版本。 |
| `num::NonZeroI32` 等 `NonZeroI*` | 有符号整数的非零版本。 |
| `NonZeroU32::get` | 零成本取回底层整数。 |
| `num::Saturating` | 溢出时钳到边界的算术包装。 |
| `num::Wrapping` | 溢出时回绕的算术包装。 |
| `num::ParseIntError` | 整数解析失败的错误类型。 |
| `num::ParseFloatError` | 浮点解析失败的错误类型。 |
| `num::IntErrorKind` | 解析原因：空、非法字符、上溢、下溢。 |
| `num::TryFromIntError` | `try_from` 整数转换失败的错误。 |
| `num::FpCategory` | 浮点分类：`Nan`/`Infinite`/`Zero`/`Subnormal`/`Normal`。 |

## 注意事项

> [!tip] `Option<NonZeroU32>` 是零开销的「0 表示无效」
> 手写 `0` 当哨兵值要靠约定和注释，`NonZeroU32` 让编译器替你检查。返回 `Option<NonZeroU32>` 的 API 既不浪费空间，也不会漏判。

> [!warning] 别用 `new_unchecked` 绕过检查
> `unsafe { NonZeroU32::new_unchecked(0) }` 是未定义行为，因为类型的不变量被破坏了。只在已经验证过非零的分支里用，且注释清楚依据。

> [!danger] 整数溢出的默认行为取决于编译模式
> debug 构建溢出会 panic，release 构建会静默回绕——同一份代码两种结果。需要确定语义时显式用 `checked_*`（返回 `Option`）、`saturating_*`、`wrapping_*`，或者直接用 `Saturating`/`Wrapping` 包装类型。

## 相关

- [[primitive.整数类型|整数类型]]：`checked_*`/`saturating_*` 等方法的来源。
- [[primitive.浮点类型|浮点类型]]：`classify`、`to_bits` 与 `NaN` 语义。
- [[convert.TryFrom|TryFrom]]：可能失败的数值转换，错误类型是 `TryFromIntError`。
- [[ops|std::ops]]：`Saturating`/`Wrapping` 的运算符由这些特质实现。
- [[cmp|std::cmp]]：`NonZero` 与普通整数一样可比较、可排序。

<!-- BEGIN AUTO ITEMS -->
## 全部条目

> [!note] 自动生成
> 本模块共 22 个公开条目。带链接的是本库已有中文笔记，其余直达 rustdoc 官方文档。

### 结构体

- [`NonZero`](https://doc.rust-lang.org/std/num/struct.NonZero.html)
- [`ParseFloatError`](https://doc.rust-lang.org/std/num/struct.ParseFloatError.html)
- [`ParseIntError`](https://doc.rust-lang.org/std/num/struct.ParseIntError.html)
- [`Saturating`](https://doc.rust-lang.org/std/num/struct.Saturating.html)
- [`TryFromIntError`](https://doc.rust-lang.org/std/num/struct.TryFromIntError.html)
- [`Wrapping`](https://doc.rust-lang.org/std/num/struct.Wrapping.html)
- [`Complex`](https://doc.rust-lang.org/std/num/struct.Complex.html)

### 枚举

- [`FpCategory`](https://doc.rust-lang.org/std/num/enum.FpCategory.html)
- [`IntErrorKind`](https://doc.rust-lang.org/std/num/enum.IntErrorKind.html)

### 特质

- [`ZeroablePrimitive`](https://doc.rust-lang.org/std/num/trait.ZeroablePrimitive.html)

### 类型别名

- [`NonZeroI8`](https://doc.rust-lang.org/std/num/type.NonZeroI8.html)
- [`NonZeroI16`](https://doc.rust-lang.org/std/num/type.NonZeroI16.html)
- [`NonZeroI32`](https://doc.rust-lang.org/std/num/type.NonZeroI32.html)
- [`NonZeroI64`](https://doc.rust-lang.org/std/num/type.NonZeroI64.html)
- [`NonZeroI128`](https://doc.rust-lang.org/std/num/type.NonZeroI128.html)
- [`NonZeroIsize`](https://doc.rust-lang.org/std/num/type.NonZeroIsize.html)
- [`NonZeroU8`](https://doc.rust-lang.org/std/num/type.NonZeroU8.html)
- [`NonZeroU16`](https://doc.rust-lang.org/std/num/type.NonZeroU16.html)
- [[num.NonZeroU32|`NonZeroU32`]]
- [`NonZeroU64`](https://doc.rust-lang.org/std/num/type.NonZeroU64.html)
- [`NonZeroU128`](https://doc.rust-lang.org/std/num/type.NonZeroU128.html)
- [`NonZeroUsize`](https://doc.rust-lang.org/std/num/type.NonZeroUsize.html)

<!-- END AUTO ITEMS -->
