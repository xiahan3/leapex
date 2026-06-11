# Leapex 需求文档 v3.0 增量

> **文档定位**：基于现有 v2.0 PRD + 已部署的 FastAPI 后端，新增两大模块
> **更新日期**：2026-06-09 | **作者**：Leapex Product
> **适用范围**：香港 SME / 会计师事务所多客户场景

---

## 一、本期范围与设计前提

### 1.1 现有系统盘点（v2.0 已实现）
- 单租户单公司：默认 `ABC Trading Co. Ltd`
- 工作台已有"全部企业 / 单企业"切换（mock 数据：ABC Trading / Peak View / HK Ventures）
- 数据闭环：采集 → 匹配记账 → 期末调整 → TB → P&L / BS
- 后端：FastAPI + SQLite，30+ REST 接口

### 1.2 本期目标
| 模块 | 解决什么问题 |
|---|---|
| **租户管理** | 把"演示数据"升级为"商业化 SaaS"——支持会计师事务所同时服务多个客户公司，按用量计费，账号/公司有配额，权限隔离 |
| **账簿管理** | 把"会计分录"沉淀为"标准账簿体系"——满足 HK CO S622 法定要求 + 审计师调阅 + 老板日常查账三类场景 |

### 1.3 用户角色总图
```
┌──────────────────────────────────────────────────────────┐
│ 平台层                                                    │
│ ┌──────────────┐                                          │
│ │ 超级管理员    │ Leapex 运营人员                          │
│ │ (Super Admin)│ — CRUD 租户、配额、计费、监控             │
│ └──────────────┘                                          │
├──────────────────────────────────────────────────────────┤
│ 租户层（Tenant = 会计师事务所 / 企业集团 / 独立 SME）       │
│  ┌────────────────────────────────────────────────────┐  │
│  │ 租户管理员 (Tenant Admin)                           │  │
│  │ — 管理本租户员工、公司、套餐用量监控、Top-up Token  │  │
│  └────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────┤
│ 公司层（Company = 法人主体，例：ABC Trading Co. Ltd）       │
│  ├─ 子账套层（Book = 同一公司的多套账，例：经营账+税务账） │
│  └─ 员工账号（绑定到公司，分角色）                          │
│     ├─ 主管会计 Senior Accountant — 全权                  │
│     ├─ 记账员 Bookkeeper         — 录入+编辑              │
│     ├─ 审核员 Reviewer           — 确认 JE+关账           │
│     └─ 查询员 Viewer             — 只读                   │
└──────────────────────────────────────────────────────────┘
```

> **概念澄清**：
> - **租户 (Tenant)** = 计费主体、订阅方（一个会计师事务所是一个租户）
> - **公司 (Company)** = 法人主体（一个会计师事务所下挂多个客户公司）
> - **账套 / 账簿 (Book)** = 同一公司可有多套账（HK 极少见但允许：经营账、税务调整账、合并报表账）
> - **员工 (Employee)** = 持有登录账号的用户，归属租户，授权到一个或多个公司

---

## 二、租户管理模块

### 2.1 功能清单总览

| 子模块 | 超管 | 租户管理员 | 描述 |
|---|:---:|:---:|---|
| 租户 CRUD | ✓ | — | 新建/暂停/恢复/删除租户 |
| 套餐配置 | ✓ | — | 选套餐、改配额、设折扣 |
| 用量监控 | ✓ | ✓ | Token 消耗、API 调用、存储 |
| 计费账单 | ✓ | ✓ | 月账单、明细、发票 |
| Top-up | — | ✓ | 自助充值 Token |
| 公司管理 | ✓ | ✓ | 在租户内增减公司，受配额限制 |
| 员工管理 | ✓ | ✓ | 邀请员工，分配公司+角色 |
| 审计日志 | ✓ | ✓ | 谁、什么时间、改了什么 |

### 2.2 套餐与计费模型

#### 套餐设计

| 套餐 | 月费 (HKD) | 公司数 | 员工账号 | Token 含 | 适用 |
|---|---|---|---|---|---|
| **Trial 试用** | 0 | 1 | 2 | 5,000 | 体验，14 天 |
| **Starter** | 380/月 | 3 | 5 | 50,000 | 独立簿记员 |
| **Professional** | 980/月 | 10 | 15 | 200,000 | 小型 CPA 行 |
| **Firm** | 2,580/月 | 50 | 50 | 800,000 | 中型 CPA 行 |
| **Enterprise** | 商谈 | 不限 | 不限 | 按需 | 大型事务所 / 集团 |

#### Token 计量规则

| AI 能力 | 单位 | 单价（Token） | 说明 |
|---|---|---|---|
| 银行流水 OCR | 每页 | 100 | PDF/Excel 解析 |
| 票据 OCR | 每张 | 50 | JPG/PNG/PDF |
| AI 智能匹配 | 每笔流水 | 30 | 流水↔票据匹配 |
| AI 科目推荐 | 每条 JE | 20 | 给出建议借贷科目 |
| AI 期末调整生成 | 每条 ADJ | 200 | 折旧/应计/税务等 |
| AI 异常检测 | 每月 | 500 | A1-A13 异常扫描 |
| AI 财务分析报告 | 每份 | 2,000 | 月度经营总结 |
| 智能问答（Q&A） | 每次 | 100 | 老板自然语言查账 |

**超额规则**：当月超出后按 HKD 0.005 / Token 后付费；或自助 Top-up 包（10万 Token = HKD 380，无限期）。

### 2.3 数据模型（新增表）

```python
class Tenant:
    id, name, business_type, contact_name, contact_email, contact_phone,
    br_no, status, plan_id, plan_started, plan_expires,
    token_balance, token_topup, created_at, notes

class Plan:
    id, name, price_hkd, max_companies, max_users,
    monthly_token, features, is_active

class User:
    id, tenant_id, email, name, phone, password_hash,
    role, status, last_login, created_at

class UserCompanyAccess:
    user_id, company_id, role_in_company, granted_at, granted_by

class Company:
    id, tenant_id, name, br_no, fy_start_month, base_currency,
    industry, status, created_by, created_at

class Book:
    id, company_id, name, book_type, status, is_default

class TokenUsage:
    id, tenant_id, company_id, user_id, feature, tokens, api_ref, created_at

class Invoice:
    id, tenant_id, period, plan_fee, overage_tokens, overage_fee,
    total, status, paid_at, issued_at

class AuditLog:
    id, tenant_id, user_id, action, target_type, target_id,
    payload, ip, user_agent, created_at
```

### 2.4 关键流程

#### 流程 A：超管创建新租户
```
1. 超管后台 → 新建租户
2. 填写：租户名 / 业务类型 / 联系人 / BR No / 选套餐
3. 系统：
   ├── 生成租户 ID (T-2026-NNNN)
   ├── 创建租户管理员账号（自动）
   ├── 发邀请邮件（含临时密码，首次登录改密）
   ├── 初始化 Token 余额 = 套餐月度配额
   └── 写审计日志
4. 租户管理员登录 → 引导：创建第一个公司 → 选 COA 模板（HK SME-FRS）→ 上传开账 TB
```

#### 流程 B：租户内邀请员工 + 分配公司权限
```
租户管理员 → 员工管理 → 邀请员工
    │
    ├─ 填邮箱 + 选角色（senior / bookkeeper / reviewer / viewer）
    ├─ 勾选可访问的公司（一个或多个）
    │       │
    │       └─→ 对每个公司可单独指定角色（可覆盖租户角色）
    │
    └─→ 发邀请邮件 → 员工首次登录设密 → 自动绑定公司
```

#### 流程 C：Token 消耗与超额
```
任何 AI 调用前：
  ├─ 计算预估 Token 消耗
  ├─ 检查 Token 余额（月度 + Top-up）
  │
  ├─ 余额充足 → 扣减 → 写 token_usage → 执行 AI 调用
  │
  └─ 余额不足 →
      ├─ 提示"本月配额已用尽，剩余 X Token"
      ├─ 选项 1：升级套餐
      ├─ 选项 2：购买 Top-up 包
      └─ 选项 3：开启超额后付费（需租户管理员事先授权）
```

### 2.5 接口设计（增量）

```
# 超管端 /api/admin/*
GET    /api/admin/tenants                    租户列表 + 用量摘要
POST   /api/admin/tenants                    新建租户
PATCH  /api/admin/tenants/{id}               改套餐 / 状态 / 配额
DELETE /api/admin/tenants/{id}               停用（软删除）
GET    /api/admin/tenants/{id}/usage         详细用量
POST   /api/admin/tenants/{id}/grant-tokens  超管手动赠送 Token
GET    /api/admin/plans                      套餐列表
POST   /api/admin/plans                      新建套餐

# 租户端 /api/tenant/*
GET    /api/tenant/me                        当前租户信息
GET    /api/tenant/usage                     本期 Token 用量曲线
POST   /api/tenant/topup                     发起 Top-up
GET    /api/tenant/invoices                  月度账单列表
GET    /api/tenant/audit-log                 操作审计

# 员工管理
GET    /api/users
POST   /api/users/invite                     邀请新员工
PATCH  /api/users/{id}                       改角色 / 状态
DELETE /api/users/{id}
POST   /api/users/{id}/companies             分配公司
DELETE /api/users/{id}/companies/{cid}       撤销公司授权

# 公司管理
GET    /api/companies
POST   /api/companies                        新建（受配额限制）
PATCH  /api/companies/{id}
DELETE /api/companies/{id}                   归档

# 账套
GET    /api/companies/{cid}/books
POST   /api/companies/{cid}/books            新建账套
```

### 2.6 异常场景

| 编号 | 触发 | 处理 |
|---|---|---|
| T1 | 租户欠费 > 7 天 | 自动暂停 AI 功能，保留只读 |
| T2 | 租户超出公司配额 | 新建公司被拒，引导升级 |
| T3 | 员工被撤销公司授权但当前正在操作 | 操作中断，强制刷新 |
| T4 | 同邮箱在多个租户被邀请 | 允许，登录后选择租户 |
| T5 | 租户管理员误删自己 | 系统阻止：租户至少保留 1 名 admin |
| T6 | Token 在并发 AI 调用下竞争扣减 | 数据库事务 + 行锁 |
| T7 | 删除公司时存在未关账期间 | 提示需先关账或归档 |
| T8 | 跨租户数据泄露 | 所有查询强制 `WHERE tenant_id = current_tenant` |

---

## 三、账簿管理模块

### 3.1 设计理念

香港会计实务中，"账簿（Books of Account）"是 **CO Section 373** 法定要求保留 7 年的核心档案，分两层：

```
┌─────────────────────────────────────────────────────┐
│ Level 1 — 总账 General Ledger                       │
│   • 按科目汇总，TB 的来源                            │
├─────────────────────────────────────────────────────┤
│ Level 2 — 明细账 / 辅助账 Subsidiary Ledgers        │
│   • 按业务维度拆细                                   │
└─────────────────────────────────────────────────────┘
```

### 3.2 账簿清单

| # | 账簿名 | 中文 | 用途 | 数据来源 |
|---|---|---|---|---|
| L1 | General Ledger | 总账 | 所有科目余额变动 | ENTRIES + ADJ |
| L2 | Cash Book | 现金日记账 | 库存现金/Petty Cash 进出 | CASH_DATA(1001/1003-*) |
| L3 | Bank Book | 银行日记账 | 每个银行账户一本 | BK_LIST + ENTRIES(1002-*) |
| L4 | Sales Day Book | 销售簿 | 收入侧票据流水 | INV_DATA(income) |
| L5 | Purchase Day Book | 采购簿 | 支出侧票据流水 | INV_DATA(expense) |
| L6 | AR Ledger | 应收账款明细账 | 按客户挂账 | 1100 + 收款流水 |
| L7 | AP Ledger | 应付账款明细账 | 按供应商挂账 | 2100 + 付款流水 |
| L8 | Fixed Asset Register | 固定资产登记簿 | 资产清单 + 折旧 | 1600-* + 折旧 ADJ |
| L9 | Director's Current A/C | 董事往来明细账 | HK SME 极高频 | 2251-01 流水 |
| L10 | MPF Ledger | MPF 强积金明细账 | 雇主+雇员供款 | 6230 + 2150 |
| L11 | Petty Cash Book | 备用金账本 | 现金小额支出 | 1003-01 流水 |
| L12 | Journal Ledger | 日记总账 | 所有 JE 的时序流水 | ENTRIES |
| L13 | Inventory Ledger | 存货明细账 | 进销存 | 1300-* |
| L14 | Tax Ledger | 税务备查账 | 利得税/薪俸税/印花税 | 7100 + 2200 |

### 3.3 账簿模型

```python
class LedgerBook:
    id, company_id, book_id, code, name_en, name_zh,
    scope_filter, is_system

class LedgerEntry:   # 虚拟视图
    book_id, txn_date, voucher_no, reference, description,
    debit, credit, balance, source_type, source_id

class PeriodLock:
    company_id, book_id, period, locked_at, locked_by, can_unlock
```

### 3.4 关键流程

#### 流程 D：账簿浏览（钻取链路）
```
TB → 点击科目 → 跳转对应账簿 → 显示当月明细
                 │
                 └─→ 点击行 → JE 详情 → 关联票据原件 + 审计日志
```

#### 流程 E：月度关账
```
校验：① TB 平衡 ② JE 全 confirmed ③ ADJ 全 confirmed
      ④ AR/AP 对账 ⑤ 银行对账
       ▼
审核员触发"关账" → PeriodLock → 当期凭证锁定 → 生成 PDF 归档包
```

#### 流程 F：审计抽凭
```
审计师 → 按凭证号/金额/科目抽样 → 一键 Excel 导出
                                  （HKICPA HKSA 530 抽样格式）
```

### 3.5 香港特色合规要求

| 法规 | 要求 | 系统实现 |
|---|---|---|
| CO S373 | 账簿保留 7 年 | 软删除 + 自动归档 |
| CO S622 | 法定审计前不可篡改 | PeriodLock + 不可变 JE |
| IRO S51C | 完整业务记录 | 每笔 JE 必有源单据 |
| AMLO | 大额交易留痕 | 大额预警 A11 |
| MPFSO | MPF 记录 7 年 | MPF Ledger 自动生成 |
| SDO | 印花税记录 | 7100 子科目 + Tax Ledger |
| PDPO | 个人资料保密 | Viewer 角色屏蔽敏感字段 |

### 3.6 接口设计（增量）

```
GET    /api/books
GET    /api/books/{code}
GET    /api/books/{code}/entries?period=...&from=...&to=...
GET    /api/books/{code}/balance
GET    /api/books/{code}/export?format=xlsx|pdf|csv

GET    /api/books/ar/aging
GET    /api/books/ap/aging
POST   /api/books/ar/{invoice_id}/receive

GET    /api/books/fa/assets
POST   /api/books/fa/assets
POST   /api/books/fa/depreciate

POST   /api/books/bank/{acct}/reconcile

POST   /api/periods/{period}/lock
POST   /api/periods/{period}/unlock
GET    /api/periods/{period}/archive
```

### 3.7 异常场景

| 编号 | 触发 | 处理 |
|---|---|---|
| L1 | 已关账期间新增 JE | 拒绝，引导记入下期或申请解锁 |
| L2 | Bank Book 余额 ≠ 银行月结单 | 对账模块显示差异 |
| L3 | AR Ledger 负余额 | 警告，检查是否记错方向 |
| L4 | 固定资产折旧月数已满仍在折 | 自动停止 + 提醒处置 |
| L5 | DCA 余额 > HKD 200,000 | 提醒 IRD 隐性分红风险 |
| L6 | MPF 雇主供款 < 雇员供款 | 警告（上限 5%） |
| L7 | 跨期凭证 | 提示是否暂估应计 |
| L8 | 删除已生成账簿条目的 JE | 阻止，仅允许冲销 |

---

## 四、与现有模块的耦合改动

### 4.1 全局上下文
```
X-Tenant-Id   : T-2026-0001
X-Company-Id  : ABC
X-Book-Id     : BK-ABC-MAIN
Authorization : Bearer <jwt>
```

### 4.2 已有接口改造

| 接口 | 改造 |
|---|---|
| `GET /api/coa` | 加 `?company_id=...` 强制隔离 |
| `POST /api/cash-entries` | 自动写 tenant_id + company_id + created_by |
| `GET /api/trial-balance` | 按 book_id 过滤；关账后只读 |
| `POST /api/journals` | 检查 PeriodLock；写 audit_log |
| 所有 AI 写接口 | Token 计费 middleware |

### 4.3 前端导航变化

```
普通用户：[工作台] [采集解析] [AI 记账] [账簿]★ [报表] [设置]
超级管理员：[租户管理] [套餐管理] [账单] [用量监控] [审计日志]
```

---

## 五、实施路线

| 阶段 | 周期 | 交付物 |
|---|---|---|
| P1 多租户基础 | 2 周 | Tenant/User/Company 表 + JWT + 中间件 + 简易后台 |
| P2 计费体系 | 2 周 | Plan/TokenUsage/Invoice + 套餐升降级 + Top-up |
| P3 账簿读视图 | 3 周 | GL/Cash/Bank/Sales/Purchase 5 本账 + 钻取 |
| P4 辅助账 | 2 周 | AR/AP/DCA/MPF/Petty Cash |
| P5 固定资产 + 关账 | 2 周 | FA Register + 折旧自动化 + PeriodLock |
| P6 审计与导出 | 1 周 | PDF 归档包 + Excel 导出 + 审计日志查询 |
| P7 合规与权限细化 | 1 周 | AMLO 预警 + RBAC 完善 + 数据隔离测试 |

总工期：~13 周 / 1 名后端 + 1 名前端 + 0.5 PM

---

## 六、非功能性需求

| 维度 | 指标 |
|---|---|
| 数据隔离 | 跨租户漏查询 = 0 |
| 性能 | 账簿明细 10万行查询 < 1.5s |
| 可用性 | 99.5%（单节点 + 每日全量备份） |
| 审计完整性 | 任何写操作必留 audit_log |
| 归档可恢复 | 7 年内任意期间归档可一键还原 |
| Token 计费 | 误差 < 0.5% |

---

*文档版本：v3.0 增量 · 2026-06-09 · 与 v2.0 PRD 配合使用*
