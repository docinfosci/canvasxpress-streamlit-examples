#!/usr/bin/env bash

echo "Configuring local environment for development..."

echo "Ensuring Python 3.12..."
uv python install 3.12

echo "Installing dependencies and creating virtual environment..."
uv sync

echo "Installing canvasxpress-cli (npm)..."
if ! command -v npm &> /dev/null; then
    echo "ERROR: npm not found. Install Node.js first: https://nodejs.org/"
    exit 1
fi
if ! command -v npx &> /dev/null; then
    echo "ERROR: npx not found. Update Node.js and retry."
    exit 1
fi
npm install

echo "Installing Playwright Chromium for canvasxpress-cli scraping..."
npx playwright install chromium

echo "Verifying core imports and linting..."
uv run python -c "import streamlit, importlib.metadata; print('  streamlit', streamlit.__version__, '| canvasxpress', importlib.metadata.version('canvasxpress'))"
uv run python -c "from canvasxpress.plot import graph, convert_from_reproducible_json; from canvasxpress.canvas import CanvasXpress; print('  canvasxpress rendering API OK')"
if command -v canvasxpress &> /dev/null; then
    echo "  canvasxpress-cli found"
else
    echo "  canvasxpress-cli not on PATH; use 'npx canvasxpress' for refresh-json-data"
fi
uv run ruff check .

echo ""
echo "Ready for development!"
echo ""
echo "Activate the virtual environment:"
echo "  source .venv/bin/activate"
echo ""
echo "Start the Streamlit app:"
echo "  invoke run"
echo "  # or: uv run streamlit run application.py"
echo ""
echo "To refresh chart specs from canvasxpress.org:"
echo "  invoke refresh-json-data"