@echo off
chcp 65001 >nul
echo ========================================
echo   Easy-Web 快速启动
echo ========================================
echo.

REM 检查虚拟环境
if exist ".venv\Scripts\activate.bat" (
    echo [1/3] 激活虚拟环境...
    call .venv\Scripts\activate.bat
) else (
    echo [警告] 未找到虚拟环境，使用系统 Python
)

echo.
echo [2/3] 检查依赖...
pip show selenium >nul 2>&1
if errorlevel 1 (
    echo 安装依赖中...
    pip install -r requirements.txt
) else (
    echo 依赖已安装
)

echo.
echo [3/3] 启动测试...
echo.
python main.py %*

pause
