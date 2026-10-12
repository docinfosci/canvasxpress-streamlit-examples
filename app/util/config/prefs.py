import os
import re

from dotenv import load_dotenv


def sort_naturally(strings: list[str]) -> list[str]:
    """Sort strings using natural (human) ordering — [S1, S2, S10] not [S1, S10, S2].

    Args:
        strings: list of strings to sort.

    Returns:
        A new list sorted naturally (digit groups compared numerically).
    """
    return sorted(
        strings,
        key=lambda string: [
            int(part) if part.isdigit() else part.lower()
            for part in re.split(r"(\d+)", string)
        ],
    )


def load_env_files() -> None:
    """Load env files into the process environment.

    Mirrors the Shiny reference app's precedence (see skills/shiny_app_architecture.md):
    ".env.prd" is loaded first as the baseline, then ".env.dev" for dev overrides,
    then any remaining ".env.*" files in natural order. Later files override earlier ones.

    Returns:
        None. Loaded variables are set via dotenv with override enabled.
    """
    env_dir = os.getcwd()
    env_filenames = sort_naturally(
        [
            filename
            for filename in os.listdir(env_dir)
            if filename.startswith(".env")
            and os.path.isfile(os.path.join(env_dir, filename))
        ]
    )
    preferred_order = [".env.prd", ".env.dev"]
    ordered_filenames = [name for name in preferred_order if name in env_filenames]
    ordered_filenames.extend(
        name for name in env_filenames if name not in preferred_order
    )
    for filename in ordered_filenames:
        load_dotenv(os.path.join(env_dir, filename), override=True)


load_env_files()


def preference(variable: str, default=None) -> str:
    """Read an environment variable, falling back to *default*.

    Args:
        variable: environment variable name.
        default: fallback value when the variable is unset.

    Returns:
        The variable's string value, or *default* when not set.
    """
    return os.environ.get(variable, default)
