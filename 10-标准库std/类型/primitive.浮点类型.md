---
title: "浮点类型（f32 / f64）"
type: std-条目
kind: 原始类型
module: primitive
slug: primitive.浮点类型
stable: "1.0.0"
tags:
  - std/类型
aliases:
  - 浮点类型
  - float
一句话: f32 与 f64 的总览：IEEE-754 表示、NaN 与 -0.0、精度极限，以及 72 个方法的分组速查。
---

# 浮点类型（`f32` / `f64`）

> [!abstract] 一句话
> `f32` 是 IEEE-754 的 **binary32**（4 字节），`f64` 是 **binary64**（8 字节）；它们能表示小数和无穷大，代价是精度有限、`NaN` 不等于自己、`-0.0 == 0.0`。

## 简介

浮点数按「符号位 + 指数 + 尾数」存储，能覆盖极大的数量级，但只能精确表示其中很小一部分——其余值都会被舍入到最近的可表示值。

| 类型 | 总位数 | 符号 | 指数 | 尾数 | 十进制有效位 | 典型用途 |
| --- | --- | --- | --- | --- | --- | --- |
| `f32` | 32 | 1 | 8 | 23 | 约 6–7 位 | 图形、游戏、内存敏感场景 |
| `f64` | 64 | 1 | 11 | 52 | 约 15–16 位 | 默认选择：计算、科学、解析 |

**默认是 `f64`**：`let x = 1.0;` 推断为 `f64`。`f32` 只有在类型标注、后缀（`1.0f32`）或 API 签名要求时才出现。

### 三个特殊值

- **`NaN`（Not a Number）**：`0.0 / 0.0`、`inf - inf`、负数开方都会得到它。任何与 `NaN` 的比较都是 `false`，包括 `NaN == NaN`；判断必须用 `is_nan()`。
- **无穷大**：`f64::INFINITY` / `f64::NEG_INFINITY`，`1.0 / 0.0` 得到正无穷。无穷参与运算仍可能变回 `NaN`。
- **`-0.0`**：与 `0.0` 相等（`==` 为 `true`），但 `1.0 / -0.0` 是负无穷，且符号位不同。需要区分时用 `is_sign_negative()` 或 `total_cmp()`。

### 精度

`f64` 的尾数只有 52 位，`0.1`、`0.2`、`0.3` 都无法精确表示：

```rust
fn main() {
    // 0.1 + 0.2 不等于 0.3
    let sum = 0.1f64 + 0.2f64;
    println!("{:.20}", sum); // 0.30000000000000004441
    assert!(sum != 0.3);

    // 1.0 / 5.0 在 f32 下存的是 0.20000000298…，不是精确的 0.2
    let fifth = 1.0f32 / 5.0f32;
    assert_eq!(fifth as f64, 0.20000000298023224);

    // 有效数字只有 6~7 位，多出来的位是噪声
    let x: f32 = 16_777_217.0; // 2^24 + 1，超出 f32 的整数精度
    assert_eq!(x, 16_777_216.0);
}
```

`f32::EPSILON`（约 1.19e-7）与 `f64::EPSILON`（约 2.22e-16）是「1.0 与其后继值的差」，可用来做相对误差比较；但它不能代替业务上的精度要求。

下面 72 个方法（71 个稳定方法 + 1 个已弃用）与 7 个关联常量对 `f32`、`f64` 完全同构，文中以 `f64` 为例。

## 关联常量

| 常量 | 说明 |
| --- | --- |
| `EPSILON` | 机器精度：`1.0` 与下一个可表示值之差。 |
| `MIN` | 最小的**有限**值，`f64::MIN` 约 -1.8e308。 |
| `MAX` | 最大的有限值，`f64::MAX` 约 1.8e308。 |
| `MIN_POSITIVE` | 最小的**正正规数**，约 2.2e-308。 |
| `NAN` | 静默 NaN 常量。 |
| `INFINITY` | 正无穷大。 |
| `NEG_INFINITY` | 负无穷大。 |

> [!note] 常量从哪里来
> `f32::EPSILON` 这类关联常量从 1.43 起可直接在原始类型上访问，等价于 `std::f32::EPSILON`。数学常量（`PI`、`E`）在 `std::f64::consts`，不在原始类型上。

## 数学方法

### 幂、开方与乘加

| 方法 | 说明 |
| --- | --- |
| `powi(n)` | 返回整数次幂。 |
| `powf(n)` | 返回浮点次幂。 |
| `sqrt()` | 返回平方根，负数得 `NaN`。 |
| `cbrt()` | 返回立方根，负数也有效。 |
| `hypot(other)` | 返回直角三角形的斜边长度。 |
| `recip()` | 返回倒数 `1.0 / self`。 |
| `mul_add(a, b)` | 返回 `self * a + b`，只舍入一次。 |

### 指数与对数

| 方法 | 说明 |
| --- | --- |
| `exp()` | 返回 `e^self`。 |
| `exp2()` | 返回 `2^self`。 |
| `exp_m1()` | 返回 `e^self - 1`，`self` 接近 0 时更精确。 |
| `ln()` | 返回自然对数。 |
| `ln_1p()` | 返回 `ln(1.0 + self)`，接近 0 时更精确。 |
| `log(base)` | 返回以 `base` 为底的对数。 |
| `log2()` | 返回以 2 为底的对数。 |
| `log10()` | 返回以 10 为底的对数。 |

### 三角与角度

| 方法 | 说明 |
| --- | --- |
| `sin()` | 返回正弦，参数是弧度。 |
| `cos()` | 返回余弦，参数是弧度。 |
| `tan()` | 返回正切，参数是弧度。 |
| `asin()` | 返回反正弦，越界得 `NaN`。 |
| `acos()` | 返回反余弦，越界得 `NaN`。 |
| `atan()` | 返回反正切。 |
| `atan2(other)` | 返回四象限反正切。 |
| `sin_cos()` | 同时返回 `(sin, cos)`，省一次化简。 |
| `to_degrees()` | 转换弧度为角度。 |
| `to_radians()` | 转换角度为弧度。 |

### 双曲函数

| 方法 | 说明 |
| --- | --- |
| `sinh()` | 返回双曲正弦。 |
| `cosh()` | 返回双曲余弦。 |
| `tanh()` | 返回双曲正切。 |
| `asinh()` | 返回反双曲正弦。 |
| `acosh()` | 返回反双曲余弦，小于 1 得 `NaN`。 |
| `atanh()` | 返回反双曲正切，绝对值大于 1 得 `NaN`。 |

### 绝对值、符号与除法

| 方法 | 说明 |
| --- | --- |
| `abs()` | 返回绝对值，`NaN` 仍是 `NaN`。 |
| `signum()` | 返回符号：`1.0`、`-1.0`，`NaN` 得 `NaN`。 |
| `copysign(sign)` | 返回取 `sign` 符号位后的绝对值。 |
| `div_euclid(rhs)` | 返回欧几里得除法的商。 |
| `rem_euclid(rhs)` | 返回欧几里得除法的余数，非负。 |

### 代数优化运算

| 方法 | 说明 |
| --- | --- |
| `algebraic_add(rhs)` | 允许按代数律重排的加法。 |
| `algebraic_sub(rhs)` | 允许按代数律重排的减法。 |
| `algebraic_mul(rhs)` | 允许按代数律重排的乘法。 |
| `algebraic_div(rhs)` | 允许按代数律重排的除法。 |
| `algebraic_rem(rhs)` | 允许按代数律重排的取余。 |

> [!warning] `algebraic_*` 会改变结果
> 它们放弃 IEEE-754 的确定性，允许编译器重排、合并且按代数律化简（例如把 `(a + b) + c` 变成 `a + (b + c)` 以缩短依赖链）。结果可能与 `+`、`*` 逐位不同，**只用于对精度不敏感的批量计算**。

## 舍入

| 方法 | 说明 |
| --- | --- |
| `floor()` | 返回不大于 `self` 的最大整数。 |
| `ceil()` | 返回不小于 `self` 的最小整数。 |
| `round()` | 返回最近整数，正好一半时远离 0。 |
| `round_ties_even()` | 返回最近整数，正好一半时取偶数。 |
| `trunc()` | 返回整数部分，向零截断。 |
| `fract()` | 返回小数部分，符号与 `self` 相同。 |

## 判断

### 分类

| 方法 | 说明 |
| --- | --- |
| `is_nan()` | 判断是否为 `NaN`。 |
| `is_infinite()` | 判断是否为正负无穷大。 |
| `is_finite()` | 判断是否为有限值。 |
| `is_normal()` | 判断是否为正规数（非零、非次正规、非无穷）。 |
| `is_subnormal()` | 判断是否为次正规数。 |
| `classify()` | 返回 `FpCategory` 分类枚举。 |

### 符号位

| 方法 | 说明 |
| --- | --- |
| `is_sign_positive()` | 判断符号位是否为正，`+0.0` 为 `true`。 |
| `is_sign_negative()` | 判断符号位是否为负，`-0.0` 为 `true`。 |

### 相邻可表示值

| 方法 | 说明 |
| --- | --- |
| `next_up()` | 返回大于 `self` 的最小可表示值。 |
| `next_down()` | 返回小于 `self` 的最大可表示值。 |

## 位转换

| 方法 | 说明 |
| --- | --- |
| `to_bits()` | 返回内存位模式，`f32` 得 `u32`、`f64` 得 `u64`。 |
| `from_bits(v)` | 由位模式构造浮点数，不校验 `NaN` 是否规范。 |
| `to_be_bytes()` | 转为大端字节数组。 |
| `to_le_bytes()` | 转为小端字节数组。 |
| `to_ne_bytes()` | 转为平台原生字节序的数组。 |
| `from_be_bytes(bytes)` | 由大端字节数组还原。 |
| `from_le_bytes(bytes)` | 由小端字节数组还原。 |
| `from_ne_bytes(bytes)` | 由原生字节数组还原。 |
| `to_int_unchecked()` | 跳过检查转为整数，越界是 UB。 |

> [!danger] `to_int_unchecked` 是 `unsafe`
> 它不做范围检查，值超出目标整数范围、或本身是 `NaN`/无穷大时，行为未定义。日常转换用 `as`（饱和）或先 `is_finite()` 校验。

## 比较

| 方法 | 说明 |
| --- | --- |
| `max(other)` | 返回较大者，忽略 `NaN`。 |
| `min(other)` | 返回较小者，忽略 `NaN`。 |
| `midpoint(other)` | 返回中点，避免直接相加溢出。 |
| `total_cmp(&other)` | 返回全序比较结果，可区分 `NaN` 与 `-0.0`。 |
| `clamp(min, max)` | 限制值在区间内，`NaN` 原样返回。 |
| `abs_sub(other)` | 已弃用，等价于 `(self - other).max(0.0)`。 |

浮点数只实现 `PartialOrd`/`PartialEq`，**没有 `Ord`/`Eq`**，所以不能直接排序、不能做 `BTreeMap` 的键；需要全序时用 `total_cmp`（见 [[cmp.Ordering|Ordering]]）。

## 示例

### 特殊值与符号位

```rust
fn main() {
    // 机器精度与极值
    assert!(f32::EPSILON > 0.0 && f32::EPSILON < 1e-6);
    assert!(f64::MAX.is_finite());
    assert!(f64::MIN < 0.0);
    assert!(f64::MIN_POSITIVE > 0.0 && f64::MIN_POSITIVE < 1e-307);

    // 三个特殊值
    let zero = 0.0f64;
    assert!((zero / zero).is_nan());
    assert_eq!(1.0f64 / zero, f64::INFINITY);
    assert_eq!(-1.0f64 / zero, f64::NEG_INFINITY);

    // -0.0 与 0.0 相等，但符号位不同、除法结果不同
    assert_eq!(-0.0f64, 0.0f64);
    assert!((-0.0f64).is_sign_negative());
    assert!((0.0f64).is_sign_positive());
    assert_eq!(1.0f64 / -0.0, f64::NEG_INFINITY);
}
```

### 分类与相邻值

```rust
use std::num::FpCategory;

fn main() {
    let nan = f64::NAN;
    assert!(nan.is_nan());
    assert!(!nan.is_finite());
    assert!(!nan.is_infinite());
    assert!(!nan.is_normal() && !nan.is_subnormal());

    // 五种类别
    assert_eq!(nan.classify(), FpCategory::Nan);
    assert_eq!(0.0f64.classify(), FpCategory::Zero);
    assert_eq!(1.0f64.classify(), FpCategory::Normal);
    assert_eq!(f64::INFINITY.classify(), FpCategory::Infinite);
    assert!(f64::MIN_POSITIVE.is_normal());
    assert!((f64::MIN_POSITIVE / 2.0).is_subnormal());

    // 相邻可表示值之间没有别的浮点数
    let one = 1.0f64;
    assert_eq!(one.next_up(), 1.0 + f64::EPSILON);
    assert_eq!(one.next_down(), 1.0 - f64::EPSILON / 2.0);
    assert!(one.next_down() < one && one.next_up() > one);
}
```

### 舍入

```rust
fn main() {
    assert_eq!(2.7f64.floor(), 2.0);
    assert_eq!((-2.7f64).floor(), -3.0);
    assert_eq!(2.1f64.ceil(), 3.0);
    assert_eq!((-2.1f64).ceil(), -2.0);

    // round 遇半数远离 0，round_ties_even 遇半数取偶数
    assert_eq!(2.5f64.round(), 3.0);
    assert_eq!((-2.5f64).round(), -3.0);
    assert_eq!(2.5f64.round_ties_even(), 2.0);
    assert_eq!(3.5f64.round_ties_even(), 4.0);

    // trunc 向零截断；fract 保留符号
    assert_eq!((-2.7f64).trunc(), -2.0);
    assert_eq!(2.75f64.fract(), 0.75);
    assert_eq!((-2.75f64).fract(), -0.75);
}
```

### 精度与相等比较

```rust
fn main() {
    // 直接比较几乎总是错的
    let sum = 0.1f64 + 0.2f64;
    assert!(sum != 0.3);
    assert!((sum - 0.3).abs() < 1e-12);

    // 累加误差：加 10 次 0.1 得不到 1.0
    let mut acc = 0.0f64;
    for _ in 0..10 {
        acc += 0.1;
    }
    assert!(acc != 1.0);
    assert!((acc - 1.0).abs() < 1e-9);

    // 相对误差比较
    fn approx_eq(a: f64, b: f64) -> bool {
        if a == b {
            return true;
        }
        (a - b).abs() <= f64::EPSILON * a.abs().max(b.abs())
    }
    assert!(approx_eq(0.1 + 0.2, 0.3));
    assert!(!approx_eq(1.0, 2.0));

    // 用 mul_add 减少一次舍入
    assert_eq!(3.0f64.mul_add(2.0, 1.0), 7.0);
}
```

### 数学函数与比较

```rust
fn main() {
    assert_eq!(16.0f64.sqrt(), 4.0);
    assert_eq!(2.0f64.powi(10), 1024.0);
    assert_eq!(100.0f64.log10(), 2.0);
    assert_eq!(5.0f64.hypot(12.0), 13.0);
    assert!((std::f64::consts::FRAC_PI_2.sin() - 1.0).abs() < 1e-15);
    assert_eq!(std::f64::consts::PI.to_degrees(), 180.0);

    assert_eq!((-3.5f64).abs(), 3.5);
    assert_eq!((-3.5f64).signum(), -1.0);
    assert_eq!(3.5f64.copysign(-1.0), -3.5);
    assert_eq!((-3.5f64).recip(), -1.0 / 3.5);

    // max / min 忽略 NaN，NaN 不会「传染」
    assert_eq!(1.0f64.max(f64::NAN), 1.0);
    assert_eq!(1.0f64.min(f64::NAN), 1.0);
    assert_eq!(7.0f64.clamp(2.0, 3.0), 3.0);

    // total_cmp 提供全序，可用于排序
    use std::cmp::Ordering;
    assert_eq!(1.0f64.total_cmp(&2.0), Ordering::Less);
    assert_eq!((-0.0f64).total_cmp(&0.0), Ordering::Less);
}
```

### 位模式与字节序

```rust
fn main() {
    // 符号位 + 指数 + 尾数
    assert_eq!(1.0f32.to_bits(), 0x3F80_0000);
    assert_eq!(f32::from_bits(0x3F80_0000), 1.0);
    assert_eq!((-1.0f32).to_bits() & 0x8000_0000u32, 0x8000_0000u32);

    // NaN 的位模式不止一种，但都能被识别
    let nan = f32::from_bits(0x7FC0_0001);
    assert!(nan.is_nan());

    // 字节序转换
    assert_eq!(1.0f32.to_be_bytes(), [0x3F, 0x80, 0x00, 0x00]);
    assert_eq!(f32::from_be_bytes(1.0f32.to_be_bytes()), 1.0);
    assert_eq!(f64::from_le_bytes(1.0f64.to_le_bytes()), 1.0);
}
```

### 与整数的转换

```rust
fn main() {
    // 浮点转整数：as 是饱和的，越界贴边界，NaN 变 0
    assert_eq!(300.7f64 as u8, 255);
    assert_eq!((-1.0f64) as u8, 0);
    assert_eq!(f64::NAN as i32, 0);
    assert_eq!((-2.9f64) as i32, -2); // 向零截断

    // 整数转浮点：超出尾数位数就丢精度
    assert_eq!(16_777_217u32 as f32, 16_777_216.0);
    assert_eq!(9_007_199_254_740_993u64 as f64, 9_007_199_254_740_992.0);
}
```

## 常见陷阱

1. **用 `==` 判断 `NaN`**：`f64::NAN == f64::NAN` 是 `false`，必须用 `is_nan()`；同理 `PartialOrd` 的所有比较对 `NaN` 都返回 `false`，排序时要先决定 `NaN` 放哪。
2. **直接比较两个浮点数**：`0.1 + 0.2 != 0.3` 是设计使然。用绝对误差（已知量级）或相对误差（`EPSILON * max(|a|, |b|)`）比较，别写 `a == b`。
3. **累加误差会放大**：循环里反复加小数值、或把大数和小数混加，误差会累积；求和大量浮点时可先排序按绝对值从小到大加，或用 Kahan 求和。
4. **`as` 转换不报错，而是饱和**：越界贴到边界（`300.7f64 as u8` 得 255）、`NaN as i32` 得 0、负数转无符号得 0、小数部分向零截断。它**不会** panic，也**不是** UB，但很可能不是你要的结果；要精确控制先用 `is_finite()` 校验再 `as`。
5. **把 `-0.0` 当 `0.0`**：两者 `==` 相等，但 `1.0 / -0.0` 是负无穷，`signum()` 分别是 `-1.0` 和 `1.0`；需要区分时用 `is_sign_negative()`。
6. **`round()` 不是四舍五入**：它是「半数远离 0」，`2.5 → 3.0`、`-2.5 → -3.0`；金融计算要「半数取偶」请用 `round_ties_even()`。
7. **拿浮点做金额和高精度计数**：`f64` 只有 15–16 位有效数字，`0.1` 无法精确表示；金额用整数分（`u64`）或定点/十进制库。
8. **以为 `f32` 只是「省内存的 f64」**：`f32` 只有约 7 位有效数字，`16777217.0` 会变成 `16777216.0`；跨平台图形接口要传 `f32`，但计算过程尽量用 `f64`。
9. **`inf - inf`、`0.0 * inf` 都是 `NaN`**：无穷大参与运算不一定还是无穷大，链式计算后要检查 `is_finite()`。

## 相关

- [[primitive|std::primitive]]：原始类型总览，本页所属模块。
- [[f32|std::f32]]：`f32` 的模块页，含 `consts` 子模块的数学常量。
- [[f64|std::f64]]：`f64` 的模块页，默认浮点类型。
- [[primitive.整数类型|Type i32]]：整数类型总览，与浮点之间用 `as` 或 `TryFrom` 转换。
- [[cmp.Ordering|Ordering]]：`total_cmp` 的返回类型，全序比较的基础。
- [[primitive.bool|Type bool]]：`is_nan`、`is_finite` 等判断方法的返回类型。
- [[03-变量与数据类型|变量与数据类型]]：浮点字面量、默认 `f64` 与类型推断。
