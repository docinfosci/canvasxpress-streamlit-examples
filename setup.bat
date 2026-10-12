@echo off
REM Setup script for Windows - Initialize canvasxpress-streamlit-examples workspace.

echo Configuring local environment for development...

REM Check for uv, install if missing
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo Installing uv...
    powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"
    REM Refresh PATH
    set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
)

echo Ensuring Python 3.12...
uv python install 3.12

echo Installing dependencies and creating virtual environment...
uv sync

echo Installing canvasxpress-cli (npm)...
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: npm not found. Install Node.js first: https://nodejs.org/
    exit /b 1
)
where npx >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: npx not found. Update Node.js and retry.
    exit /b 1
)
npm install

echo Installing Playwright Chromium for canvasxpress-cli scraping...
npx playwright install chromium

echo Verifying core imports and linting...
uv run python -c "import streamlit, importlib.metadata; print('  streamlit', streamlit.__version__, '| canvasxpress', importlib.metadata.version('canvasxpress'))"
uv run python -c "from canvasxpress.plot import graph, convert_from_reproducible_json; from canvasxpress.canvas import CanvasXpress; print('  canvasxpress rendering API OK')"
where canvasxpress >nul 2>nul
if %errorlevel% equ 0 (
    echo   canvasxpress-cli found
) else (
    echo   canvasxpress-cli not on PATH; use 'npx canvasxpress' for refresh-json-data
)
uv run ruff check .

echo.
echo Ready for development!
echo.
echo Activate the virtual environment:
echo   .venv\Scripts\activate.bat
echo.
echo Start the Streamlit app:
echo   invoke run
echo   # or: uv run streamlit run application.py
echo.
echo To refresh chart specs from canvasxpress.org:
echo   invoke refresh-json-data