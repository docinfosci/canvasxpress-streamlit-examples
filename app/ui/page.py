from importlib.metadata import PackageNotFoundError, version
from platform import python_version

import streamlit

from app.service.data.loaders import get_data_dir, get_update_date
from app.util.config.prefs import preference
from app.util.config.vars import (
    CHART_TYPE_KEY,
    EXAMPLES_BASE_URL,
    EXAMPLES_URL,
    TITLE,
)
from app.util.misc import (
    build_unique_cx_types_list,
    find_available_cx_plot_files,
    parse_plot_filename,
)

TITLE = preference(TITLE)
EXAMPLES_URL = preference(EXAMPLES_URL)
EXAMPLES_BASE_URL = preference(EXAMPLES_BASE_URL)
CHART_TYPE_KEY = preference(CHART_TYPE_KEY)


def first_plot_url(chart_type: str, plot_files: list[str]) -> str | None:
    """Return the canvasxpress.org URL of the first chart in a type.

    Args:
        chart_type: chart type name (e.g. "Area").
        plot_files: list of chart spec file paths.

    Returns:
        The examples URL for the type's lowest-numbered chart, or None when the
        type has no charts.
    """
    plot_indexes = [
        parse_plot_filename(path)[1]
        for path in plot_files
        if parse_plot_filename(path)[0] == chart_type
    ]
    first_url: str | None = None
    if plot_indexes:
        first_index = min(plot_indexes)
        first_url = f"{EXAMPLES_BASE_URL}{chart_type.lower()}-{first_index}.html"
    return first_url


def package_version(package: str) -> str:
    """Get the installed version string of a Python package.

    Args:
        package: name of the installed distribution.

    Returns:
        The installed version, or "unknown" when the package is not installed.
    """
    installed_version: str = "unknown"
    try:
        installed_version = version(package)
    except PackageNotFoundError:
        installed_version = "unknown"
    return installed_version


def app_ui() -> None:
    """Render the page header, version metadata, and gallery navigation buttons.

    Returns:
        None. Rendering happens via Streamlit; navigation buttons render only
        when chart files are available.
    """
    streamlit.set_page_config(page_title=TITLE, layout="wide")
    streamlit.title(TITLE)
    streamlit.caption(
        f"P/Streamlit Chart Viewer; Date Generated: {get_update_date()}; "
        f"Python: {python_version()}; "
        f"canvasXpress: {package_version('canvasxpress')}; "
        f"streamlit: {package_version('streamlit')}"
    )

    plot_files = find_available_cx_plot_files(get_data_dir())
    cx_types = build_unique_cx_types_list(plot_files)
    if plot_files and cx_types:
        current_type = streamlit.session_state.get(CHART_TYPE_KEY, cx_types[0])
        if current_type not in cx_types:
            current_type = cx_types[0]
        target_url = first_plot_url(current_type, plot_files)

        col_examples, col_plots = streamlit.columns(2)
        with col_examples:
            streamlit.link_button("CX-Plots Examples Page", EXAMPLES_URL)
        with col_plots:
            if target_url:
                streamlit.link_button(f"{current_type} Plots", target_url)
