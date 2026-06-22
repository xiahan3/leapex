# EasybookX

香港中小企业服务平台，含两条产品线：

- **Part A · 会计做账**（Web 后台）— 票据 AI 解析、银行流水对账、JE/试算平衡/财务报表、账簿
- **平台管理**（超管控制台）— 租户/员工/套餐/账单收款/用量/审计日志（已后端持久化）
- **AI 审计报告** — 选企业 → 抓平台数据 → 生成审前分析/审计辅助报告（HKFRS/SME-FRS/HKSA）

> Part B · TCSP 公司秘书（Leapexbiz 小程序 + 管理后台）已迁出至独立仓库 [`leapex_Leapexbiz`](https://github.com/xiahan3/leapex_Leapexbiz)。

## 技术栈

- 后端：FastAPI + SQLModel + SQLite
- 前端：原生 HTML/CSS/JS（单文件原型）
- 部署：systemd + uvicorn

## 本地运行

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8080 --app-dir ..
```

首次启动自动建表并写入种子数据（`backend/seed.py`）。

## 访问

| 路径 | 内容 |
|---|---|
| `/` | EasybookX Web 主应用（会计做账） |
| `/docs` | FastAPI Swagger API 文档 |
| `/api/health` | 健康检查 |

## 目录结构

```
backend/
├── main.py          FastAPI 应用 + 50+ REST 接口（会计 + 平台管理 + 审计报告）
├── db.py            SQLite 引擎
├── models.py        SQLModel 数据表（会计 + Tenant/TenantUser/Plan/BillingInvoice/AuditReport）
├── seed.py          种子数据
├── data/            COA 科目表种子
└── static/          前端 (index.html)
deploy/
├── easybookx.service     systemd 单元
├── nginx_easybookx.conf  Nginx 反向代理
├── setup_server.sh       服务器端一键安装/更新
└── remote_deploy.sh      本地 → 服务器 一键 rsync 部署
docs/                PRD（平台管理 / 审计报告 + 提示词 / v3.x / TCSP）
```

## 平台管理 / 审计报告 API（节选）

| 资源 | 接口 |
|---|---|
| 租户 | `GET/POST /api/tenants`，`PATCH/DELETE /api/tenants/{id}` |
| 平台员工 | `GET/POST /api/tenant-users`，`PATCH/DELETE /api/tenant-users/{id}` |
| 套餐 | `GET/POST /api/plans`，`PATCH/DELETE /api/plans/{key}` |
| 平台账单 | `GET/POST /api/billing-invoices`，`PATCH/DELETE /api/billing-invoices/{no}` |
| 审计报告 | `GET/POST /api/audit-reports`，`DELETE /api/audit-reports/{no}` |

> 前端核心模块启动时从后端 `hydrate`，变更即持久化；后端不可达时回退本地演示数据。
> AI 审计报告的生成逻辑当前为前端模拟（演示用），生成记录持久化到 `audit_report` 表。

## 部署到腾讯云服务器

**方式一 · 本地一键远程部署（推荐）**
```bash
# 在开发机执行，rsync 代码到服务器并自动安装
SSH_TARGET=root@<服务器IP> SSH_KEY=~/.ssh/id_rsa bash deploy/remote_deploy.sh
```

**方式二 · 服务器端手动**
```bash
# 将代码放到 /opt/easybookx 后
sudo bash /opt/easybookx/deploy/setup_server.sh
```

脚本会：安装 python3/venv/nginx → 建 venv 装依赖 → 注册并启动 `easybookx` systemd 服务（:8080）→ 配置 Nginx 反代（:80）→ 健康检查。

**注意事项**
- 腾讯云【安全组】需放行 `80`（及 HTTPS 的 `443`）。
- HTTPS：`sudo certbot --nginx -d your-domain.com`。
- SQLite 数据库 (`backend/easybookx.db`) 运行时生成，不纳入版本管理；首次启动自动建表 + 写入种子。
