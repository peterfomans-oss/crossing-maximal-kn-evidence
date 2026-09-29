# 交叉极大完全图形：证明、证书与计算记录

[English](README.md)

本仓库整理了关于交叉极大简单完全图形的数学论证、有限穷举、可核查图形证书，以及可复现的 SAT/XOR 运行记录。

## 最重要的结论边界

本仓库**不宣称已经证明新的 K17 定理**。

目前有两次 K17 计算：

1. 历史的**有前缀约束公式**被 CryptoMiniSat 报告为 UNSAT。它额外包含 14 条子句：1 条固定首个伙伴的子句和 13 条前缀子句。支持这种规范化的一般存在性引理尚未证明，所以这次运行不能推出无条件的 K17 结论。
2. 后来的**安全无前缀公式**删掉了全部 14 条有争议子句，也被 CryptoMiniSat 报告为 UNSAT。

两次结果都是针对精确哈希编码公式的**无独立证书、求解器报告 UNSAT**。两次运行都没有生成可由独立证明检查器核验的 UNSAT 证明证书。安全版本不依赖有争议的前缀规范化，因此证据更强；但在完整关闭“编码到真实图形”的审计并取得独立可核查的 UNSAT 证书以前，仍不能把它写成数学定理。

可以准确表述为：

> 使用 crossing-only SAT/XOR 编码，CryptoMiniSat 对精确哈希的 K17 公式报告了 UNSAT；其中安全版本已经删去有争议的 14 条前缀相关子句。目前保存的是可复现的求解器审计记录，不是独立认证的 UNSAT 证明。

不能仅凭这些记录表述为“已经证明 K17”。

## 安全无前缀运行摘要

| 实例 | 变量数 | CNF 子句 | XOR 子句 | 公式 SHA-256 | 已保存结果 |
|---|---:|---:|---:|---|---|
| K14 | 3,003 | 134,335 | 30,030 | `32affac3edb48da546fc57a518fb8bca3d77b1f18adb69d10e584e7da9e4abad` | 求解器报告 UNSAT，无证书 |
| K15 | 4,095 | 200,892 | 50,050 | `4c69c551566203434aca6297de0f0180682cfa8451d0f5ecda6f088c7f935233` | 求解器报告 UNSAT，无证书 |
| K16 | 5,460 | 291,476 | 80,080 | `7fbb430aaba9761372840f08de315c3d8a7fcaf1781c69c8a64f079df116c5d3` | 求解器报告 UNSAT，无证书 |
| K17 | 7,140 | 412,058 | 123,760 | `9c9abf7012053fa6f064f2d43233e11ec3f274fcb1003b900d6f4910664c5490` | 求解器报告 UNSAT，无证书 |

原始记录给出的证据标签是 `UNCERTIFIED_SOLVER_AUDIT`，声明范围是 `HASHED_ENCODED_FORMULA_ONLY`。

## 仓库中可以独立复核的成果

- K5 完整有限分类：穷尽 1,296 个规范旋转系统及 650 种相关沿边交叉次序，最终得到两个无标号交叉表类型和 72 个带标号表。
- 利用完整 K5 分类及有限局部表，证明删除见证对应的竞赛关系为全序。
- 条件性逻辑归约：如果存在一个好的非空删除见证，那么在明确背景下可以无损加入历史前缀规范化。
- 固定根边障碍定理：一条被交叉的根边没有任何好的非空删除中心，当且仅当某个至多七点的含根边限制已经有这一性质；七点上界是尖锐的。
- 经过检查的真实 K8、K9 图形，反驳删去“每条边都被交叉”前提后的若干更强说法。它们**不是**原始全边被交叉 K17 目标的反例。

每项结论的精确范围见 [`CLAIMS.md`](CLAIMS.md)，证据标签说明见 [`EVIDENCE_LEVELS.md`](EVIDENCE_LEVELS.md)。

## 目录

- [`proofs/`](proofs/)：K5 完备性、条件性逻辑归约和固定根边障碍定理。
- [`certificates/`](certificates/)：K8/K9 交叉数据、旋转、平面化证书、构造和独立检查器。
- [`computations/`](computations/)：脱敏后的安全 K14–K17 记录及历史有前缀 K17 记录。
- [`solver/`](solver/)：用于审阅和复现 SAT/XOR 编码的源代码；不包含求解器二进制。
- [`audits/`](audits/)：独立有限复核和数学检查入口。
- [`research/`](research/)：尚未证明的前缀引理状态及已失败路线。
- [`OPEN_OBLIGATIONS.md`](OPEN_OBLIGATIONS.md)：形成更强结论前仍需完成的义务。
- [`DATA_AND_PROVENANCE.md`](DATA_AND_PROVENANCE.md)：来源、整理和完整性说明。

## 快速复核

建议使用 Python 3.10 或更高版本。发布前检查和数学证书复核只使用 Python 标准库。

```text
python scripts/release_preflight.py
python scripts/run_core_checks.py
```

不要使用 `-O`，因为若干有限检查器依赖断言。这两个命令不会重新运行完整 K17 求解。详情见 [`REPRODUCE.md`](REPRODUCE.md)。

## 许可证与引用

本仓库的原创内容由 `peterfomans-oss` 以 [MIT 许可证](LICENSE)
发布，引用信息见 [`CITATION.cff`](CITATION.cff)。所引用工具及历史来源见
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。仓库不包含第三方求解器二进制或源码。
