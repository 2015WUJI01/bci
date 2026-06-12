#!/bin/bash
# 股票竞技游戏 - Linux/macOS 启动脚本
echo "========================================"
echo "  股票竞技游戏 - 启动器"
echo "========================================"
echo ""
echo "正在安装依赖..."
pip install -q -r backend/requirements.txt
echo ""
echo "启动服务器 (http://localhost:8000)"
echo "========================================"
echo ""
exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload
