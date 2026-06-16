# Leapexbiz 管理后台 — 技术开发文档 v1.0

> **配套**：《PRD_Leapexbiz管理后台_v1.0》
> **更新**：2026-06-11
> **目标读者**：后端 / 前端 / DevOps 工程师
> **基线**：沿用已部署的 FastAPI + SQLModel + SQLite 技术栈（124.221.97.241），生产化平滑迁移 PostgreSQL。

---

## 一、系统架构

```
┌────────────────────────────────────────────────────────────────┐
│ 客户端                                                          │
│  ┌──────────────────────┐     ┌────────────────────────────┐  │
│  │ Leapexbiz 微信小程序  │     │ 管理后台 Web SPA           │  │
│  │ (WXML/WXSS/JS 或 Taro)│     │ (Vue3/React + Element/Antd)│  │
│  └──────────┬───────────┘     └──────────────┬─────────────┘  │
└─────────────┼─────────────────────────────────┼────────────────┘
              │ HTTPS / JWT                      │ HTTPS / JWT + RBAC
              ▼                                  ▼
┌────────────────────────────────────────────────────────────────┐
│ API 网关 (Nginx 反代 + TLS)                                     │
├────────────────────────────────────────────────────────────────┤
│ 应用层  FastAPI (Python 3.11)                                   │
│  ├ 鉴权/RBAC 中间件   ├ 业务路由(client / admin)                │
│  ├ 计费/佣金/印花税服务  ├ 通知服务  ├ PDF 渲染服务(Puppeteer)   │
│  └ 审计日志(哈希链)   └ 文件加密上传                            │
├────────────────────────────────────────────────────────────────┤
│ 数据层                                                          │
│  ├ PostgreSQL (生产) / SQLite (MVP)   主业务库                  │
│  ├ Redis        会话/限流/异步队列                              │
│  ├ 对象存储 OSS/S3(SSE 加密)  证件/回单/交付物 PDF              │
│  └ 备份         每日增量 + 每周全量                             │
├────────────────────────────────────────────────────────────────┤
│ 外部集成                                                        │
│  邮件(SendGrid/SES/阿里云) · 微信(login/订阅消息) · 快递100      │
│  · 海外聚合收款(连连/后续) · iCRIS/IPD(MVP 人工，后续 API)      │
└────────────────────────────────────────────────────────────────┘
```

### 技术选型

| 层 | MVP | 生产 |
|---|---|---|
| 后端 | FastAPI + SQLModel | 同 + Alembic 迁移 |
| 数据库 | SQLite | PostgreSQL 15 |
| 缓存/队列 | 内存 | Redis（会话、限流、Celery/RQ 异步） |
| 文件 | 本地加密目录 | OSS/S3 + SSE-KMS |
| 后台前端 | — | Vue3 + Element Plus / React + Antd Pro |
| 小程序 | 原生 / Taro | 同 |
| PDF | Puppeteer (Node 旁路服务) | 同，容器化 |
| 鉴权 | JWT（access 1h + refresh 7d） | 同 + 2FA（管理端） |

---

## 二、数据模型（核心表）

> 命名 snake_case；金额 `DECIMAL(12,2)`；敏感字段 AES-256 加密存储；所有表含 `created_at/updated_at`。

### 2.1 ER 关系（简）

```
channel 1───* customer 1───* kyc_record
customer 1───* company 1───* deliverable
customer 1───* order 1───* bill 1───1 payment
order  *───1 channel        order *───1 service_type
channel 1───* channel_pricing / channel_commission
supplier 1───* supplier_task / supplier_bill
admin_user *───* role (RBAC)        * audit_log
company 1───1 scr_register
```

### 2.2 关键表

```python
# ── 客户与合规 ──
customer(id, openid, name, email_verified, phone, channel_code,
         source['channel'|'organic'], kyc_status, tags[], created_at)

kyc_record(id, customer_id, type['individual'|'company'],
           id_doc_type['hkid'|'cn_id'|'passport'], id_doc_files[],   # 加密
           address_proof_files[], business_nature, fund_source,
           is_pep, pep_relations, sanction_hit, edd_required,
           status['draft'|'submitted'|'reviewing'|'approved'|'edd_required'|'rejected'|'frozen'],
           reject_reason, reviewed_by, reviewed_at,
           retention_until)                                          # = submit + 7y

name_check(id, customer_id, name_en, name_zh, stage, risk_level['G'|'Y'|'O'|'R'|'B'],
           similar_hits[], ipd_screenshot, icris_screenshot,
           locked_until, recheck_count, free_quota=3, status)

scr_register(id, company_id, controllers[json], last_updated_by, last_updated_at)

# ── 公司与交付 ──
company(id, customer_id, name_en, name_zh, ci_no, br_no, reg_date,
        articles_type['A'|'B'|'custom'], status['registering'|'active'|'ar_due'|'ar_overdue'|'deregistered'],
        next_ar_date, directors[json], members[json])

deliverable(id, company_id, order_id, seq, name, category,
            gen_type['pdf'|'manual'|'physical'], file_url, courier_no,
            visible_to_client, supplier_task_id?, status, version)

# ── 订单/账单/支付 ──
service_catalog(key, name, std_price, deliverable_count, kyc_trigger, active)

order(id, no['ORD-..'], customer_id, company_id?, service_type, channel_code,
      status['待支付'|'服务中'|'已完成'|'已取消'], total_amount, created_at)

bill(id, no['LEA-..'], order_id, service_item, amount,
     status['待支付'|'待确认'|'已到账'|'已驳回'|'已作废'],
     stamp_duty, generated_at, paid_at, expired_at, reopen_count)

payment(id, bill_id UNIQUE, method, proof_url, confirmed_by, confirmed_at,
        remark, refund_status?, refund_approved_by?)               # 1:1

# ── 渠道/定价/佣金 ──
channel(code, partner_name, status, created_at)
channel_pricing(id, channel_code, service_key, price?, discount_rate?,
                effective_from, effective_to)                       # 留空继承标准价
channel_commission(id, channel_code, service_key, rate,
                   effective_from, effective_to)
commission_ledger(id, channel_code, order_id, service_key, base_amount,
                  rate, commission, period, settle_status['待结算'|'已结算'], settled_at)

# ── 供应商 ──
supplier(id, name, contact, email, service_types[], status['active'|'suspended'])
supplier_task(id, supplier_id, deliverable_id, order_ref, desc, due_date,
              status['待接收'|'进行中'|'已上传'|'已确认'|'已驳回'], file_url)
supplier_bill(id, no['SUP-..'], supplier_id, service_desc, related_orders[],
              amount, period, settle_status, settled_at, remark)

# ── 线索/工单（企微承接）──
lead(id, customer_id?, source['svc_detail'|'order_confirm'|'fab'|'partner'],
     intent_service, status['待跟进'|'跟进中'|'已转化'|'关闭'], owner, notes[])

# ── 平台账号/权限/审计/通知/配置 ──
admin_user(id, email, name, password_hash, role, status, last_login,
           channel_code?, supplier_id?, twofa_enabled)
role(key, name, permissions[json])
audit_log(id, actor_id, action, target_type, target_id, payload[json],
          prev_hash, hash, ip, ua, created_at)                      # 哈希链
notification(id, customer_id, channel['sub'|'inapp'|'email'], template_key,
             payload, status, sent_at, read_at)
system_config(key, value, updated_by, updated_at)
```

### 2.3 不可篡改审计日志（哈希链）
`hash = SHA256(prev_hash + actor + action + target + payload + created_at)`。每条引用上一条 `hash`，篡改任一条则后续校验失败。定期把链尾 hash 外部存证。

---

## 三、API 设计

### 3.1 约定
- RESTful；前缀：客户端 `/api/client/*`，后台 `/api/admin/*`。
- 鉴权：`Authorization: Bearer <JWT>`；JWT 含 `sub, role, channel_code?, supplier_id?`。
- RBAC：路由级 `@require(perm)` 依赖；数据级按 `role` 过滤（渠道仅归属、供应商仅自己）。
- 统一响应：`{code, message, data}`；分页 `?page&size`；错误用标准 HTTP 状态。

### 3.2 客户端 API（小程序）
```
POST /api/client/auth/login          wx.login code → openid → JWT
GET  /api/client/channels/{code}     渠道码校验
POST /api/client/kyc                  提交 KYC
POST /api/client/name-check           提交核名
GET  /api/client/services             服务目录（按渠道码返回渠道价）
POST /api/client/orders               下单（生成订单+账单）
POST /api/client/bills/{no}/proof     上传回单
GET  /api/client/companies            我的企业
GET  /api/client/companies/{id}/deliverables  交付物中心
POST /api/client/leads                问顾问/预约咨询（企微线索）
GET  /api/client/messages             站内信
POST /api/client/subscribe            requestSubscribeMessage 回执
```

### 3.3 后台 API（节选）
```
# 鉴权/权限
POST /api/admin/auth/login            邮箱+密码(+2FA) → JWT
GET  /api/admin/me/permissions

# 运营审核
GET  /api/admin/kyc?status=submitted
POST /api/admin/kyc/{id}/approve|reject|request-more|mark-edd
GET  /api/admin/name-check?status=pending
POST /api/admin/name-check/{id}/result   上传查册+风险评级+锁定
GET  /api/admin/orders   POST /api/admin/orders/{id}/note
GET  /api/admin/bills?status=待确认
POST /api/admin/bills/{no}/confirm|reject       回单确认/驳回(Finance)
POST /api/admin/bills/{no}/void|reopen|refund   作废/重开/退款(审批)
POST /api/admin/bills                          手动生成账单
GET  /api/admin/deliverables  POST .../{id}/upload|courier

# 定价/渠道/佣金
GET/PUT /api/admin/pricing-matrix
GET/PUT /api/admin/commission-matrix
GET  /api/admin/commission-ledger?period=2026-06
POST /api/admin/commission-ledger/{id}/settle

# 供应商
GET/POST /api/admin/suppliers
POST /api/admin/supplier-tasks            派发
GET  /api/admin/supplier-tasks (supplier 视角仅自己)
POST /api/admin/supplier-tasks/{id}/upload|confirm|reject
GET/POST /api/admin/supplier-bills  POST .../{id}/settle

# 线索/合规/系统
GET/POST /api/admin/leads  POST /api/admin/leads/{id}/follow
GET  /api/admin/compliance/sanctions  POST .../update
GET  /api/admin/compliance/reports
GET  /api/admin/scr/{company_id}  PUT .../update
GET  /api/admin/audit-log
GET/PUT /api/admin/system-config
GET  /api/admin/dashboard/kpi|trends|todos
```

---

## 四、关键流程时序

### 4.1 回单确认 → 服务启动
```
客户上传回单 → bill.status=待确认 → 待办推 Finance
Finance 核对银行入账 → confirm → payment 写入 → bill=已到账
→ order=服务中 → 生成 commission_ledger(应付佣金) → 通知客户 + 触发交付流程
（驳回 → bill=已驳回 → 通知客户重传）
```

### 4.2 KYC 审核（含制裁）
```
提交 → reviewing → 制裁筛查
  命中 → frozen → 合规复核 → 解冻/上报(STR)
  未命中 → 人工审核 → approved / request-more / reject(留档7y)
  PEP/高风险 → edd_required → 补资料 → 合规二审
```

### 4.3 月度佣金结算
```
月末 Cron → 汇总 commission_ledger(period) → 渠道应付台账
→ 渠道Admin 后台查看 → 线下转账 → Finance 标记已结算 → 审计留痕
```

### 4.4 交付物（含供应商）
```
order=服务中 → 并行：PDF 自动渲染(12项) / 政府文件等待 / 派供应商任务(印章等)
供应商上传 → 运营确认 → deliverable=就绪 → 全部就绪 → 通知客户(交付物中心可见)
```

---

## 五、安全与合规实现

| 要求 | 实现 |
|---|---|
| 字段加密 | AES-256-GCM 加密 id_doc/address/UBO；密钥走 KMS/环境隔离 |
| 传输 | 全站 HTTPS/TLS 1.3（Nginx + certbot） |
| 鉴权 | JWT + refresh 轮换；管理端强制 2FA；失败锁定 |
| RBAC | 路由级 + 数据级双重；供应商/渠道强隔离 |
| 审计 | 写操作哈希链，不可篡改，7 年留存 |
| 数据保存 | KYC（含被拒）7 年；到期前不可物理删除 |
| 备份 | 每日增量 + 每周全量；异地副本 |
| PDPO | 客户数据查阅/更正/导出接口 |
| 防爆破/限流 | Redis 限流；敏感操作二次确认 |

---

## 六、部署

### 6.1 沿用现有（MVP）
```
腾讯云轻量 (124.221.97.241)
 ├ systemd: leapexbiz.service  → uvicorn :8080
 ├ Nginx 反代 :80/:443 → :8080
 └ SQLite + 本地加密文件目录
开发期：微信开发者工具勾「不校验合法域名」直连后端联调。
```

### 6.2 生产化清单
- DB：SQLite → PostgreSQL（Alembic 迁移），连接池。
- 文件：本地 → OSS/S3 + SSE-KMS。
- 会话/队列：引入 Redis；PDF/通知异步化（Celery/RQ）。
- 备案：小程序上线需 ICP 备案域名 + HTTPS。
- 监控：日志聚合 + 健康检查 + 告警；DB 慢查询。
- CI/CD：镜像化（Docker），蓝绿/滚动发布。

### 6.3 环境变量（节选）
`DATABASE_URL · JWT_SECRET · AES_KEY(KMS) · REDIS_URL · OSS_* · WX_APPID/SECRET · MAIL_PROVIDER_KEY · STAMP_DUTY_RATE=0.002`

---

## 七、与小程序的接口契约（要点）
- 小程序 `wx.login` → 后端换 openid，首登绑定 customer。
- 服务目录按 JWT 里的 `channel_code` 返回**渠道专属价**；无则标准价。
- 下单原子事务：建 order + bill（首付/尾款）+ 写 channel 归属。
- 回单上传走对象存储直传（后端签发临时凭证），仅存 file_url。
- 通知：状态变更经 notification 表 → 订阅消息/站内信/邮件三通道下发。

---

## 八、里程碑（与 PRD 优先级对齐）

| 阶段 | 周期 | 内容 |
|---|---|---|
| M1 | 2 周 | 鉴权 RBAC + 客户 + KYC 审核 + 核名 + 订单/账单/回单 + Dashboard |
| M2 | 2 周 | 交付物 + 定价矩阵 + 渠道/佣金台账 + 通知 + 审计 |
| M3 | 2 周 | 供应商 + 任务 + 应付 + 年审任务 + 企微线索 |
| M4 | 1.5 周 | 合规报告/STR + SCR + 印花税 + 退款审批 + 生产化(PG/OSS/Redis) |

---

*技术开发文档 v1.0 · 2026-06-11 · 配套《PRD_Leapexbiz管理后台_v1.0》*
