# Demos

Each teaching demo lives in its own folder under `demos/`.

The first demo is [`montenegro-res-news/`](montenegro-res-news/): a search → analyse → report agent on Montenegro’s Renewable Energy Sources (RES) Law and first solar auction.

## Layout convention

```
demos/<slug>/
  README.md          # how to run this demo in class
  requirements.txt   # Python deps for this demo only
  <package>/         # importable code (run as python -m <package>)
  sample/            # pre-run artifacts (classroom fallback)
  tests/             # pytest
```

Keep demos **self-contained**. Shared ideas belong in this file and the root README, not a heavy framework.

## Adding a later demo

1. Copy the folder shape above. Use a short kebab-case slug (`demos/albania-grid-brief/`).
2. Write a README that a colleague can follow in five minutes: install, env vars, run, what “good” output looks like, and when to use the sample.
3. Check in a **sample / pre-run** so the session still works without live web access or API keys.
4. If the live path needs a key, fail **gracefully** to the sample. Do not invent rows, quotes, or sources.
5. Link the new demo from the root `README.md`.
6. Visuals (HTML reports, charts, notebooks): clean workshop look — white or light neutrals, readable tables, quiet colour. Not neon, not “terminal hacker”, not a marketing landing page.
7. If the demo is meant to be hosted (e.g. Railway), keep a thin web wrapper in the demo folder and put deploy config at the **repo root** unless the service Root Directory is the demo itself.

## Shared teaching rules (from the Montenegro mandate)

These are useful defaults for later evidence-style demos:

- Quote the source for every claim.
- Write `not found` instead of inferring missing facts (dates, quotes, tones).
- Keep a log of every search.
- Published news and official statements only — no social media — unless a later brief says otherwise.
