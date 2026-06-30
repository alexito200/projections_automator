"""
app.py — Projection Form Filler (Streamlit)
===========================================
Loads your projection data (Excel upload or pasted text) and types each record
into a browser form for you: Style, Color, Tab (to skip field 3), the monthly
values, then Enter.

>>> IMPORTANT: run this LOCALLY <<<
    streamlit run app.py
The app simulates keystrokes on the computer it runs on. That only reaches your
browser form if the app runs on YOUR machine. It will NOT work deployed to
Streamlit Community Cloud or any remote server (no desktop to type into).
"""

import time

import pandas as pd
import streamlit as st

import filler_core as core

st.set_page_config(page_title="Projection Form Filler", layout="wide")
st.title("Projection Form Filler")

# --------------------------------------------------------------------------- #
# How it works
# --------------------------------------------------------------------------- #
with st.expander("How this works — read me first", expanded=False):
    st.markdown(
        """
**Run locally.** Start it with `streamlit run app.py` on the same computer you
enter data on. It types keystrokes into your desktop, so it can't work on a
remote/cloud server.

**The flow for each record**
1. Load your data (upload the `.xlsx` or paste rows).
2. Click into the **first field** of the form in your browser.
3. Pick a record here and click **Fill** — you get a short countdown to switch
   back to the browser, then it types: *Style → Color → Tab (skips field 3) →
   each monthly value → Enter*.

**Field count is read from your data:** 2 ID fields + however many monthly
columns the file has. More months = more fields, automatically.

**Abort anytime:** slam your mouse into any screen corner to stop typing.
        """
    )

if not core.PYAUTOGUI_OK:
    st.error(
        "Keyboard control is unavailable here, so filling is disabled. "
        "Install requirements and run locally on a machine with a display "
        "(`pip install -r requirements.txt` then `streamlit run app.py`). "
        f"Details: {core.PYAUTOGUI_ERR}"
    )

# --------------------------------------------------------------------------- #
# 1) Load data
# --------------------------------------------------------------------------- #
st.subheader("1) Load your data")
method = st.radio(
    "Data source",
    ["Upload Excel (.xlsx)", "Paste data"],
    horizontal=True,
    help="Excel upload is recommended — it matches your existing files and "
    "avoids paste/column ambiguity.",
)

records = None
headers = None

if method.startswith("Upload"):
    up = st.file_uploader("Upload your projections file", type=["xlsx", "xlsm"])
    if up is not None:
        try:
            headers, records = core.parse_excel(up)
        except Exception as exc:
            st.error(f"Could not read that file: {exc}")
else:
    txt = st.text_area(
        "Paste rows — one record per line, columns separated by Tab or comma",
        height=160,
        placeholder="917648\tY16\t137\t48\t40\t32\t0\t92",
    )
    skip_first = st.checkbox("First pasted row is a header (skip it)", value=False)
    if txt.strip():
        rows = core.parse_pasted(txt)
        if skip_first and rows:
            rows = rows[1:]
        records = rows
        headers = None

# Persist across reruns
if records:
    st.session_state["records"] = records
    st.session_state["headers"] = headers

records = st.session_state.get("records")
headers = st.session_state.get("headers")

if not records:
    st.info("Load a file or paste data to begin.")
    st.stop()

# Preview
width = max(len(r) for r in records)
prev_rows = [r + [""] * (width - len(r)) for r in records]
cols = headers if (headers and len(headers) == width) else [f"Col {i + 1}" for i in range(width)]
st.dataframe(pd.DataFrame(prev_rows, columns=cols), use_container_width=True, height=240)

months = max(0, len(records[0]) - 2)
st.caption(
    f"Detected {len(records[0])} columns per record → fills 2 ID fields, "
    f"skips field 3, then enters {months} monthly value(s), then Enter. "
    f"({len(records)} records loaded.)"
)

# --------------------------------------------------------------------------- #
# 2) Settings
# --------------------------------------------------------------------------- #
st.subheader("2) Settings")
c1, c2, c3 = st.columns(3)
secs = c1.number_input("Seconds to switch to your form", 1, 30, 5)
interval = c2.number_input(
    "Typing speed (sec/char)", 0.0, 0.5, 0.0, step=0.01,
    help="0 = instant. Raise a little if a slow form drops characters.",
)
tab_after_first = c3.checkbox(
    "Send a Tab after the Style field too", value=False,
    help="Leave OFF: the Style box fills to its 6-character limit and the form "
    "jumps to Color on its own. Turn ON only if Style and Color end up in the "
    "SAME box.",
)
press_enter = st.checkbox("Press Enter after the last field", value=True)

# --------------------------------------------------------------------------- #
# 3) Fill
# --------------------------------------------------------------------------- #
st.subheader("3) Fill")

if "idx" not in st.session_state:
    st.session_state.idx = 0
st.session_state.idx = max(0, min(st.session_state.idx, len(records) - 1))
i = st.session_state.idx

nav1, nav2, nav3 = st.columns([1, 3, 1])
if nav1.button("Prev", use_container_width=True):
    st.session_state.idx = max(0, i - 1)
    st.rerun()
nav2.markdown(
    f"**Record {i + 1} of {len(records)}** — " + " / ".join(records[i][:2])
)
if nav3.button("Next", use_container_width=True):
    st.session_state.idx = min(len(records) - 1, i + 1)
    st.rerun()

disabled = not core.PYAUTOGUI_OK
fill_one = st.button("▶ Fill this record", type="primary", disabled=disabled)
with st.container():
    gap = st.number_input("Pause between records when filling all (sec)", 1, 60, 3)
    fill_all = st.button(
        "▶▶ Fill ALL records (test with one first!)", disabled=disabled
    )


def run_fill(indices):
    ph = st.empty()
    for s in range(int(secs), 0, -1):
        ph.warning(
            f"Switch to your form and click the FIRST field… starting in {s}s "
            "(slam the mouse into a screen corner to abort)"
        )
        time.sleep(1)
    try:
        for k, idx in enumerate(indices):
            ph.info(f"Typing record {idx + 1}…")
            core.type_record(
                records[idx],
                tab_after_first=tab_after_first,
                press_enter=press_enter,
                interval=float(interval),
            )
            if k < len(indices) - 1:
                ph.info(f"Record {idx + 1} done. Next in {int(gap)}s…")
                time.sleep(int(gap))
        ph.success(f"Done — {len(indices)} record(s) filled.")
    except Exception as exc:
        ph.error(f"Stopped: {exc}")


if fill_one:
    run_fill([st.session_state.idx])
if fill_all:
    run_fill(list(range(len(records))))
