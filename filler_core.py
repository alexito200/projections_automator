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
    auto_advance: bool,
    press_enter: bool,
    interval: float = 0.0,
) -> None:
    """Type one record into whatever window currently has focus.

    Field mapping (your form):
        value[0] -> field 1 (Master Style)
        value[1] -> field 2 (Color)
        field 3  -> SKIPPED via Tab (no data)
        value[2:] -> field 4, 5, ... (monthly projections)

    auto_advance=True  : the form moves between fields itself; we press Tab
                         ONLY after the 2nd field (to skip field 3). Matches
                         "Tab only after the second field, always."
    auto_advance=False : we drive every move -> Tab after each field, and an
                         extra Tab after field 2 so field 3 is skipped.
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

        is_last = i == n - 1
        if auto_advance:
            if i == 1:  # after the 2nd field -> one Tab skips field 3
                pyautogui.press("tab")
        else:
            if i == 1:
                pyautogui.press("tab")  # leave field 2
                pyautogui.press("tab")  # skip field 3
            elif not is_last:
                pyautogui.press("tab")  # advance to next field

    if press_enter:
        pyautogui.press("enter")
