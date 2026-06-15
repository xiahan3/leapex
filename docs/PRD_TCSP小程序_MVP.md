# EasybookX TCSP 公司秘书小程序 — MVP 需求文档（产品/技术版）

> **定位**：基于客户 V2.2 需求文档的 MVP 实现版，聚焦微信小程序客户端主线
> **更新**：2026-06-11
> **来源**：6.11-EasybookX_TCSP_需求文档.md（V2.2）
> **作者**：产品 + HK 财务/合规理解整合

---

## 〇、产品定位与 EasybookX 全局关系

### 0.1 两条产品线（重要边界）

EasybookX 是一个多产品线的香港中小企业服务平台。本小程序属于 **Part B**：

```
┌──────────────────── EasybookX 平台 ────────────────────┐
│                                                      │
│  Part A · 会计做账（已有）        Part B · 公司秘书（本项目）│
│  ┌────────────────────┐          ┌────────────────────┐ │
│  │ 票据 AI 解析/对账    │          │ TCSP 公司秘书服务   │ │
│  │ 银行流水/JE/TB/报表  │          │ KYC/核名/注册/年审  │ │
│  │ 形态：Web 后台       │          │ 形态：微信小程序     │ │
│  │ 用户：会计师/记账员  │          │ 用户：终端企业客户   │ │
│  └────────────────────┘          └────────────────────┘ │
│            │                              │              │
│            └──────────┬───────────────────┘              │
│                       ▼                                  │
│         共用：租户/账号体系 · 账单支付模型 · 合规存档     │
└──────────────────────────────────────────────────────────┘
```

> V2.2 附录 A 第 1 条已明确："Part A 票据 AI 解析与对账系统与 TCSP 设计无关，独立存放。"
> **但两者在底层共享**：① 多租户/RBAC（见 EasybookX v3.0/v3.1）② 账单支付模型（见 EasybookX v3.2，与本文档第 12 章 1:1 映射完全一致）③ 7 年合规存档与审计日志。

### 0.2 复用决策（避免重复造轮子）

| 能力 | 来源 | 复用方式 |
|---|---|---|
| 账单=支付单元、1:1、回单上传+人工确认 | EasybookX v3.2 | 直接复用 Payment/Invoice 状态机，仅业务字段不同 |
| 收款账户配置 | EasybookX v3.2 | 共用 PaymentAccount 表 |
| RBAC 6 角色 | EasybookX v3.1 + V2.2 第13章 | 合并角色字典（新增 Compliance/Channel Admin） |
| 审计日志 7 年 | EasybookX v3.1 | 共用 AuditLog，扩展事件类型 |
| 文件加密存储/PDPO | EasybookX v3.1 | 共用 |

---

## 一、MVP 范围界定

### 1.1 本期做（小程序客户端主线）

```
Channel Code → KYC 5步 → 核名 3阶段 → 签约注册 NNC1 5步(含章程) → 回单支付 → 交付物中心
                                                                         │
                                                              后续管理：年审/变更入口
```

| 模块 | MVP 必做 | 说明 |
|---|:---:|---|
| 小程序框架（4 Tab + wx.login） | ✅ | 首页/服务/消息/我的 |
| Channel Code 渠道入口 | ✅ | 6 位码校验 + 自然流量 |
| KYC 五步向导 | ✅ | AML说明/身份/地址/业务/提交 |
| 核名（前端校验 + 风险评级 + 锁定） | ✅ | iCRIS 人工查册（后台） |
| 签约注册 NNC1 五步 | ✅ | 含章程 Step 3 |
| 章程选择（Sample A/B/自定义） | ✅ | 智能推荐 |
| 回单上传支付 | ✅ | 复用 v3.2 |
| 我的公司 + 交付物中心 | ✅ | 17 项可见交付物 |
| 消息中心（站内信） | ✅ | 订阅消息/邮件后台触发 |

### 1.2 本期不做（后台 / 后续迭代）

- 后台管理系统 13 模块（另立 Web 后台，引用 V2.2 第13章）
- 微信支付/支付宝在线支付（架构预留）
- IPD 商标 API、iCRIS API（MVP 人工）
- 公证认证/银行开户/减资/恢复（V2.2 已标注预留）
- 渠道结算佣金（V2.2 第13.9 已标注不实现）

---

## 二、小程序信息架构（IA）

```
TabBar
├── 首页 Home
│    ├── Channel Code 入口（首个交互项）
│    ├── 核心服务入口卡（新公司注册 / 年审 / 变更）
│    ├── 我的进行中订单（流程进度条）
│    └── 合规提醒 Banner
│
├── 服务 Services
│    ├── 新公司注册（主推）
│    └── 其他 8 项服务（年审/董事变更/秘书变更/地址变更/
│         股份转让/名称变更/股份配发/注销）
│
├── 消息 Messages
│    ├── 合规通知（不可关闭）
│    ├── 流程通知（KYC/核名/支付/交付）
│    └── 年审提醒（6 轮递进）
│
└── 我的 Me
     ├── 我的公司（列表 → 详情 → 交付物中心）
     ├── 我的订单 / 账单
     ├── KYC 状态
     └── 设置（通知订阅 / 隐私 / 关于）

二级流程页（非 Tab）
├── KYC 向导（5 步）
├── 核名（输入 → 评级 → 结果）
├── 签约注册（NNC1 5 步）
│    └── 章程确认（Step 3）
├── 账单详情 + 上传回单
└── 交付物详情（PDF 预览 / 快递追踪）
```

---

## 三、关键流程与状态机

### 3.1 KYC 五步（含合规要点）

| 步骤 | 内容 | 我补充的合规设计 |
|---|---|---|
| 1 AML 合规说明 | AMLO 摘要 + 数据用途 | **必须勾选**才能下一步；记录勾选时间戳入审计 |
| 2 身份认证 | 证件 OCR + 邮箱验证 | 支持 HKID/内地身份证/护照；**邮箱在此采集验证**（通知渠道）；PEP 含家庭成员 |
| 3 地址证明 | 3 个月内账单 | 水/电/煤/银行对账单截图 |
| 4 业务声明 | 业务性质/资金来源 | 下拉+自由填；资金来源用于 EDD 判断 |
| 5 提交审核 | 汇总确认 | **提交后不可改**；命中制裁名单→冻结转人工 |

**KYC 状态机**：
```
draft → submitted → reviewing →┬→ approved（进入核名/注册）
                               ├→ edd_required（PEP/高风险 → 补充资料）
                               └→ rejected（资料存 7 年）
                  命中制裁名单 → frozen（转合规人工）
```

### 3.2 核名三阶段 + 五级风险

```
前端实时校验 ──→ 智能预检(近似名+IPD) ──→ iCRIS人工查册 ──→ 客户决定
   长度/后缀/        Levenshtein≤2          后台截图存档       接受/换名
   字符/敏感词        风险评级
```

**五级风险（颜色 + 处理）**：
| 🟢 Green 无冲突 → 可用 | 🟡 Yellow 轻微近似 → 确认可继续 | 🟠 Orange 近似冲突 → 不混淆声明 | 🔴 Red 商标/敏感词 → 合规审批 | 🔵 Blue 需牌照 → 提供证明 |

**名称锁定 30 天**；免费重查 3 次。

### 3.3 签约注册 NNC1 五步

| Step | 名称 | NNC1 字段 | 数据来源 |
|---|---|---|---|
| 1 公司名称 | 英/中文名 | 核名结果自动填充 |
| 2 地址与股本 | 注册地址 + 股本 | EasybookX 虚拟地址/自选；默认每股 HKD 1.00 |
| 3 确认章程 | 章程选择 | Sample A/B/自定义（智能推荐） |
| 4 董事与秘书 | 董事 + 秘书 | 董事 KYC 复用；秘书=EasybookX 内嵌 |
| 5 创办成员 | 股东/股份分配 | KYC 复用 |

### 3.4 账单与支付（复用 EasybookX v3.2，对齐 V2.2 第12章）

```
待支付 ──客户上传回单──→ 待确认 ──运营核对──→ 已到账 ──自动──→ 服务中
   │                        │
 7天未付→已作废           运营驳回→已驳回→退回待支付
```
- 账单=支付单元，**1:1 映射**（payment.bill_id UNIQUE）
- 新注册支持 **首付款(50%) + 尾款(50%)** 两张独立账单
- 7 天未付自动作废；每订单最多重开 2 次

### 3.5 交付物状态（新注册 19 项 / 客户可见 17 项）

```
服务开始 → PDF并行生成(12) → 政府文件等待(CI/BR) → 人工上传扫描件(3)
        → 实物印章制作(2) → 内部组装快递(1) → 全部就绪 → 通知客户
```
> 完整 19 项 + 其他 8 服务 67 项清单见 V2.2 第 9/10 章，不在此重列。

---

## 四、Channel Code 渠道机制

| 项 | 设计 |
|---|---|
| 位置 | 小程序首页**首个交互项** |
| 格式 | 6 位字母数字混合 |
| 校验 | 实时校验，无效提示"请确认渠道码" |
| 归属 | 注册后标记来源渠道，订单数据归属该渠道 |
| 无码 | 可跳过 → 标记"自然流量"→ 归 EasybookX 直营 |
| 渠道权限 | 渠道伙伴后台**只读**归属客户/订单/收入，不可操作审批 |

---

## 五、通知机制（三渠道 MVP）

| 渠道 | MVP | 说明 |
|---|:---:|---|
| 微信订阅消息 | ✅ | 需用户主动订阅（小程序 requestSubscribeMessage） |
| 站内信 | ✅ | 小程序消息中心 |
| 邮件 | ✅ | KYC Step2 采集邮箱；SendGrid/SES/阿里云 |
| 短信 | ❌ | 后续 |

**年审 6 轮递进**：到期前 60/30/14/7 天 + 当天 + 逾期 7 天。
**合规通知不可关闭**：KYC 结果/核名结果/年审逾期/制裁命中/AML-EDD。

---

## 六、小程序技术方案

| 维度 | 方案 |
|---|---|
| 框架 | 原生小程序（WXML/WXSS/JS）或 Taro（React） |
| 登录 | wx.login → code 换 openid → 绑定 EasybookX 账号 → JWT |
| 后端 | 复用现有 FastAPI（124.221.97.241）；上线需备案域名+HTTPS |
| 文件上传 | wx.chooseMedia/chooseImage → 上传证件/回单 → 后端加密存储 |
| OCR | MVP 后台人工复核；后续接腾讯云/阿里云 OCR |
| PDF 交付物 | 后端 Puppeteer HTML 模板渲染 |
| 订阅消息 | requestSubscribeMessage + 后端 subscribeMessage.send |
| 合规存储 | 敏感字段 AES-256；KYC 7 年留存 |

### 开发期绕过备案（重要）
微信开发者工具勾选"**不校验合法域名/HTTPS**"，开发阶段可直连 `http://124.221.97.241:8080` 跑真数据；上线前再办 ICP 备案 + HTTPS。

---

## 七、数据模型（TCSP 增量，与 EasybookX 共表标注）

```python
class Customer:          # 小程序终端客户（与 EasybookX User 可打通）
    id, openid, name, email(verified), phone, channel_code,
    source('channel'|'organic'), kyc_status, created_at

class KycRecord:
    id, customer_id, type('individual'|'company'),
    id_doc_type('hkid'|'cn_id'|'passport'), id_doc_files,
    address_proof_files, business_nature, fund_source,
    is_pep, pep_relations, sanction_hit, status, reviewed_by,
    retention_until(=submit+7y)   # AMLO

class NameCheck:
    id, customer_id, name_en, name_zh, stage, risk_level,
    similar_hits, ipd_screenshot, icris_screenshot,
    locked_until(=pass+30d), recheck_count, free_quota(=3)

class Order:             # 服务申请单元
    id, customer_id, company_id, service_type, channel_code,
    status, created_at

class Bill:              # 复用 EasybookX v3.2 Invoice
    id, order_id, bill_no('LEA-2026-NNN'), amount, status,
    generated_at, paid_at, expired_at(=gen+7d)

class Payment:           # 复用 EasybookX v3.2 Payment
    id, bill_id(UNIQUE), method, proof_url, confirmed_by,
    confirmed_at, remark

class Company:           # 注册成功后的公司主体
    id, customer_id, name_en, name_zh, ci_no, br_no,
    reg_date, articles_type, directors, members, scr,
    next_annual_return_date

class Deliverable:
    id, company_id, order_id, seq, name, category,
    gen_type('pdf'|'manual'|'physical'), file_url,
    courier_no, visible_to_client, status

class Channel:
    code, partner_name, status, created_at
```

---

## 八、合规红线（HK 法规映射）

| 法规 | 模块 | 系统实现 |
|---|---|---|
| AMLO | KYC/核名/全程 | 尽调+PEP(含家属)+制裁筛查+7年留存 |
| CO Cap.622 | 核名/注册/章程/SCR | NNC1 字段、名称规则、SCR 维护 |
| 电子交易条例 Cap.553 | 全程 | 电子签名/记录效力 |
| TCSP 牌照 | 全程 | 持牌经营、合规审计 |
| PDPO | 全程 | 告知用途、最小化、可查阅更正、AES-256 |

---

## 九、原型 Demo 屏幕清单（本次交付）

小程序形态（手机框 + 微信风格 + 底部 TabBar），含以下可点击屏：

1. 启动/首页（Channel Code 入口 + 服务卡 + 进行中订单）
2. Channel Code 输入（校验动效）
3. 服务大厅（新注册 + 8 服务）
4. KYC 向导 5 步
5. 核名（输入 → 实时校验 → 五级风险结果 → 锁定）
6. 签约注册 NNC1 5 步
7. 章程确认（Sample A/B/自定义 + PDF 预览）
8. 账单详情 + 上传回单
9. 我的公司（列表 + 详情）
10. 交付物中心（17 项 + PDF 预览 + 快递追踪）
11. 消息中心（合规/流程/年审）
12. 我的（资料 + 订单 + KYC 状态 + 设置）

---

## 十、实施排期（MVP）

| 阶段 | 内容 | 周期 |
|---|---|---|
| P0 | 小程序框架 + wx.login + Channel Code + 首页/我的 | 1.5 周 |
| P1 | KYC 5 步 + 文件上传 + 后台审核 | 2 周 |
| P2 | 核名（前端校验+评级）+ 后台 iCRIS 录入 | 1.5 周 |
| P3 | 签约注册 NNC1 5 步 + 章程 | 2 周 |
| P4 | 账单+回单支付（复用 v3.2）+ 收据 | 1 周 |
| P5 | 交付物中心 + PDF 渲染 + 快递追踪 | 1.5 周 |
| P6 | 三渠道通知 + 年审 6 轮递进 | 1 周 |

**合计**：~10.5 周（不含后台管理系统）

---

*文档版本：TCSP 小程序 MVP · 2026-06-11 · 配合客户 V2.2 全量文档使用*
