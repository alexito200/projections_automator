"""
filler_core.py
==============
Pure logic for the Projection Form Filler:
  * reading the projection data (Excel upload or pasted text)
  * formatting cell values into clean strings
  * the keystroke "typing" engine that drives the browser form

The Streamlit UI (app.py) imports from here. Keeping this separate makes the
parsing testable without a running Streamlit/desktop session.
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

import pandas as pd

# --------------------------------------------------------------------------- #
# pyautogui is only needed when actually typing. Import it defensively so this
# module can be imported (and the parsers tested) on a headless machine.
# --------------------------------------------------------------------------- #
try:
    import pyautogui

    pyautogui.FAILSAFE = True  # slam mouse into a screen corner to abort
    PYAUTOGUI_OK = True
    PYAUTOGUI_ERR = ""
except Exception as exc:  # ImportError, or "no display" at import time
    pyautogui = None
    PYAUTOGUI_OK = False
    PYAUTOGUI_ERR = str(exc)


# --------------------------------------------------------------------------- #
# Value formatting
# --------------------------------------------------------------------------- #
def fmt(v) -> str:
    """Turn any cell value into a clean string for typing.

    Notably: 137.0 -> "137" (Excel stores whole numbers as floats), NaN -> "".
    """
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if math.isnan(v):
            return ""
        return str(int(v)) if v.is_integer() else ("%g" % v)
    # numpy scalars, if numpy is present
    try:
        import numpy as np

        if isinstance(v, np.integer):
            return str(int(v))
        if isinstance(v, np.floating):
            fv = float(v)
            return "" if math.isnan(fv) else (str(int(fv)) if fv.is_integer() else ("%g" % fv))
    except Exception:
        pass
    s = str(v).strip()
    return "" if s.lower() == "nan" else s


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #
def parse_excel(file, max_scan: int = 15) -> Tuple[List[str], List[List[str]]]:
    """Read an uploaded .xlsx into (headers, records).

    Skips any junk rows above the header (e.g. a row of date serials) by
    locating the row that contains "Master Style" (case-insensitive). Columns
    are defined by the header cells that actually have a label.
    """
    raw = pd.read_excel(file, header=None, engine="openpyxl")

    header_row = None
    for idx in range(min(max_scan, len(raw))):
        cells = [str(x).strip().lower() for x in raw.iloc[idx].tolist()]
        if any(("master style" in c) or c == "style" for c in cells):
            header_row = idx
            break
    if header_row is None:
        header_row = 0  # fall back: assume the first row is the header

    header_vals = [fmt(x) for x in raw.iloc[header_row].tolist()]
    keep = [j for j, h in enumerate(header_vals) if h != ""]
    if not keep:
        keep = list(range(raw.shape[1]))
    headers = [header_vals[j] for j in keep]

    records: List[List[str]] = []
    for r in range(header_row + 1, len(raw)):
        row = raw.iloc[r].tolist()
        vals = [fmt(row[j]) for j in keep]
        if all(v == "" for v in vals):
            continue  # blank row
        if vals[0] == "" and (len(vals) < 2 or vals[1] == ""):
            continue  # no Style/Color -> not a real record
        records.append(vals)
    return headers, records


def parse_pasted(text: str) -> List[List[str]]:
    """Parse pasted text into records. Columns may be Tab- or comma-separated;
    falls back to splitting on any whitespace."""
    lines = [ln for ln in text.splitlines() if ln.strip() != ""]
    if not lines:
        return []
    if "\t" in lines[0]:
        delim: Optional[str] = "\t"
    elif "," in lines[0]:
        delim = ","
    else:
        delim = None  # whitespace
    rows = []
    for ln in lines:
        parts = ln.split(delim) if delim else ln.split()
        rows.append([fmt(p.strip()) for p in parts])
    return rows


# --------------------------------------------------------------------------- #
# Typing engine
# --------------------------------------------------------------------------- #
def type_record(
    values: List[str],
    *,
    tab_after_first: bool = False,
    press_enter: bool = True,
    interval: float = 0.0,
) -> None:
    """Type one record into whatever window currently has focus.

    Field mapping for the projection form:
        values[0]  -> Style. This box auto-advances once it is full, and the
                      Master Style codes are always 6 characters, so by default
                      we do NOT send a Tab after it (the form jumps on its own).
        values[1]  -> Color -> Tab. That single Tab also lands past the
                      non-editable Label column, onto the first month.
        values[2:] -> the monthly fields -> a Tab between each one. The month
                      numbers are shorter than the 6-character box limit, so
                      they do NOT auto-advance; we must Tab ourselves.

    Rule: send a Tab after every field EXCEPT the last (Enter finishes that
    one), and except the first when tab_after_first is False. Turn
    tab_after_first on only if a Style value ever fails to auto-advance.
    """
    if not PYAUTOGUI_OK:
        raise RuntimeError(
            "Keyboard control is unavailable (pyautogui could not start). "
            "This app must run locally on a machine with a display."
        )

    n = len(values)
    for i, val in enumerate(values):
        if val != "":
            pyautogui.write(val, interval=interval)

        if i == n - 1:
            continue  # last field: no Tab; Enter handles it below
        if i == 0 and not tab_after_first:
            continue  # Style auto-advances when full; don't double-advance
        pyautogui.press("tab")

    if press_enter:
        pyautogui.press("enter")
