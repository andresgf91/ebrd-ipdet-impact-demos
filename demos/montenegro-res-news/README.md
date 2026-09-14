# Montenegro RES / solar auction news agent

First teaching demo for **IPDET Impact London** (28–29 September 2026).

Implements the slide brief: search published coverage of Montenegro’s Renewable Energy Sources (RES) Law and the first solar auction → extract a quoted claim, **tone** and **topic** → write a table, a **two-line summary**, and a **tone-by-month strip**.

## What the agent does

1. **Search** — local and international news plus official statements (last **12 months** on the live path). No social media.
2. **Analyse** — for each hit, a quote about the reform, tone (`positive` / `negative` / `neutral`) with a one-line justification, and a topic (`investor interest`, `grid`, `coal phase-out`, `permitting`, or a related topic if the quote supports it).
3. **Report** — table (`outlet`, `date`, `link`, `quote`, `tone`, `topic`) + two-line summary of what has shifted since the law passed + tone-by-month strip.

## Mandate (constraints)

- Goal: evidence on how the RES Law and auctions are being **received**.
- Scope: published news and official statements only.
- Quote the source for every claim.
- Write **`not found`** rather than infer (including missing dates).
- Log **every search**.
- Quality target: **≥ 20 articles**; every tone label has a one-line justification.
- If live search is flaky in the room, use the **pre-run sample**.

The agent will not invent rows to hit 20. If live results are short, it falls back to the sample (unless you pass `--live`).

## Install

Python 3.11+. From this folder:

```bash
python -m pip install -r requirements.txt
```

Optional keys (copy `.env.example` — or export in the shell). None are required for `--sample`:

| Variable | Backend |
| --- | --- |
| `TAVILY_API_KEY` | [Tavily](https://tavily.com) web search (tried first) |
| `BRAVE_API_KEY` | [Brave Search](https://brave.com/search/api/) |
| `NEWSAPI_KEY` | [NewsAPI](https://newsapi.org) |
| *(none)* | DuckDuckGo via `ddgs` |

`OPENAI_API_KEY` is optional. Without it, live tone/topic labels use a **keyword heuristic** you can show on the projector. The sample table is **hand-labelled** from the quoted pages.

## How to run in class

**Fallback (recommended if wifi/API is uncertain):**

```bash
python -m montenegro_res_news --sample
```

Opens nothing in a browser by itself. Open `output/report.html` (quiet paper-style handout) or `output/report.md`.

**Default (try live, then sample):**

```bash
python -m montenegro_res_news
```

**Live only** (honest, possibly short):

```bash
python -m montenegro_res_news --live --outdir ./output
```

## What “good” output looks like

| File | Role |
| --- | --- |
| `output/report.html` | Classroom handout: mandate, two-line summary, tone-by-month strip, table, search log |
| `output/report.md` | Same content in Markdown |
| `output/table.csv` | Spreadsheet of the agent table |
| `output/search_log.json` | Every query, backend, timestamp, hit count, error |
| `output/summary.txt` | The two-line summary alone |

Checked-in copies of a successful pre-run live in [`sample/`](sample/) (frozen 14 September 2026). The sample window starts at **law passage (August 2024)** so the summary can show what shifted since the law passed. Live search stays on the slide’s **last 12 months**.

The HTML uses a white/cream page, serif headings, muted green/brick/grey for tone — an evaluation brief, not a dashboard.

## Teaching notes

- Walk **search log → table → strip → two-liner**. The log is the audit trail.
- Point at the JPM row: **date = `not found`** because the page did not print a publish date. That is the constraint working.
- Tone is about **how the piece receives the reform**, not whether auctions are good policy.
- Live classification without an LLM will be coarser than the sample. That is a feature: students can disagree with a heuristic using the quote.

## Tests

```bash
python -m pytest
```

## Regenerating the sample handout

After editing `sample/articles.json`:

```bash
python -m montenegro_res_news --sample --write-sample
```
