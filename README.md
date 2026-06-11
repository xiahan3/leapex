# Leapex 利柏思商务

香港中小企业服务平台，含两条产品线：

- **Part A · 会计做账**（Web 后台）— 票据 AI 解析、银行流水对账、JE/试算平衡/财务报表、账簿、多租户/计费
- **Part B · TCSP 公司秘书**（微信小程序原型）— KYC / 核名 / NNC1 注册 / 交付物中心

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
| `/` | Leapex Web 主应用（会计做账） |
| `/tcsp` | TCSP 公司秘书小程序原型 |
| `/docs` | FastAPI Swagger API 文档 |
| `/api/health` | 健康检查 |

## 目录结构

```
backend/
├── main.py          FastAPI 应用 + 30+ REST 接口
├── db.py            SQLite 引擎
├── models.py        SQLModel 数据表
├── seed.py          种子数据
├── data/            COA 科目表种子
└── static/          前端 (index.html, tcsp.html)
deploy/
└── leapex.service   systemd 单元
docs/                PRD 需求文档 (v3.0 / v3.1 / v3.2 / TCSP)
```

## 部署

见 `deploy/leapex.service`。SQLite 数据库 (`backend/leapex.db`) 为运行时生成，不纳入版本管理。
