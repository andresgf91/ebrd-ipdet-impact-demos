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

Writes `output/report.html` (quiet paper-style handout) and `output/report.md`. The CLI does not start a server.

**Default (try live, then sample):**

```bash
python -m montenegro_res_news
```

**Live only** (honest, possibly short):

```bash
python -m montenegro_res_news --live --outdir ./output
```

## Local web (classroom URL)

Same HTML as the sample, served so you can share a link (and deploy to Railway):

```bash
python -m pip install -r requirements.txt
python -m uvicorn montenegro_res_news.web:app --host 127.0.0.1 --port 8000
# same thing, reads PORT (default 8000):
# PORT=8000 python -m montenegro_res_news.web
```

Open http://127.0.0.1:8000/ — the page plays the checked-in sample as an agent loop (goal, tools, plan/reason, action, observation, memory, stop), then leaves the two-line summary, tone-by-month strip, quoted table, and search log on screen. Replay restarts that run. No API key is required. `GET /health` is the Railway health check.

**Try live search** on that page only runs if `TAVILY_API_KEY`, `BRAVE_API_KEY`, or `NEWSAPI_KEY` is set. If none are set, the page stays on the sample and says so. It does not invent articles. DuckDuckGo is used by the CLI when no key is present; the web app does not call it automatically (Railway IPs are often blocked).

## Railway

Canonical config is at the **repository root** (this is a course-demos repo; the start command then `cd`s into this folder):

| File | Role |
| --- | --- |
| [`railway.toml`](../../railway.toml) | Nixpacks + start command + `/health` |
| [`Procfile`](../../Procfile) | `web:` process, listens on `$PORT` |
| [`requirements.txt`](../../requirements.txt) | `-r demos/montenegro-res-news/requirements.txt` |
| [`Procfile`](Procfile) / [`railway.toml`](railway.toml) here | Use these if you set the Railway **Root Directory** to `demos/montenegro-res-news` |

**Deploy from GitHub (typical):**

1. [New project](https://railway.com/new) → Deploy from GitHub repo `ebrd-ipdet-impact-demos`.
2. Leave the root as the repository root so `railway.toml` applies. Do **not** invent a start command unless you override the file.
3. Railway injects `PORT`. Optional variables: `TAVILY_API_KEY`, `BRAVE_API_KEY`, `NEWSAPI_KEY` (live button); `OPENAI_API_KEY` (optional live labels).
4. Generate a public URL. `/` is the sample handout; `/health` should return `{"status":"ok",...}`.

**CLI deploy** (from a clone of this repo):

```bash
npm i -g @railway/cli   # or see https://docs.railway.com/guides/cli
railway login
railway init            # link this repo
railway up
```

If you prefer the service root to be this demo folder, set **Root Directory** to `demos/montenegro-res-news` in the Railway service settings. Then this folder’s `Procfile` and `requirements.txt` are enough; the start command is `python -m montenegro_res_news.web` (listens on `$PORT`).

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

- Let the page play the loop, or click a step: **goal, tools, plan/reason, action, observation, memory, stop**. Then read the summary, the strip, the quoted table, and the log.
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
