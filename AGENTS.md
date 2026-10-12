## Environment & Tooling
- Use `uv` for Python package and virtual environment management
- Python version: 3.12 (define in `.python-version`)
- Install dependencies: `uv sync`
- Update lock file: `uv lock --upgrade`
- Run the Streamlit app: `uv run streamlit run application.py`
- Check code style: `uv run ruff check .`
- Format code: `uv run ruff format .` 

