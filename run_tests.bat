@echo off
chcp 65001 >nul
echo ========================================
echo   Easy-Web 测试运行器 (Master 企业版)
echo ========================================
echo.

REM 检查虚拟环境
if exist ".venv\Scripts\activate.bat" (
    echo [1/4] 激活虚拟环境...
    call .venv\Scripts\activate.bat
) else (
    echo [警告] 未找到虚拟环境，使用系统 Python
)

echo.
echo [2/4] 检查依赖...
pip show pytest >nul 2>&1
if errorlevel 1 (
    echo 安装依赖中...
    pip install -r requirements.txt
) else (
    echo 依赖已安装
)

echo.
echo [3/4] 运行测试并生成 Allure 报告...
echo.
python main.py %*

echo.
echo [4/4] 测试完成！
echo.
echo 查看报告:
echo   - 手动打开: pkg\allurec\bin\allure open allure-report
echo   - 或双击: allure-report\index.html
echo.
pause
