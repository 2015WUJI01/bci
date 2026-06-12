@echo off
chcp 65001 >nul
cd /d %~dp0

echo ========================================
echo   股票竞技游戏 - 启动器
echo ========================================
echo.

echo 正在安装依赖...
pip install -q -r backend/requirements.txt

if "%PORT%"=="" set PORT=8000

echo.
echo 启动服务器 (http://localhost:%PORT%)
echo 在浏览器中打开 http://localhost:%PORT%
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

python -m uvicorn backend.main:app --host 0.0.0.0 --port %PORT% --reload
