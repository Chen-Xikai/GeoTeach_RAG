@echo off
chcp 65001 >nul
title GeoTeach RAG 服务管理

echo ========================================
echo   GeoTeach RAG 服务管理脚本
echo ========================================
echo.

:menu
echo 请选择操作:
echo   1. 启动所有服务
echo   2. 停止所有服务
echo   3. 重启所有服务
echo   4. 查看服务状态
echo   5. 仅启动Web服务
echo   6. 仅启动MCP服务
echo   7. 退出
echo.
set /p choice=请输入选项 (1-7): 

if "%choice%"=="1" goto start_all
if "%choice%"=="2" goto stop_all
if "%choice%"=="3" goto restart_all
if "%choice%"=="4" goto status
if "%choice%"=="5" goto start_web
if "%choice%"=="6" goto start_mcp
if "%choice%"=="7" goto exit
echo 无效选项，请重新选择
goto menu

:start_all
echo.
echo 正在启动所有服务...
call :start_web_service
call :start_mcp_service
echo.
echo 所有服务已启动!
echo   Web界面: http://localhost:9767
echo   MCP服务: http://localhost:9766
echo.
pause
goto menu

:stop_all
echo.
echo 正在停止所有服务...
taskkill /F /FI "WINDOWTITLE eq GeoTeach Web*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq GeoTeach MCP*" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":9767 "') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":9766 "') do taskkill /F /PID %%a >nul 2>&1
echo 所有服务已停止!
echo.
pause
goto menu

:restart_all
echo.
echo 正在重启所有服务...
call :stop_all_silent
timeout /t 2 >nul
call :start_web_service
call :start_mcp_service
echo.
echo 所有服务已重启!
echo   Web界面: http://localhost:9767
echo   MCP服务: http://localhost:9766
echo.
pause
goto menu

:status
echo.
echo ========================================
echo   服务状态
echo ========================================
echo.
echo 检查Web服务 (端口 9767)...
netstat -ano | findstr ":9767 " | findstr "LISTENING" >nul
if %errorlevel%==0 (
    echo   [运行中] Web服务 - http://localhost:9767
) else (
    echo   [未运行] Web服务
)

echo.
echo 检查MCP服务 (端口 9766)...
netstat -ano | findstr ":9766 " | findstr "LISTENING" >nul
if %errorlevel%==0 (
    echo   [运行中] MCP服务 - http://localhost:9766
) else (
    echo   [未运行] MCP服务
)

echo.
echo 检查数据库...
if exist "data\milvus.db" (
    echo   [存在] Milvus数据库
) else (
    echo   [不存在] Milvus数据库
)

echo.
echo 检查缓存...
if exist "data\cache\embedding_cache.json" (
    echo   [存在] Embedding缓存
) else (
    echo   [不存在] Embedding缓存
)

echo.
pause
goto menu

:start_web
echo.
call :start_web_service
echo.
pause
goto menu

:start_mcp
echo.
call :start_mcp_service
echo.
pause
goto menu

:exit
echo 再见!
exit /b

:stop_all_silent
taskkill /F /FI "WINDOWTITLE eq GeoTeach Web*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq GeoTeach MCP*" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":9767 "') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":9766 "') do taskkill /F /PID %%a >nul 2>&1
exit /b

:start_web_service
echo 正在启动Web服务...
start "GeoTeach Web" /MIN cmd /c "py -3.11 -m servers.web"
timeout /t 3 >nul
netstat -ano | findstr ":9767 " | findstr "LISTENING" >nul
if %errorlevel%==0 (
    echo   [成功] Web服务已启动 - http://localhost:9767
) else (
    echo   [等待] Web服务正在启动...
    timeout /t 5 >nul
    netstat -ano | findstr ":9767 " | findstr "LISTENING" >nul
    if %errorlevel%==0 (
        echo   [成功] Web服务已启动 - http://localhost:9767
    ) else (
        echo   [失败] Web服务启动失败，请检查日志
    )
)
exit /b

:start_mcp_service
echo 正在启动MCP服务...
start "GeoTeach MCP" /MIN cmd /c "py -3.11 -m servers.mcp"
timeout /t 3 >nul
netstat -ano | findstr ":9766 " | findstr "LISTENING" >nul
if %errorlevel%==0 (
    echo   [成功] MCP服务已启动 - http://localhost:9766
) else (
    echo   [等待] MCP服务正在启动...
    timeout /t 5 >nul
    netstat -ano | findstr ":9766 " | findstr "LISTENING" >nul
    if %errorlevel%==0 (
        echo   [成功] MCP服务已启动 - http://localhost:9766
    ) else (
        echo   [失败] MCP服务启动失败，请检查日志
    )
)
exit /b
