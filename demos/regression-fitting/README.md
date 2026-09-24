# Regression fitting

A screen-recordable walkthrough of the BA climate credit line: 214 synthetic sub-loans, and why the 11.3× result is deal mix rather than a causal effect of the line.

The page does not call a model. It plays a captured run of `analyze_climate_subloans.py`.

## Start a recording

1. Open `index.html` in a browser (double-click, or `open index.html` from this folder). `copilot.html` is the Copilot live result, linked from the walkthrough.
2. Use the window at laptop size. Play, Pause, and Step sit along the bottom.
3. Press Play and let the four beats run, or Step through them: the mandate, the script being written, the run, then the results.
4. For a live Copilot take, paste `copilot_live_prompt.txt` and attach `data/ba_loan_climate_subloans.csv`. That file is for the live recording. The page only points at it.

## Run the script

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 analyze_climate_subloans.py
```

The captured stdout from 24 September 2026 is in `sample/script_stdout.txt`. If the script cannot run, read `prerun_fallback_output.txt` instead. The walkthrough numbers match that fallback: naive R² 0.441, log-log R² 0.958, elasticity 0.97.

## What is in this folder

| File | Role |
| --- | --- |
| `index.html` | Recordable walkthrough |
| `analyze_climate_subloans.py` | The analysis that is typed on screen and that was run |
| `data/ba_loan_climate_subloans.csv` | Synthetic sub-loans, built to the case totals |
| `live_demo_prompt.txt` | Original classroom prompt |
| `copilot_live_prompt.txt` | Paste this for a live Copilot recording |
| `prerun_fallback_output.txt` | Pre-run write-up if the script cannot run |
| `sample/script_stdout.txt` | Captured script output used on the page |
