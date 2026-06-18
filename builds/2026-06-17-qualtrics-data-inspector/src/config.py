"""Load and merge qi.toml configuration with CLI arguments."""

import tomllib
from pathlib import Path
from typing import Optional


DEFAULT_CONFIG_NAME = "qi.toml"


def load_config(path: Optional[str] = None) -> dict:
    """
    Load a qi.toml config file. Returns an empty dict if the file does not exist.
    Raises ValueError if the file exists but contains invalid TOML.
    """
    config_path = Path(path or DEFAULT_CONFIG_NAME)
    if not config_path.exists():
        return {}
    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Config file {config_path} is invalid TOML: {e}") from e


def apply_config_defaults(parser, config: dict) -> None:
    """
    Set argparse defaults from config file values. CLI flags always win —
    this only affects the built-in default shown when a flag is omitted.
    """
    thr = config.get("thresholds", {})
    _maybe_set(parser, "threshold",          thr, "fast_response_seconds")
    _maybe_set(parser, "missing_warn",       thr, "missing_column_warn")
    _maybe_set(parser, "missing_flag",       thr, "missing_column_flag")
    _maybe_set(parser, "missing_respondent", thr, "missing_respondent_flag")
    _maybe_set(parser, "outlier_z",          thr, "outlier_z")
    _maybe_set(parser, "low_r",              thr, "low_item_total_r")

    insp = config.get("inspect", {})
    _maybe_set(parser, "no_conditions", insp, "no_conditions")

    cln = config.get("clean", {})
    _maybe_set(parser, "keep_incomplete",      cln, "keep_incomplete")
    _maybe_set(parser, "keep_fast",            cln, "keep_fast")
    _maybe_set(parser, "keep_straight_liners", cln, "keep_straight_liners")
    _maybe_set(parser, "exclude_high_missing", cln, "exclude_high_missing")


def _maybe_set(parser, dest: str, section: dict, key: str) -> None:
    if key in section:
        parser.set_defaults(**{dest: section[key]})


def get_scales_from_config(config: dict) -> Optional[dict]:
    """
    Return inline scale definitions from the [scales] section, or None.

    Each value must be a list of column-name strings:
      [scales]
      PSS10 = ["Q3_1", "Q3_2", "Q3_3"]
    """
    scales = config.get("scales")
    if not scales:
        return None
    result = {
        name: cols
        for name, cols in scales.items()
        if isinstance(cols, list) and all(isinstance(c, str) for c in cols)
    }
    return result or None


def get_attention_answers_from_config(config: dict) -> Optional[dict]:
    """
    Return attention-check expected answers from the [attention] section, or None.

      [attention]
      ATTN1 = "4"
      ATTN2 = "Strongly Agree"
    """
    attn = config.get("attention")
    if not attn:
        return None
    return {col: str(val) for col, val in attn.items()}
