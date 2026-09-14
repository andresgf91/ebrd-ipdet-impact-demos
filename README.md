# EBRD / IPDET Impact London — course demos

Teaching demos for **IPDET Impact London** (28–29 September 2026).

Owner: **Andrés González Flores / Filo Analytics**.

This repo is a **folder of demos**, not a one-off script. Each session piece lives under [`demos/`](demos/) so later exercises can drop in beside the first.

## Demos

| Folder | What it teaches |
| --- | --- |
| [`demos/montenegro-res-news/`](demos/montenegro-res-news/) | Search → analyse → report agent on Montenegro’s RES Law and first solar auction (slide: *What the agent does* / *The mandate*) |

## How to run (classroom)

You only need the demo you are teaching. From that folder:

```bash
python -m pip install -r requirements.txt
python -m montenegro_res_news --sample    # always works offline
```

Default `python -m montenegro_res_news` tries a **live** web search, then falls back to the checked-in sample if the live harvest is thin or fails. It does **not** invent articles.

See the demo README for API keys and the HTML handout.

## How to add a later demo

Follow [`demos/README.md`](demos/README.md). Short version: new folder, its own README + sample fallback, link it in the table above, keep live paths honest, and keep any HTML/charts in a **quiet workshop style** (light background, readable tables — not neon “tech”).

## Design note (Andrés)

Reports, tone strips and any other visuals: **clean and calm**. White or light neutrals, simple type, evaluation-handout aesthetic. Not a startup landing page and not a terminal.
