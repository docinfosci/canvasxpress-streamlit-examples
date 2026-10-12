import json

import streamlit
from canvasxpress.plot import convert_from_reproducible_json
from canvasxpress.render.streamlit import plot

from app.service.data.loaders import (
    get_data_dir,
    load_cx_json_file,
    load_excluded_cx_plots_info,
)
from app.util.misc import (
    build_unique_cx_types_list,
    find_available_cx_plot_files,
    normalize_chart_type,
    parse_plot_filename,
    reset_plot_dimensions,
)

PLOT_SIZE = 500
ALL_OPTION = "All"


@streamlit.cache_data(show_spinner=False)
def cached_cx_plot_files(data_dir: str) -> list[str]:
    """Find and naturally sort all chart spec files for the given data directory.

    Args:
        data_dir: directory holding the cx_chart_*.json files.

    Returns:
        Naturally sorted list of chart spec file paths.
    """
    return find_available_cx_plot_files(data_dir)


@streamlit.cache_data(show_spinner=False)
def cached_cx_json_file(filepath: str) -> dict | None:
    """Load and cache a chart spec JSON file.

    Caching avoids re-reading from disk on every Streamlit rerun.

    Args:
        filepath: absolute path of the cx_chart_*.json file.

    Returns:
        The parsed JSON dict, or None when it cannot be parsed.
    """
    return load_cx_json_file(filepath)


def excluded_indexes(exclude_info: dict | list) -> dict[str, list[int]]:
    """Normalize cx_types.json exclude_plots into a per-type index mapping.

    Args:
        exclude_info: the raw exclude_plots config (dict or list of entries).

    Returns:
        A {chart_type: [excluded indices]} mapping.
    """
    excluded_by_type: dict[str, list[int]] = {}
    if isinstance(exclude_info, dict):
        for chart_type, plot_indexes in exclude_info.items():
            excluded_by_type[chart_type] = [
                int(plot_index) for plot_index in (plot_indexes or [])
            ]
    elif isinstance(exclude_info, list):
        for exclude_entry in exclude_info:
            if isinstance(exclude_entry, dict) and exclude_entry.get("type"):
                excluded_by_type[exclude_entry["type"]] = [
                    int(plot_index)
                    for plot_index in (exclude_entry.get("indexes") or [])
                ]
    return excluded_by_type


def render_chart(
    chart_type: str,
    chart_idx: int,
    chart_path: str,
    excluded_plots: dict[str, list[int]],
) -> None:
    """Render a single chart with its title, or a warning when excluded.

    Args:
        chart_type: chart type name (e.g. "Area").
        chart_idx: chart number within the type.
        chart_path: absolute path of the chart spec file.
        excluded_plots: {chart_type: [excluded indices]} mapping.

    Returns:
        None. Renders via Streamlit; excluded or unparsable charts show a
        message instead of a plot.
    """
    chart_label = f"cX{normalize_chart_type(chart_type).lower()}{chart_idx}"
    streamlit.subheader(chart_label)
    if chart_idx in excluded_plots.get(chart_type, []):
        streamlit.warning(f"{chart_label} — EXCLUDED FROM TEST APP - per configuration")
    else:
        chart_data = cached_cx_json_file(chart_path)
        if chart_data is None:
            streamlit.error(f"Could not parse chart spec: {chart_path}")
        else:
            canvasxpress_plot = convert_from_reproducible_json(json.dumps(chart_data))
            reset_plot_dimensions(canvasxpress_plot, PLOT_SIZE, PLOT_SIZE)
            plot(canvasxpress_plot)


def app_server() -> None:
    """Render the sidebar chart selector and the selected charts.

    Returns:
        None. The chart type and number are driven by sidebar widgets; the
        selected chart(s) are rendered in the main area.
    """
    data_dir = get_data_dir()
    plot_files = cached_cx_plot_files(data_dir)
    if not plot_files:
        streamlit.info(
            "No CanvasXpress chart data found. Run `invoke refresh-json-data` to "
            "populate app/data."
        )
    else:
        cx_types = build_unique_cx_types_list(plot_files)
        excluded = excluded_indexes(load_excluded_cx_plots_info())

        charts_by_type: dict[str, list[tuple[int, str]]] = {}
        for path in plot_files:
            chart_type, chart_idx = parse_plot_filename(path)
            charts_by_type.setdefault(chart_type, []).append((chart_idx, path))
        for charts in charts_by_type.values():
            charts.sort()

        with streamlit.sidebar:
            streamlit.header("Chart Selector")
            chart_type = streamlit.selectbox(
                "Chart Type", cx_types, key="cx_chart_type"
            )
            if chart_type in charts_by_type:
                options = {
                    f"cX{normalize_chart_type(chart_type).lower()}{chart_idx}": (
                        chart_idx,
                        path,
                    )
                    for chart_idx, path in charts_by_type[chart_type]
                }
                chart_options = [ALL_OPTION, *options]
            else:
                options = {}
                chart_options = [ALL_OPTION]
            selected_chart = streamlit.selectbox(
                "Chart Number", chart_options, key="cx_chart_plot"
            )

        if chart_type not in charts_by_type:
            streamlit.error(f"No charts found for type '{chart_type}'.")
        elif selected_chart == ALL_OPTION:
            charts = charts_by_type[chart_type]
            for row in range(0, len(charts), 2):
                row_charts = charts[row : row + 2]
                columns = streamlit.columns(len(row_charts))
                for column, (chart_idx, chart_path) in zip(
                    columns, row_charts, strict=False
                ):
                    with column:
                        render_chart(chart_type, chart_idx, chart_path, excluded)
        else:
            chart_idx, chart_path = options[selected_chart]
            render_chart(chart_type, chart_idx, chart_path, excluded)
