# canvasxpress-streamlit-examples

This application provides a visual reference for CanvasXpress charts in the 
context of Streamlit for Python.

## How to Install

### Local Development Environment
A local development environment such as VSCode or PyCharm can be used in developing this project:

1. Install Python 3.12 or later (managed automatically by uv)
2. Checkout this project from: https://github.com/your-repo/canvasxpress-streamlit-examples.git
3. In a terminal, execute the setup script for your platform. This script performs:
   1. Installs uv (if not present)
   2. Establishment of a virtual environment if one does not exist
   3. Installation of project packages via uv
   4. Installation of canvasxpress-cli (npm) and Playwright Chromium

**macOS / Linux:**
```bash
./setup.sh
```

**Windows (Command Prompt):**
```cmd
setup.bat
```

3. Activate the virtual environment:
   - macOS / Linux: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate.bat`

### Local deployment
This project can be run on a local workstation with Internet access (required for acquiring data only):

1. Ensure that the setup script has been executed.
2. Open a terminal window.
3. Activate the local virtual environment:
   - macOS / Linux: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate.bat`
4. Execute Streamlit with the entrypoint module: `streamlit run application.py` OR use invoke: `invoke run`
5. When canvasxpress website has updated data plots, you can update plots json files using `invoke refresh-json-data`

Open http://localhost:8501 and pick a chart type and chart number in the sidebar.

### Configuring environment variables
This project uses python-dotenv for managing environment variables by file, and it monitors the OS runtime context for environment variables.

`.env.prd` provides a template for variables that must be set. Some are commented out, and are expected to be provided by the runtime environment or another `.env.*` file.

`.env.dev` is a convenience file with typical values across development environments.

Additional dot files can be created, such as `.env.local`. Ideally add these to the gitignore so that secrets, etc. are not committed into the repository.

Remember that the Python debug level is `10`. Higher numbers reduce the log information.

### Note For Developers

- **Windows:** `invoke refresh-json-data` Won't work in windows due to canvasxpress-cli bug

### Log messages for `invoke refresh-json-data`
- If having 404 error you will get a warning that url not found so, it won't proceed further and continue to the next plot. (e.g "WARNING:root:URL not found (404): https://canvasxpress.org/examples/area-17.html, stopping further downloads for Area.")
- If the accessing page exist but has empty plot you will have a timeout error and continue to the next plot. (e.g "ERROR:root:Timeout occurred for https://canvasxpress.org/examples/arealine-5.html. Moving to next plot type.")