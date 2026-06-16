@echo off
setlocal
cd /d "%~dp0"

echo [1/3] Creating virtual environment...
uv venv .venv
if %errorlevel% neq 0 (
    echo Failed to create virtual environment.
    pause
    exit /b %errorlevel%
)

echo [2/3] Activating virtual environment and installing dependencies...
call .venv\Scripts\activate.bat
uv pip install -e .
if %errorlevel% neq 0 (
    echo Failed to install dependencies.
    pause
    exit /b %errorlevel%
)

echo [3/3] Checking environment variables...
if not exist .env (
    echo Warning: .env file not found. Please create one based on .env.example.
    if exist .env.example (
        copy .env.example .env
        echo Created .env from .env.example. Please update it with your API keys.
    )
)

echo Setup completed successfully!
pause
