# 测试数据说明 · HSBC 对账单（456-459775-838）票据映射

> 数据文件：[`backend/data/test_invoices_hsbc_456459775838.json`](../backend/data/test_invoices_hsbc_456459775838.json)
> 用途：基于真实 HSBC 商务户口结单流水，造对应票据，用于「银行票据匹配 → 会计分录生成」的端到端测试验证。
> 结单：HSBC Business Direct · 户口 456-459775-838 · KWUN TONG · 2025-04-25 ~ 2025-05-24 · Page 3 of 3。
> 我方公司：ABC Trading Co. Ltd（company_id=ABC）· 币种 HKD（含 1 张 USD 外币票据）。

---

## 一、测试覆盖场景一览

| # | 票据号 | 对方 | 金额 | 收/支 | 期望匹配 | 对应银行流水 |
|---|---|---|---|---|---|---|
| TINV-001 | SI-2025-0418 | 中國海外建築 | 82,368.00 | 收入 | **match** | 26 Apr 转账收入 +82,368.00 |
| TINV-002 | SI-2025-0421 | 中國建築(香港) | 5,992.00 | 收入 | **match** | 29 Apr 转账收入 +5,992.00 |
| TINV-003 | SI-2025-0509 | 中國海外建築 | 14,600.00 | 收入 | **match** | 09 May 转账收入 +14,600.00 |
| TINV-004A | SI-2025-0518 | 中國海外建築 | 100,000.00 | 收入 | **multi 一对多** | 22 May 转账收入 +159,554.00 |
| TINV-004B | SI-2025-0519 | 中國海外建築 | 59,554.00 | 收入 | **multi 一对多** | （同上，合并匹配）|
| TINV-005 | SI-2025-0511 | 豐盛企業 | 13,500.00 | 收入 | **partial 差额** | 23 May 入票机 +13,422.00（差 78.00）|
| TINV-006 | MHC-8750033 | 三菱HC資本 | 9,994.00 | 支出 | **match** | 02 May 自动转账支出 −9,994.00 |
| TINV-007 | MPF-0459635501-202505 | 宏利公積金 | 6,580.00 | 支出 | **match** | 13 May 自动转账支出 −6,580.00 |
| TINV-008 | SI-2025-0418 | 中國海外建築 | 82,368.00 | 收入 | **duplicate 重复** | （TINV-001 重复，应去重）|
| TINV-009 | RCP-0505-1180 | 美心食品 | 850.00 | 支出 | **orphan 现金** | 无对应流水（现金支付）|
| TINV-010 | PK-2025-0515 | 中環停車場 | 2,200.00 | 支出 | **orphan 董事垫付** | 无对应流水 |
| TINV-011 | SI-2025-0524 | 嘉華貿易 | 28,000.00 | 收入 | **orphan 应收** | 已开票未收款 |
| TINV-012 | UPS-2025-0507 | UPS Hong Kong | USD 78.40 | 支出 | **orphan 外币** | 外币账户本期无交易 |

**统计**：13 张票据（收入 8 / 支出 5）· match 5 · multi 2 · partial 1 · duplicate 1 · orphan 4。

---

## 二、期望生成的会计分录（验证 JE 逻辑）

| 票据 | 期望分录（Dr / Cr） |
|---|---|
| TINV-001/002/003 | Dr 银行-HSBC储蓄 / Cr Revenue from services（收入）|
| TINV-004A+004B | 合并：Dr 银行-HSBC储蓄 159,554 / Cr Revenue 159,554 |
| TINV-005（partial）| Dr 银行 13,422 + Dr Bank charges 78 / Cr Revenue 13,500 |
| TINV-006 | Dr 融资租赁/利息 / Cr 银行-HSBC储蓄 |
| TINV-007 | Dr MPF contributions / Cr 银行-HSBC储蓄 |
| TINV-009 | Dr Meals and entertainment / Cr Petty Cash（现金）|
| TINV-010 | Dr Travelling expenses / Cr Director's Current Account |
| TINV-011 | Dr Accounts Receivable / Cr Revenue（已开票未收款）|
| TINV-012 | Dr Postage and courier / Cr 银行/应付（USD 按交易日汇率折算 HKD）|

---

## 三、结单中「无需票据」的流水（单独列示，测试 unmatched/免票据）

| 银行流水 | 处理 | 期望分录 |
|---|---|---|
| 28 Apr 利息收入 +18.43 | 免票据自动入账 | Dr 银行 / Cr Interest income |
| 29 Apr CHOI YUET MAN CHARGES −5.00 | 银行手续费 | Dr Bank charges / Cr 银行 |
| 30 Apr ATM 提取现金 −63,500.00 | 现金提取（无票据）| Dr Petty Cash / Cr 银行 |
| 02 May ATM 提取现金 −8,000.00 | 现金提取 | Dr Petty Cash / Cr 银行 |
| 03 May ATM 提取现金 −8,000.00 | 现金提取 | Dr Petty Cash / Cr 银行 |
| 23 May CR TO 456-459775-001 −150,000.00 | 内部账户调拨（不进损益）| Dr 银行-往来 001 / Cr 银行-储蓄 |

> 说明：现金提取（ATM）合计 79,500.00 形成备用金池，TINV-009/010 的现金支出即由此池支付，可用于测试「现金提取 → 现金费用结转」链路。

---

## 四、结单勾稽校验（可用于断言）

- **港元储蓄子账户**：期初 B/F 40,644.90；存入 5 笔合计 262,532.43；提取 7 笔合计 246,079.00；期末应为 57,098.33。
- **港元往来子账户**：本页可见入票机存入 13,422.00，期末 397,400.52；存入 11 笔 296,155.00 / 提取 21 笔 504,438.20（整张结单口径）。
- **外币储蓄 USD**：期初 128,244.17，本期 0 进 0 出。
- 全面理财总结余平均值 HKD 2,546,639.08（2025-02-01 ~ 04-30），本期免月费。

---

## 五、使用建议

1. **导入**：把 `invoices[]` 写入 `Invoice` 表（字段已对齐 `backend/models.py`；以 `_` 开头字段为测试元数据，导入时忽略）。
2. **匹配验证**：配合提示词 [`prompts_银行票据匹配会计分录.md`](prompts_银行票据匹配会计分录.md)，验证 match / multi / partial / orphan / duplicate 各分支与 unmatched 流水识别。
3. **分录验证**：核对生成 JE 是否借贷平衡、科目正确（见第二节）。
4. **报表验证**：确认后过账，结合 [`财务报告生成规则与说明.md`](财务报告生成规则与说明.md) 验证试算平衡与 P&L / B/S。
