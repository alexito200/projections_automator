# Projection Form Filler

A small local Streamlit app that types your projection data into a browser
form for you. For each record it enters **Master Style**, **Color**, presses
**Tab once to skip the third field**, types each **monthly projection value**,
and finishes with **Enter**. The number of monthly fields is read from your
data, so files with more months just work.

---

## ⚠️ Must run locally

This app simulates keystrokes on the computer it runs on. That only reaches
your browser form when the app runs on **your own machine**:

```bash
streamlit run app.py
```

It will **not** work deployed to Streamlit Community Cloud or any remote
server — there is no desktop there for it to type into.

---

## Setup

```bash
# from the repo folder
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Platform notes for the keystroke part (pyautogui):
- **macOS** — grant Accessibility permission to your terminal / Python in
  System Settings → Privacy & Security → Accessibility.
- **Linux** — works under X11; Wayland may block synthetic key events.

---

## Using it

1. **Load data** — upload your `.xlsx` (recommended) or paste rows.
2. **Open the form** in your browser and click into its **first field**.
3. Back in the app, pick a record and click **Fill**. You get a short
   countdown to switch to the browser, then it types the record.
4. Use **Prev / Next** to step through records, or **Fill ALL** to run the
   whole list with a pause between each (test a single record first).

**Abort anytime:** slam the mouse into any screen corner.

---

## Data format

The Excel reader expects a header row containing `Master Style` and `Color`
followed by the monthly `PROJ UNITS…` columns. Any junk rows above the header
(e.g. a row of Excel date serials) are skipped automatically. Each row below
the header is one record:

| Master Style | Color | PROJ UNITS2 | PROJ UNITS3 | … |
| ------------ | ----- | ----------- | ----------- | - |
| 917648       | Y16   | 137         | 48          | … |

For pasted data, put one record per line with columns separated by Tab or
comma; tick *"First pasted row is a header"* if you include the header line.

---

## The Tab logic (important)

By default the app presses **Tab only after the second field** — this assumes
your form **auto-advances** between fields as you type, which is the only way
"no Tab between the other fields" works mechanically.

If, on your first test, **Style and Color end up in the same box**, your form
does *not* auto-advance. Untick **"My form auto-advances between fields"** in
Settings — the app will then Tab after every field (and twice after field 2 to
skip field 3).

Other settings:
- **Seconds to switch** — countdown before typing starts.
- **Typing speed** — raise slightly if a slow form drops characters.
- **Press Enter at end** — on by default.

---

## Files

- `app.py` — the Streamlit interface.
- `filler_core.py` — data parsing + the keystroke engine (no UI).
- `requirements.txt` — dependencies.
