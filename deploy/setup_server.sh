#!/usr/bin/env bash
# EasybookX · 服务器端一键安装/更新脚本（在腾讯云服务器上执行）
# 适配 Ubuntu/Debian (apt) 与 CentOS/TencentOS (yum/dnf)
# 用法： sudo bash /opt/easybookx/deploy/setup_server.sh
set -euo pipefail

APP_DIR=/opt/easybookx
PORT=8080

echo "==> EasybookX 部署：$APP_DIR (port $PORT)"

# 1. 安装系统依赖（python3 + venv + nginx）
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -y
  apt-get install -y python3 python3-venv python3-pip nginx
elif command -v dnf >/dev/null 2>&1; then
  dnf install -y python3 python3-pip nginx
elif command -v yum >/dev/null 2>&1; then
  yum install -y python3 python3-pip nginx
else
  echo "!! 未识别的包管理器，请手动安装 python3/venv/nginx" >&2
fi

# 2. Python 虚拟环境 + 依赖
cd "$APP_DIR"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r backend/requirements.txt

# 3. systemd 服务
cp deploy/easybookx.service /etc/systemd/system/easybookx.service
systemctl daemon-reload
systemctl enable easybookx
systemctl restart easybookx
sleep 2
systemctl --no-pager --full status easybookx | head -n 8 || true

# 4. Nginx 反向代理
if [ -d /etc/nginx/conf.d ]; then
  cp deploy/nginx_easybookx.conf /etc/nginx/conf.d/easybookx.conf
else
  mkdir -p /etc/nginx/conf.d
  cp deploy/nginx_easybookx.conf /etc/nginx/conf.d/easybookx.conf
fi
nginx -t && systemctl enable nginx && systemctl restart nginx

# 5. 健康检查
echo "==> 健康检查："
curl -fsS "http://127.0.0.1:${PORT}/api/health" && echo
echo "==> 完成。请确认腾讯云【安全组】已放行 80/443 端口（如用 HTTPS）。"
echo "    HTTPS： sudo certbot --nginx -d your-domain.com"
