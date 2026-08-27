@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title Yakob (ያዕቆብ) - Multilingual Desktop Assistant
cd /d "%~dp0"
echo Starting Yakob Desktop Assistant...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred while launching Yakob.
    pause
)
