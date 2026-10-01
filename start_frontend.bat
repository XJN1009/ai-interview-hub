@echo off
chcp 65001 >nul
title 经纬职引-智面仓 - 前端 Vite 服务 (Port: 5173)
echo 正在启动前端开发服务 (http://localhost:5173)...
cd /d "%~dp0frontend"
npm.cmd run dev
pause
