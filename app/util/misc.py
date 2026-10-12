import os
import re
from glob import glob

from .config.prefs import sort_naturally

FILE_GLOB = "cx_chart_*.json"
FILENAME_PATTERN = re.compile(r"cx_chart_(?P<type>.+)_(?P<idx>\d+)\.json")


def find_available_cx_plot_files(data_dir: str) -> list[str]:
    """Glob all chart spec JSON filenames from the data directory.

    Args:
        data_dir: directory holding the cx_chart_*.json files.

    Returns:
        Naturally sorted list of chart spec file paths.
    """
    return sort_naturally(glob(os.path.join(data_dir, FILE_GLOB)))


def build_unique_cx_types_list(cx_plot_files: list[str]) -> list[str]:
    """Extract unique, naturally-sorted chart type names from chart filenames.

    Type names may contain hyphens (e.g. Hexplot-Binplot). The index contributes
    nothing to the type name.

    Args:
        cx_plot_files: list of chart spec file paths.

    Returns:
        Naturally sorted unique list of chart type names.
    """
    types = set()
    for path in cx_plot_files:
        match = FILENAME_PATTERN.match(os.path.basename(path))
        if match:
            types.add(match.group("type"))
    return sort_naturally(types)


def parse_plot_filename(filename: str) -> tuple[str, int]:
    """Parse a chart filename into its chart type and plot id.

    Args:
        filename: path or name matching cx_chart_<Type>_<N>.json.

    Returns:
        A (chart_type, plot_id) tuple.

    Raises:
        ValueError: when the filename does not match the contract.
    """
    match = FILENAME_PATTERN.match(os.path.basename(filename))
    if not match:
        raise ValueError(
            f"filename does not match cx_chart_<Type>_<N>.json contract: {filename}"
        )
    return match.group("type"), int(match.group("idx"))


def normalize_chart_type(chart_type: str) -> str:
    """Normalize a chart type for use in Streamlit widget keys.

    Spaces and hyphens are replaced with underscores.

    Args:
        chart_type: chart type name (e.g. "Hexplot-Binplot").

    Returns:
        The underscore-normalized type name.
    """
    return chart_type.replace(" ", "_").replace("-", "_")


def reset_plot_dimensions(
    canvasxpress_plot, width: int = 500, height: int = 500
) -> None:
    """Normalize a CanvasXpress object to a uniform plot size.

    Streamlit renders each chart in an iframe sized (canvasxpress_plot.width + 50, canvasxpress_plot.height + 50),
    so setting width/height here gives deterministic, uniformly sized plots —
    replacing the Shiny app's afterRender.setDimensions workaround.

    Args:
        canvasxpress_plot: the CanvasXpress plot object to resize.
        width: desired plot width in pixels.
        height: desired plot height in pixels.

    Returns:
        None. The object is mutated in place.
    """
    if canvasxpress_plot is not None:
        canvasxpress_plot.width = int(width)
        canvasxpress_plot.height = int(height)
