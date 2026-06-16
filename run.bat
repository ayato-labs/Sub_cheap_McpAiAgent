@echo off
setlocal
cd /d "%~dp0"

if not exist .venv (
    echo Error: .venv directory not found. Please run setup.bat first.
    pause
    exit /b 1
)

echo Starting Sub-cheap-McpAiAgent...
uv run sub-cheap-mcp
if %errorlevel% neq 0 (
    echo Server exited with error code %errorlevel%.
    pause
)
