import json
import logging
import os
import re
import subprocess
from datetime import datetime

import requests
from invoke import task

from app.service.data.loaders import (
    cx_types_path,
    get_data_dir,
    latest_update_path,
)
from app.util.config.prefs import preference
from app.util.config.vars import REFRESH_CX_JSON_FILES_TIME_OUT_ENV


@task
def run(context) -> None:
    """Run the Streamlit application.

    Args:
        context: the Invoke context.

    Returns:
        None. Launches `streamlit run application.py` in the shell.
    """
    context.run("streamlit run application.py")


def parse_plotname_and_number(filename: str, plot_data: dict) -> tuple[str, str]:
    """Parse a scraped filename into (plot_name, plot_number).

    Matches against the 'plot_types' list in *plot_data*.

    Args:
        filename: scraped JSON filename (e.g. "area-1.json").
        plot_data: config dict that must include a "plot_types" list.

    Returns:
        A (plot_name, plot_number) tuple, or ("", "") when neither can
        be identified.
    """
    parse_result: tuple[str, str] = ("", "")
    plot_base_name: str = filename.replace(".json", "")
    if plot_base_name.lower().startswith("cx"):
        plot_base_name = plot_base_name[2:]

    normalized_base_name = plot_base_name.lower().replace("-", "").replace("_", "")

    for plot_type in plot_data["plot_types"]:
        normalized_plot_type = plot_type.lower().replace("-", "").replace("_", "")

        if normalized_base_name.startswith(normalized_plot_type):
            plot_name = plot_type
            remaining_part = normalized_base_name[len(normalized_plot_type) :]

            plot_number_match = re.search(r"\d+$", remaining_part)
            plot_number = plot_number_match.group() if plot_number_match else ""
            parse_result = (plot_name, plot_number)

    return parse_result


def load_json(filepath: str) -> dict | None:
    """Read and decode a JSON file.

    Args:
        filepath: path of the JSON file to read.

    Returns:
        The parsed JSON dict, or None when the file is malformed.
    """
    parsed_data = None
    try:
        with open(filepath, encoding="utf-8") as json_file:
            parsed_data = json.load(json_file)
    except json.JSONDecodeError:
        parsed_data = None
    return parsed_data


def merge_plot_metadata(chart_data: dict, plot_data: dict) -> dict:
    """Overlay matching plot_data keys onto a loaded chart JSON.

    Args:
        chart_data: the loaded chart JSON dict to update in place.
        plot_data: master config dict whose keys are overlaid when present.

    Returns:
        The updated *chart_data* dict.
    """
    updated_chart_data = {
        key: plot_data[key] for key in chart_data.keys() if key in plot_data
    }
    chart_data.update(updated_chart_data)
    return chart_data


def rename_files_in_folder(plots_folder: str, plot_data: dict) -> None:
    """Normalize scraped JSON names to 'cx_chart_<plot_name>_<plot_number>.json'.

    Args:
        plots_folder: directory holding the scraped JSON files.
        plot_data: config dict including the "plot_types" list.

    Returns:
        None. Files are renamed in place; already-named files are updated with
        matching plot_data metadata.
    """
    for filename in os.listdir(plots_folder):
        existing_filepath = os.path.join(plots_folder, filename)
        if not filename.endswith(".json"):
            continue

        if filename.startswith("cx_chart_"):
            logging.debug(f"Skip already named files: {filename}")
            chart_data = load_json(existing_filepath)
            if chart_data is None:
                continue
            with open(existing_filepath, "w", encoding="utf-8") as json_file:
                json.dump(
                    merge_plot_metadata(chart_data, plot_data), json_file, indent=6
                )
            continue

        parse_result = parse_plotname_and_number(filename, plot_data)
        if not parse_result:
            logging.debug(f"Skipping non-plot file: {filename}")
            continue

        plotname, number = parse_result
        new_filepath = os.path.join(plots_folder, f"cx_chart_{plotname}_{number}.json")
        chart_data = load_json(existing_filepath)
        if chart_data is None:
            logging.error(f"Skipping file {filename}: could not decode JSON.")
            continue

        with open(new_filepath, "w", encoding="utf-8") as new_json_file:
            json.dump(
                merge_plot_metadata(chart_data, plot_data), new_json_file, indent=6
            )

        os.remove(existing_filepath)
        logging.debug(f"Renamed {existing_filepath} to {new_filepath}")


@task
def refresh_json_data(context) -> None:
    """Scrape the latest chart specs from canvasxpress.org into app/data.

    Probes each plot type's numbered example pages, downloads the reproducible
    JSON via the `canvasxpress` CLI, normalizes filenames into app/data, and
    stamps the update date into app/plots_and_update_date/latest_update.txt.

    Args:
        context: the Invoke context.

    Returns:
        None. Downloads, renames, and stamps files as a side effect.
    """
    data_dir = get_data_dir()
    cx_types_file: str = cx_types_path()
    time_out: int = int(preference(REFRESH_CX_JSON_FILES_TIME_OUT_ENV, 30))

    with open(cx_types_file, encoding="utf-8") as file_handle:
        plot_data = json.load(file_handle)

    for plot_type in plot_data["plot_types"]:
        base_url: str = (
            "https://canvasxpress.org/examples/{category}-{plot_number}.html"
        )
        plot_number: int = 1

        while True:
            url = base_url.format(category=plot_type.lower(), plot_number=plot_number)

            logging.info(f"Checking URL: {url}")
            try:
                response = requests.head(url, timeout=time_out)
            except requests.RequestException as error:
                logging.error(f"Could not reach {url}: {error}. Skipping this plot.")
                break

            if response.status_code == 404:
                logging.warning(
                    f"URL not found (404): {url}, stopping further downloads for {plot_type}."
                )
                break

            cmd = ["npx", "canvasxpress", "json", "-i", url, "-o", data_dir]
            logging.info(f"Running command: {' '.join(cmd)}")

            try:
                process_result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    timeout=time_out,
                )
                output = process_result.stdout.decode() + process_result.stderr.decode()

                if "404" in output or "failed" in output.lower():
                    logging.error(
                        f"CanvasXpress command failed for {url}. Skipping this plot."
                    )
                    break

                logging.info(f"Successfully saved JSON in {data_dir}")
                rename_files_in_folder(data_dir, plot_data)

            except subprocess.CalledProcessError as error:
                logging.error(
                    f"Command execution error: {error}. Skipping file creation for {url}."
                )
                continue

            except subprocess.TimeoutExpired:
                logging.error(f"Timeout occurred for {url}. Moving to next plot type.")
                break

            plot_number += 1

    current_updated_time: str = datetime.now().strftime("%Y-%m-%d")
    update_date_file: str = latest_update_path()
    try:
        with open(update_date_file, "w", encoding="utf-8") as file_handle:
            file_handle.write(current_updated_time)
    except (OSError, ConnectionError, InterruptedError) as error:
        logging.error(f"Failed to update the date file: {error}")

    logging.info(
        f"Refresh complete. Last update date and time ({current_updated_time}) "
        f"saved in '{update_date_file}'."
    )
