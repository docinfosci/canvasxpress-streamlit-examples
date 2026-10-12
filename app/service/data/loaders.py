import json
import os

from app.util.config.prefs import preference
from app.util.config.vars import DATA_DIR_ENV, PLOTS_AND_UPDATE_DATE_DIR_ENV

APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DEFAULT_DATA_DIR = os.path.join(APP_DIR, "data_management", "data")
PLOTS_AND_UPDATE_DATE_DIR_NAME = "plots_and_update_date"
DEFAULT_PLOTS_AND_UPDATE_DATE_DIR = os.path.join(
    APP_DIR, "data_management", PLOTS_AND_UPDATE_DATE_DIR_NAME
)


def resolve_preferred_dir(env_name, default_dir: str) -> str:
    """Resolve an env-provided directory, falling back to *default_dir*.

    Relative env values are anchored to the repository's app directory so they
    behave identically to the built-in defaults regardless of the CWD.

    Args:
        env_name: environment variable name holding the directory override.
        default_dir: absolute directory used when the env var is unset.

    Returns:
        The resolved absolute directory.
    """
    preferred = preference(env_name, None)
    if not preferred:
        resolved_dir = default_dir
    elif os.path.isabs(preferred):
        resolved_dir = preferred
    else:
        resolved_dir = os.path.join(APP_DIR, preferred)
    return resolved_dir


def get_data_dir() -> str:
    """Resolve and create the chart-spec data directory.

    Returns:
        The absolute path of the created chart data directory.
    """
    data_dir = resolve_preferred_dir(DATA_DIR_ENV, DEFAULT_DATA_DIR)
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_plots_and_update_date_dir() -> str:
    """Resolve and create the plots-and-update-date metadata directory.

    Returns:
        The absolute path of the created metadata directory.
    """
    plots_dir = resolve_preferred_dir(
        PLOTS_AND_UPDATE_DATE_DIR_ENV, DEFAULT_PLOTS_AND_UPDATE_DATE_DIR
    )
    os.makedirs(plots_dir, exist_ok=True)
    return plots_dir


def cx_types_path() -> str:
    """Return the absolute path to the cx_types.json configuration file.

    Returns:
        The path of the file under the plots-and-update-date directory.
    """
    return os.path.join(get_plots_and_update_date_dir(), "cx_types.json")


def latest_update_path() -> str:
    """Return the absolute path to the latest_update.txt timestamp file.

    Returns:
        The path of the file under the plots-and-update-date directory.
    """
    return os.path.join(get_plots_and_update_date_dir(), "latest_update.txt")


def load_cx_types_info() -> dict:
    """Load the plot_types + exclude_plots configuration from cx_types.json.

    Returns:
        A dict with "plot_types" as a list of type names and "exclude_plots"
        as a mapping; empty defaults when the file is missing.
    """
    path = cx_types_path()
    cx_types_info: dict = {"plot_types": [], "exclude_plots": {}}
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as file_handle:
            cx_types_info = json.load(file_handle)
    return cx_types_info


def load_excluded_cx_plots_info() -> dict[str, list[int]]:
    """Return the excluded-chart indices per chart type.

    Returns:
        A {chart_type: [excluded indices]} mapping (empty when not configured).
    """
    cx_types_info = load_cx_types_info()
    exclude_plots = cx_types_info.get("exclude_plots", {}) or {}
    if isinstance(exclude_plots, list):
        normalized: dict[str, list[int]] = {}
        for entry in exclude_plots:
            if isinstance(entry, dict) and entry.get("type"):
                normalized[entry["type"]] = [
                    int(i) for i in (entry.get("indexes") or [])
                ]
        return normalized
    if isinstance(exclude_plots, dict):
        return {
            chart_type: [int(i) for i in (indexes or [])]
            for chart_type, indexes in exclude_plots.items()
        }
    return {}


def load_cx_json_file(filepath: str) -> dict | None:
    """Load a chart spec JSON file into a dict.

    Args:
        filepath: absolute path of the cx_chart_*.json file to read.

    Returns:
        The parsed JSON dict, or None when the file cannot be parsed.
    """
    json_data: dict | None = None
    try:
        with open(filepath, encoding="utf-8") as file_handle:
            json_data = json.load(file_handle)
    except (OSError, json.JSONDecodeError):
        json_data = None
    return json_data


def get_update_date() -> str:
    """Read the data refresh timestamp.

    Returns:
        The refresh date string, or an empty string when unavailable.
    """
    path = latest_update_path()
    update_date: str = ""
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as file_handle:
            update_date = file_handle.read().strip()
    return update_date
