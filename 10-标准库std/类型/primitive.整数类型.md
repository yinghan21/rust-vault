---
title: "整数类型（i8 ~ i128 / isize、u8 ~ u128 / usize）"
type: std-条目
kind: 原始类型
module: primitive
slug: primitive.整数类型
stable: "1.0.0"
tags:
  - std/类型
aliases:
  - 整数类型
  - integer
一句话: 10 种定宽整数与 2 种平台宽度整数的总览：范围、字面量、溢出策略与 120 个方法的分组速查。
---

# 整数类型（`i8` ~ `i128` / `isize`、`u8` ~ `u128` / `usize`）

> [!abstract] 一句话
> 整数类型分为**有符号**（`i8`/`i16`/`i32`/`i64`/`i128`/`isize`）与**无符号**（`u8`/`u16`/`u32`/`u64`/`u128`/`usize`）两族，位宽固定（`isize`/`usize` 随平台），溢出行为可显式选择。

## 简介

Rust 没有「整数」这种单一类型，而是按位宽和符号拆成 12 个原始类型：10 个定宽类型（`i8`~`i128`、`u8`~`u128`）加 `isize`/`usize` 两个平台相关类型。它们都是 `Copy` 的值类型，编译期就能确定大小，没有装箱、没有对象头——这一点和 Java 的 `Integer` 有本质区别。

### 位宽与范围

有符号类型用**补码**表示，n 位取值范围是 `-2^(n-1) ..= 2^(n-1) - 1`；无符号类型是 `0 ..= 2^n - 1`。同样位宽下，无符号的最大值是有符号的两倍多一点，但代价是不能表示负数。

| 类型 | 位宽 | 字节 | 最小值 | 最大值 |
| --- | --- | --- | --- | --- |
| `i8` | 8 | 1 | -128 | 127 |
| `i16` | 16 | 2 | -32_768 | 32_767 |
| `i32` | 32 | 4 | -2_147_483_648 | 2_147_483_647 |
| `i64` | 64 | 8 | -9_223_372_036_854_775_808 | 9_223_372_036_854_775_807 |
| `i128` | 128 | 16 | `-2^127` | `2^127 - 1` |
| `isize` | 平台 | 平台 | 同 `i64`/`i32` | 同 `i64`/`i32` |

| 类型 | 位宽 | 字节 | 最小值 | 最大值 |
| --- | --- | --- | --- | --- |
| `u8` | 8 | 1 | 0 | 255 |
| `u16` | 16 | 2 | 0 | 65_535 |
| `u32` | 32 | 4 | 0 | 4_294_967_295 |
| `u64` | 64 | 8 | 0 | 18_446_744_073_709_551_615 |
| `u128` | 128 | 16 | 0 | `2^128 - 1` |
| `usize` | 平台 | 平台 | 0 | 同 `u64`/`u32` |

> [!tip] `isize` / `usize` 是「指针宽度」
> 64 位平台上它们是 8 字节（`usize::BITS == 64`），32 位平台上是 4 字节。所以**不要**用 `usize` 存需要跨平台一致的数据（文件格式、网络协议），那是 `u32`/`u64` 的活；切片下标、集合长度才用 `usize`。

### 字面量与类型推断

```rust
fn main() {
    let dec = 42;            // 默认推断为 i32
    let hex = 0x2A;          // 十六进制
    let oct = 0o52;          // 八进制
    let bin = 0b101010;      // 二进制
    let sep = 1_000_000;     // 下划线只是分隔符
    let typed = 42u8;        // 后缀显式指定类型
    let big = 10_000_000_000u64;

    assert_eq!(dec, hex);
    assert_eq!(hex, oct);
    assert_eq!(oct, bin);
    assert_eq!(sep, 1_000_000);
    assert_eq!(dec as u8, typed);
    assert_eq!(big, 10_000_000_000u64);
}
```

- **默认是 `i32`**：写 `let x = 1;` 得到 `i32`；有上下文时按上下文推断，`let x: u8 = 1;` 不会先变成 `i32` 再转。
- **字面量放不下是编译错误**：`let x: i8 = 200;` 直接编译失败，不会悄悄截断。
- **负号不是字面量的一部分**：`-1i8` 是「对 `1i8` 取负」，所以 `-128i8` 合法，而 `128i8` 不合法。

### 溢出行为

整数运算不允许「悄悄错」，但 Rust 允许你在**编译配置**和**调用方式**两个层面选择策略：

| 场景 | 行为 |
| --- | --- |
| `cargo build`（debug） | 溢出时 panic：`attempt to add with overflow`。 |
| `cargo build --release` | 默认按二进制回绕（wrapping），等价于补码加法取低位。 |
| 常量 / `const` 求值 | 溢出一律是编译错误，与优化级别无关。 |
| `checked_*` | 返回 `Option`，溢出得 `None`。 |
| `overflowing_*` | 返回 `(结果, 是否溢出)`。 |
| `saturating_*` | 溢出时贴到 `MIN`/`MAX`。 |
| `wrapping_*` | 明确回绕，不受编译配置影响。 |
| `strict_*` | 任何配置下都 panic，行为与 debug 一致。 |

依赖「release 会回绕」是危险的：`overflow-checks = true` 一开，同样的代码就 panic。要确定语义就显式选一个族。

下面 120 个方法（118 个稳定方法 + 2 个已弃用）与 3 个关联常量对所有整数类型通用（无符号类型没有 `abs`、`neg`、`is_negative` 这类与符号相关的方法），文中以 `i32` 为例。

## 边界常量

| 条目 | 说明 |
| --- | --- |
| `MIN` | 类型最小值：`i32::MIN` 为 -2_147_483_648，无符号为 0。 |
| `MAX` | 类型最大值：`i32::MAX` 为 2_147_483_647。 |
| `BITS` | 位宽：`i32::BITS` 为 32，`usize::BITS` 随平台。 |

### 已弃用

| 方法 | 说明 |
| --- | --- |
| `min_value()` | 已弃用，等价于 `MIN`。 |
| `max_value()` | 已弃用，等价于 `MAX`。 |

> [!note] 常量优先
> 新代码直接写 `i32::MIN` / `i32::MAX`；这两个关联函数已在标准库中标记为弃用，只为兼容老代码保留。

## 进制与位操作

| 方法 | 说明 |
| --- | --- |
| `count_ones()` | 返回二进制表示中 1 的个数。 |
| `count_zeros()` | 返回二进制表示中 0 的个数。 |
| `leading_zeros()` | 返回最高位一侧连续 0 的个数。 |
| `trailing_zeros()` | 返回最低位一侧连续 0 的个数。 |
| `leading_ones()` | 返回最高位一侧连续 1 的个数。 |
| `trailing_ones()` | 返回最低位一侧连续 1 的个数。 |
| `highest_one()` | 返回最高位 1 的下标，全 0 时为 `None`。 |
| `lowest_one()` | 返回最低位 1 的下标，全 0 时为 `None`。 |
| `isolate_highest_one()` | 只保留最高的 1，其余位清零。 |
| `isolate_lowest_one()` | 只保留最低的 1，其余位清零。 |
| `rotate_left(n)` | 循环左移 n 位，移出的高位补到低位。 |
| `rotate_right(n)` | 循环右移 n 位，移出的低位补到高位。 |
| `swap_bytes()` | 翻转字节序，如 0x1234 变 0x3412。 |
| `reverse_bits()` | 反转全部比特，最低位与最高位互换。 |
| `cast_unsigned()` | 重解释位模式为同宽无符号类型。 |

> [!tip] `leading_zeros` 是「无分支求对数」的常用写法
> `x.ilog2() == 31 - x.leading_zeros()`，在需要手写位运算的场合比浮点 `log2` 更快也更精确。

## 类型转换

| 方法 | 说明 |
| --- | --- |
| `from_be(x)` | 转换大端字节序的值为目标平台字节序。 |
| `from_le(x)` | 转换小端字节序的值为目标平台字节序。 |
| `to_be()` | 转为大端字节序表示，小端平台上交换字节。 |
| `to_le()` | 转为小端字节序表示，大端平台上交换字节。 |
| `from_str_radix(src, radix)` | 按给定进制解析字符串，失败返回 `Err`。 |
| `format_into(buf)` | 写入调用方提供的缓冲区，返回十进制文本。 |

类型之间的转换还有两条通用路径，不在上表里：`as` 是**截断/符号扩展**的强制转换（`u32 as u8` 只留低 8 位，`i8 as u32` 先符号扩展再解释），`From`/`TryFrom` 是带语义的转换，跨位宽收窄时用 [[convert.TryFrom|TryFrom]] 才不会静默丢数据。

## 检查与溢出

五套溢出策略覆盖同一组运算（加、减、乘、除、取余、取负、绝对值、幂、移位），区别只在**出错时怎么办**；最后两组直接跳过检查。

### `checked_*`：失败返回 `None`

| 方法 | 说明 |
| --- | --- |
| `checked_add(rhs)` | 加法，溢出返回 `None`。 |
| `checked_add_unsigned(rhs)` | 与无符号数相加，溢出返回 `None`。 |
| `checked_sub(rhs)` | 减法，下溢返回 `None`。 |
| `checked_sub_unsigned(rhs)` | 减去无符号数，下溢返回 `None`。 |
| `checked_mul(rhs)` | 乘法，溢出返回 `None`。 |
| `checked_div(rhs)` | 除法，除数为 0 或 `MIN / -1` 返回 `None`。 |
| `checked_div_euclid(rhs)` | 欧几里得除法，除零或溢出返回 `None`。 |
| `checked_rem(rhs)` | 取余，除数为 0 或溢出返回 `None`。 |
| `checked_rem_euclid(rhs)` | 欧几里得取余，除零或溢出返回 `None`。 |
| `checked_neg()` | 取负，`self == MIN` 时返回 `None`。 |
| `checked_shl(rhs)` | 左移，移位数不小于位宽时返回 `None`。 |
| `checked_shr(rhs)` | 右移，移位数不小于位宽时返回 `None`。 |
| `checked_abs()` | 取绝对值，`self == MIN` 时返回 `None`。 |
| `checked_pow(exp)` | 幂运算，溢出返回 `None`。 |
| `checked_isqrt()` | 开平方取整，负数返回 `None`。 |
| `checked_ilog(base)` | 以 `base` 为底的对数，非法输入返回 `None`。 |
| `checked_ilog2()` | 以 2 为底的对数，非正数返回 `None`。 |
| `checked_ilog10()` | 以 10 为底的对数，非正数返回 `None`。 |

### `overflowing_*`：返回结果与溢出标志

| 方法 | 说明 |
| --- | --- |
| `overflowing_add(rhs)` | 加法，返回 `(结果, 是否溢出)`。 |
| `overflowing_add_unsigned(rhs)` | 与无符号数相加，返回结果与溢出标志。 |
| `overflowing_sub(rhs)` | 减法，返回结果与下溢标志。 |
| `overflowing_sub_unsigned(rhs)` | 减去无符号数，返回结果与溢出标志。 |
| `overflowing_mul(rhs)` | 乘法，返回结果与溢出标志。 |
| `overflowing_div(rhs)` | 除法，返回结果与溢出标志。 |
| `overflowing_div_euclid(rhs)` | 欧几里得除法，返回结果与溢出标志。 |
| `overflowing_rem(rhs)` | 取余，返回结果与溢出标志。 |
| `overflowing_rem_euclid(rhs)` | 欧几里得取余，返回结果与溢出标志。 |
| `overflowing_neg()` | 取负，返回结果与溢出标志。 |
| `overflowing_shl(rhs)` | 左移，返回结果与溢出标志。 |
| `overflowing_shr(rhs)` | 右移，返回结果与溢出标志。 |
| `overflowing_abs()` | 取绝对值，返回结果与溢出标志。 |
| `overflowing_pow(exp)` | 幂运算，返回结果与溢出标志。 |

### `saturating_*`：贴到边界

| 方法 | 说明 |
| --- | --- |
| `saturating_add(rhs)` | 加法，上溢贴到 `MAX`。 |
| `saturating_add_unsigned(rhs)` | 与无符号数相加，溢出贴到 `MAX`。 |
| `saturating_sub(rhs)` | 减法，下溢贴到 `MIN`。 |
| `saturating_sub_unsigned(rhs)` | 减去无符号数，下溢贴到 `MIN`。 |
| `saturating_neg()` | 取负，`self == MIN` 时返回 `MAX`。 |
| `saturating_abs()` | 取绝对值，`self == MIN` 时返回 `MAX`。 |
| `saturating_mul(rhs)` | 乘法，溢出贴到最近的边界。 |
| `saturating_div(rhs)` | 除法，只有 `MIN / -1` 会贴到 `MAX`。 |
| `saturating_pow(exp)` | 幂运算，溢出贴到最近的边界。 |

### `wrapping_*`：按位宽回绕

| 方法 | 说明 |
| --- | --- |
| `wrapping_add(rhs)` | 加法，溢出按二进制回绕。 |
| `wrapping_add_unsigned(rhs)` | 与无符号数相加，溢出回绕。 |
| `wrapping_sub(rhs)` | 减法，下溢按二进制回绕。 |
| `wrapping_sub_unsigned(rhs)` | 减去无符号数，下溢回绕。 |
| `wrapping_mul(rhs)` | 乘法，溢出按二进制回绕。 |
| `wrapping_div(rhs)` | 除法，`MIN / -1` 时返回 `MIN`。 |
| `wrapping_div_euclid(rhs)` | 欧几里得除法，溢出时回绕。 |
| `wrapping_rem(rhs)` | 取余，除数为 0 仍然 panic。 |
| `wrapping_rem_euclid(rhs)` | 欧几里得取余，除数为 0 仍然 panic。 |
| `wrapping_neg()` | 取负，`self == MIN` 时返回 `MIN`。 |
| `wrapping_shl(rhs)` | 左移，移位数按位宽取模。 |
| `wrapping_shr(rhs)` | 右移，移位数按位宽取模。 |
| `wrapping_abs()` | 取绝对值，`self == MIN` 时返回 `MIN`。 |
| `wrapping_pow(exp)` | 幂运算，溢出按二进制回绕。 |
| `unsigned_abs()` | 取绝对值并转成同宽无符号整数。 |

### `strict_*`：任何配置下都 panic

| 方法 | 说明 |
| --- | --- |
| `strict_add(rhs)` | 加法，溢出即 panic。 |
| `strict_add_unsigned(rhs)` | 与无符号数相加，溢出即 panic。 |
| `strict_sub(rhs)` | 减法，下溢即 panic。 |
| `strict_sub_unsigned(rhs)` | 减去无符号数，下溢即 panic。 |
| `strict_mul(rhs)` | 乘法，溢出即 panic。 |
| `strict_div(rhs)` | 除法，除零或溢出即 panic。 |
| `strict_div_euclid(rhs)` | 欧几里得除法，溢出即 panic。 |
| `strict_rem(rhs)` | 取余，除零或溢出即 panic。 |
| `strict_rem_euclid(rhs)` | 欧几里得取余，溢出即 panic。 |
| `strict_neg()` | 取负，`self == MIN` 时 panic。 |
| `strict_shl(rhs)` | 左移，移位数越界即 panic。 |
| `strict_shr(rhs)` | 右移，移位数越界即 panic。 |
| `strict_abs()` | 取绝对值，`self == MIN` 时 panic。 |
| `strict_pow(exp)` | 幂运算，溢出即 panic。 |

### 不做边界检查

| 方法 | 说明 |
| --- | --- |
| `unchecked_add(rhs)` | 跳过溢出检查的加法，溢出是 UB。 |
| `unchecked_sub(rhs)` | 跳过下溢检查的减法，溢出是 UB。 |
| `unchecked_mul(rhs)` | 跳过溢出检查的乘法，溢出是 UB。 |
| `unchecked_neg()` | 跳过检查的取负，`MIN` 是 UB。 |
| `unchecked_shl(rhs)` | 跳过移位检查，越界是 UB。 |
| `unchecked_shr(rhs)` | 跳过移位检查，越界是 UB。 |
| `unbounded_shl(rhs)` | 左移，移位数越界时结果为 0。 |
| `unbounded_shr(rhs)` | 右移，移位数越界时结果为 0 或 -1。 |

## 数学

| 方法 | 说明 |
| --- | --- |
| `abs()` | 返回绝对值，`self == MIN` 时 panic。 |
| `abs_diff(other)` | 返回两数差的绝对值，结果为无符号。 |
| `signum()` | 返回符号：`1`、`-1`，零返回 `0`。 |
| `is_positive()` | 判断是否大于 0。 |
| `is_negative()` | 判断是否小于 0。 |
| `pow(exp)` | 返回 `self` 的 `exp` 次幂，溢出 panic。 |
| `isqrt()` | 返回向下取整的整数平方根。 |
| `div_euclid(rhs)` | 返回欧几里得除法的商，向负无穷取整。 |
| `rem_euclid(rhs)` | 返回欧几里得除法的余数，总是非负。 |
| `ilog(base)` | 返回以 `base` 为底的对数，向下取整。 |
| `ilog2()` | 返回以 2 为底的对数，向下取整。 |
| `ilog10()` | 返回以 10 为底的对数，向下取整。 |
| `midpoint(rhs)` | 返回两数的中点，中间结果不溢出。 |

> [!note] 无符号类型另有专用方法
> `u32` 这类无符号类型额外提供 `is_power_of_two()`、`next_power_of_two()`、`checked_next_power_of_two()`、`div_ceil()`、`cast_signed()` 等方法，`i32` 上不存在，需要时去对应模块页查。

> [!note] 标准库没有 `gcd` / `lcm`
> 整数原始类型上不存在 `gcd` 方法，最大公约数需要自己写（用 `%` 或 `rem_euclid` 迭代）或借助 `num` crate。`pow` 也不算捷径：它只是快速幂，指数大照样溢出。

## 字节序

| 方法 | 说明 |
| --- | --- |
| `to_be_bytes()` | 转为大端（网络序）字节数组。 |
| `to_le_bytes()` | 转为小端字节数组。 |
| `to_ne_bytes()` | 转为平台原生字节序的数组。 |
| `from_be_bytes(bytes)` | 由大端字节数组还原成整数。 |
| `from_le_bytes(bytes)` | 由小端字节数组还原成整数。 |
| `from_ne_bytes(bytes)` | 由原生字节数组还原成整数。 |

数组长度等于 `size_of::<T>()`，所以 `i32::to_be_bytes()` 返回 `[u8; 4]`、`i128::to_be_bytes()` 返回 `[u8; 16]`；**数组长度是类型的一部分**，跨位宽不能直接赋值。

## 示例

### 范围与实际存储

```rust
fn main() {
    // 位宽决定范围
    assert_eq!(i8::BITS, 8);
    assert_eq!(i8::MIN, -128);
    assert_eq!(i8::MAX, 127);
    assert_eq!(u8::MAX, 255);
    assert_eq!(std::mem::size_of::<i64>(), 8);
    assert_eq!(std::mem::size_of::<usize>(), usize::BITS as usize / 8);

    // i32 的 MIN 只有最高位是 1
    assert_eq!(i32::MIN.count_ones(), 1);
    assert_eq!((-1i32).count_ones(), 32);
}
```

### 位操作

```rust
fn main() {
    let x: u32 = 0b1011_0000;

    // 计数与定位
    assert_eq!(x.count_ones(), 3);
    assert_eq!(x.leading_zeros(), 24);
    assert_eq!(x.trailing_zeros(), 4);
    assert_eq!(x.highest_one(), Some(7));
    assert_eq!(x.lowest_one(), Some(4));
    assert_eq!(0u32.highest_one(), None);

    // 只留一个 1，常用于轮询位标志
    assert_eq!(x.isolate_lowest_one(), 0b0001_0000);
    assert_eq!(x.isolate_highest_one(), 0b1000_0000);

    // 循环移位与位反转
    let y: u8 = 0b1000_0001;
    assert_eq!(y.rotate_left(1), 0b0000_0011);
    assert_eq!(y.rotate_right(1), 0b1100_0000);
    assert_eq!(0x34u8.reverse_bits(), 0b0010_1100);
    assert_eq!(0x1234u16.swap_bytes(), 0x3412);

    // 有符号数的二进制位被原样解释
    assert_eq!((-1i8).cast_unsigned(), 255u8);
}
```

### 四种溢出策略

```rust
fn main() {
    let max = i8::MAX;

    // 同一次加法，四种语义
    assert_eq!(max.checked_add(1), None);
    assert_eq!(max.overflowing_add(1), (-128, true));
    assert_eq!(max.saturating_add(1), 127);
    assert_eq!(max.wrapping_add(1), -128);

    // 除法只在 MIN / -1 时溢出
    assert_eq!(i8::MIN.checked_div(-1), None);
    assert_eq!(i8::MIN.wrapping_div(-1), i8::MIN);
    assert_eq!(i8::MIN.saturating_div(-1), i8::MAX);

    // 混合符号：一个方法顶掉「先转 i32 再算」
    assert_eq!((-5i32).checked_add_unsigned(7), Some(2));
    assert_eq!((-5i32).saturating_sub_unsigned(7), -12);

    // 幂与绝对值同样会溢出
    assert_eq!(10i32.checked_pow(10), None);
    assert_eq!(i8::MIN.wrapping_abs(), i8::MIN);
    assert_eq!(i8::MIN.unsigned_abs(), 128u8);
}
```

### 欧几里得除法与对数

```rust
fn main() {
    // / 与 % 截断向零，余数符号跟被除数
    assert_eq!((-7i32) / 2, -3);
    assert_eq!((-7i32) % 2, -1);

    // 欧几里得除法：余数永远非负，适合分页、取模索引
    assert_eq!((-7i32).div_euclid(2), -4);
    assert_eq!((-7i32).rem_euclid(2), 1);

    // 对数向下取整，0 走 checked 版本
    assert_eq!(1000u32.ilog10(), 3);
    assert_eq!(1024u32.ilog2(), 10);
    assert_eq!(0u32.checked_ilog10(), None);
    assert_eq!(256u32.isqrt(), 16);
    assert_eq!((-1i32).checked_isqrt(), None);

    // 符号与差值
    assert_eq!((-3i32).signum(), -1);
    assert!(0i32.signum() == 0);
    assert!(!0i32.is_positive() && !0i32.is_negative());
    assert_eq!((-7i32).abs_diff(7), 14u32);
    assert_eq!(90i32.midpoint(100), 95);
}
```

### 进制解析与字节序

```rust
fn main() {
    // 按进制解析：字符串必须是「可选负号 + 合法数字」
    assert_eq!(i32::from_str_radix("ff", 16), Ok(255));
    assert_eq!(i32::from_str_radix("-101", 2), Ok(-5));
    assert!(i32::from_str_radix("2", 2).is_err());
    assert!(i32::from_str_radix("0x1f", 16).is_err());

    // 序列化到字节数组，再原样读回
    let v: u32 = 0x1234_5678;
    assert_eq!(v.to_be_bytes(), [0x12, 0x34, 0x56, 0x78]);
    assert_eq!(v.to_le_bytes(), [0x78, 0x56, 0x34, 0x12]);
    assert_eq!(u32::from_be_bytes(v.to_be_bytes()), v);
    assert_eq!(u32::from_le_bytes(v.to_le_bytes()), v);
    assert_eq!(i32::from_ne_bytes(v.to_ne_bytes()), v as i32);

    // to_be / from_be 互逆，与平台字节序无关
    assert_eq!(u16::from_be(0x1234u16.to_be()), 0x1234);
}
```

### usize 与索引

```rust
fn main() {
    // 切片下标、长度、容量都是 usize
    let data = [10u8, 20, 30];
    let idx: usize = 1;
    assert_eq!(data[idx], 20);
    assert_eq!(data.len(), 3usize);

    // 大数值不要塞进 i32 / u32
    let big: u64 = 4_000_000_000;
    assert_eq!(big as u32, 4_000_000_000u32);

    // usize 位宽随平台，写死 4 或 8 的代码不可移植
    println!("usize 位宽 = {}，字节 = {}", usize::BITS, std::mem::size_of::<usize>());
}
```

## 常见陷阱

1. **依赖「溢出会回绕」**：release 默认回绕，但 `overflow-checks = true` 或 debug 构建立刻变成 panic。要么显式用 `wrapping_*`，要么用 `checked_*`。
2. **`as` 是截断而不是报错**：`300u32 as u8` 得 44，`-1i8 as u32` 得 4_294_967_295（先符号扩展再解释）。取值可能超范围时用 [[convert.TryFrom|TryFrom]]。
3. **把 `usize` 当万能整数**：32 位平台上 `usize` 只有 4 字节，`let x = 5_000_000_000usize;` 直接编译失败；协议字段用定宽类型。
4. **除零与 `MIN / -1`**：`/` 和 `%` 除数为 0 会 panic，`i32::MIN / -1` 也会 panic（结果不可表示）。外部数据先 `checked_div`。
5. **`abs()` 在 `MIN` 上 panic**：`i32::MIN.abs()` 溢出；要绝对值用 `unsigned_abs()` 或 `saturating_abs()`。
6. **移位超出位宽**：debug 下 `1u8 << 8` panic，release 下变成 `1u8 << 0`。移位数来自外部时用 `checked_shl` / `wrapping_shl`。
7. **`%` 的符号**：`-7 % 2 == -1`，如果业务需要非负余数（哈希桶、环形缓冲），用 `rem_euclid`。
8. **默认字面量是 `i32`**：`let x = 3_000_000_000;` 编译报错「out of range for `i32`」，加 `u32`/`i64` 后缀。
9. **混用无符号减法**：`5u32 - 10u32` 在 debug 下 panic，release 下得到巨大值；计数递减先判空或用 `saturating_sub`。

## 相关

- [[primitive|std::primitive]]：原始类型总览，本页所属模块。
- [[i32|std::i32]]：`i32` 的模块页；`i8`/`i16`/`i64`/`i128`/`isize` 的方法完全同构。
- [[u32|std::u32]]：无符号整数模块页，另有 `cast_signed` 等专用方法。
- [[usize|std::usize]]：指针宽度的无符号类型，切片与集合长度都用它。
- [[primitive.浮点类型|Type f32]]：浮点类型总览，与整数之间用 `as` 或 `TryFrom` 转换。
- [[num.NonZeroU32|NonZeroU32]]：非零整数，让 `Option` 零开销。
- [[convert.TryFrom|TryFrom]]：跨位宽、跨符号的显式转换。
- [[03-变量与数据类型|变量与数据类型]]：字面量、类型推断与默认 `i32`。
