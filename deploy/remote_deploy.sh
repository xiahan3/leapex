#!/usr/bin/env bash
# EasybookX · 本地一键远程部署（在你的开发机执行，rsync 到腾讯云服务器）
#
# 用法：
#   SSH_TARGET=root@1.2.3.4 SSH_KEY=~/.ssh/id_rsa bash deploy/remote_deploy.sh
# 可选：
#   SSH_PORT=22  APP_DIR=/opt/easybookx
#
# 前置：服务器可 SSH 登录；本机已装 rsync。
set -euo pipefail

SSH_TARGET="${SSH_TARGET:?请设置 SSH_TARGET，如 root@1.2.3.4}"
SSH_PORT="${SSH_PORT:-22}"
APP_DIR="${APP_DIR:-/opt/easybookx}"
SSH_KEY="${SSH_KEY:-}"

SSH_OPTS=(-p "$SSH_PORT" -o StrictHostKeyChecking=accept-new)
[ -n "$SSH_KEY" ] && SSH_OPTS+=(-i "$SSH_KEY")

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "==> 同步代码 $REPO_ROOT -> $SSH_TARGET:$APP_DIR"

# rsync：排除虚拟环境/数据库/git，运行时数据库在服务器上独立生成
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "mkdir -p $APP_DIR"
rsync -az --delete \
  --exclude '.venv' --exclude '.git' --exclude '__pycache__' \
  --exclude '*.db' --exclude '.DS_Store' \
  -e "ssh ${SSH_OPTS[*]}" \
  "$REPO_ROOT/" "$SSH_TARGET:$APP_DIR/"

echo "==> 在服务器上执行安装/更新脚本"
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "sudo bash $APP_DIR/deploy/setup_server.sh"

echo "==> 部署完成。访问 http://<服务器IP>/ 或你的域名。"
