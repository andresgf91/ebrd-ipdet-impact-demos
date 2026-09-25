"""Classroom page: an agent loop on screen, then the evidence it produced.

Steps, in order: goal, tools, plan/reason, action, observation, memory, stop.
With JavaScript the sample run reveals them one step at a time. Without it,
or with reduced motion, the full page is shown at once.
"""

from __future__ import annotations

import html
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from montenegro_res_news.mandate import GOAL, QUALITY_MIN_ARTICLES, SAMPLE_FREEZE_DATE, SCOPE

# Workshop palette: paper, ink, muted evaluation-report colours. No neon.
CSS = """
:root {
  --paper: #f7f5f1;
  --card: #ffffff;
  --ink: #2b2a27;
  --muted: #6d6860;
  --line: #e3ddd4;
  --accent: #3f5c4c;
  --positive: #3f5c4c;
  --negative: #8a5348;
  --neutral: #7a746c;
}
* { box-sizing: border-box; }
html, body {
  margin: 0;
  padding: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  line-height: 1.5;
  font-size: 17px;
}
.skip {
  position: absolute;
  left: -999px;
  top: 0;
}
.skip:focus {
  left: 0.75rem;
  top: 0.75rem;
  background: var(--card);
  padding: 0.35rem 0.6rem;
  z-index: 8;
}
.wrap {
  max-width: 1120px;
  margin: 0 auto;
  padding: 1.25rem 1.35rem 2.75rem;
}
.top {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-end;
  gap: 0.75rem 1.25rem;
  margin-bottom: 0.85rem;
}
.top-text { flex: 1 1 34rem; min-width: 0; }
h1 {
  font-family: Georgia, "Times New Roman", serif;
  font-weight: 400;
  font-size: 1.7rem;
  letter-spacing: -0.01em;
  line-height: 1.25;
  margin: 0.15rem 0 0.3rem;
}
.kicker, .status {
  color: var(--muted);
  font-size: 0.92rem;
  margin: 0;
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: center;
  justify-content: flex-end;
}
.actions form { margin: 0; }
.actions button,
.actions a.quiet,
.filters button {
  font: inherit;
  font-size: 0.9rem;
  background: var(--card);
  color: var(--ink);
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 0.38rem 0.72rem;
  cursor: pointer;
  text-decoration: none;
}
.actions button:hover,
.actions a.quiet:hover,
.filters button:hover,
.loop button:hover { border-color: #cfc8bc; }
button:focus-visible,
a:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
html.is-settled #skip-run { display: none; }
.banner {
  background: var(--card);
  border: 1px solid var(--line);
  border-left: 3px solid var(--accent);
  border-radius: 6px;
  padding: 0.75rem 1rem;
  margin: 0 0 0.9rem;
  font-size: 0.95rem;
}
.loop-wrap {
  position: sticky;
  top: 0;
  z-index: 4;
  background: var(--paper);
  margin: 0 0 1rem;
  padding: 0.45rem 0 0.55rem;
  border-bottom: 1px solid var(--line);
}
.loop {
  list-style: none;
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 0.4rem;
  margin: 0;
  padding: 0;
}
.loop button {
  width: 100%;
  text-align: left;
  font: inherit;
  background: var(--card);
  color: var(--muted);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 0.42rem 0.5rem 0.48rem;
  cursor: pointer;
}
.loop .n {
  display: block;
  font-size: 0.68rem;
  letter-spacing: 0.04em;
}
.loop .name {
  display: block;
  color: var(--ink);
  font-weight: 600;
  font-size: 0.86rem;
  line-height: 1.25;
}
.loop .gloss {
  display: block;
  margin-top: 0.12rem;
  font-size: 0.75rem;
  line-height: 1.3;
}
.loop button.now {
  border-color: var(--accent);
  box-shadow: inset 0 0 0 1px var(--accent);
  color: var(--ink);
}
.loop button.done .n { color: var(--accent); }
html.js-run .loop button:not(.done):not(.now) { opacity: 0.55; }
main { min-height: 68vh; }
.card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 0.95rem 1.1rem 1.05rem;
  margin-bottom: 0.85rem;
}
.setup {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
  gap: 0.85rem 1.2rem;
}
.setup .panel + .panel {
  border-left: 1px solid var(--line);
  padding-left: 1rem;
}
h2 {
  font-family: Georgia, "Times New Roman", serif;
  font-weight: 400;
  font-size: 1.28rem;
  margin: 0 0 0.45rem;
}
.setup h2 { font-size: 1.12rem; margin-bottom: 0.35rem; }
.step-kicker {
  margin: 0 0 0.15rem;
  color: var(--accent);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.note { color: var(--muted); font-size: 0.88rem; margin: 0.45rem 0 0; }
.setup p, .card > p { margin: 0.2rem 0 0; }
.setup ul, .tight {
  margin: 0.4rem 0 0;
  padding-left: 1.1rem;
}
.setup li { margin: 0.15rem 0; }
.summary .lead {
  max-width: 68ch;
  font-size: 1.06rem;
  line-height: 1.45;
  margin: 0 0 0.55rem;
}
.summary .lead:last-child { margin-bottom: 0; }
html.js-run footer { display: none; }
html.js-run .panel { display: none; }
html.js-run .panel.shown { display: block; animation: rise 0.35s ease; }
html.js-run .setup:not(:has(.panel.shown)) { display: none; }
.panel { scroll-margin-top: 7rem; }
.panel.current { box-shadow: inset 3px 0 0 var(--accent); }
.setup .panel.current { padding-left: 0.7rem; }
@keyframes rise {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: none; }
}
.strip {
  display: flex;
  gap: 0.7rem;
  align-items: flex-end;
  overflow-x: auto;
  padding: 0.35rem 0 0.15rem;
}
.month { min-width: 4.1rem; text-align: center; }
.month.wide { min-width: 5.8rem; }
.bars {
  height: 108px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 4px;
}
.col { display: flex; flex-direction: column; align-items: center; justify-content: flex-end; }
.tick {
  min-height: 0.85rem;
  font-size: 0.68rem;
  font-weight: 600;
  line-height: 1;
}
.tick.positive { color: var(--positive); }
.tick.negative { color: var(--negative); }
.tick.neutral { color: var(--neutral); }
.bar { width: 10px; border-radius: 2px 2px 0 0; }
.bar.positive { background: var(--positive); }
.bar.negative { background: var(--negative); }
.bar.neutral { background: var(--neutral); opacity: 0.8; }
.month label {
  display: block;
  margin-top: 0.35rem;
  font-size: 0.68rem;
  color: var(--muted);
}
.legend { font-size: 0.84rem; color: var(--muted); margin: 0.65rem 0 0; }
.legend span { margin-right: 0.9rem; }
.swatch {
  display: inline-block;
  width: 9px;
  height: 9px;
  margin-right: 0.28rem;
  vertical-align: middle;
  border-radius: 2px;
}
.swatch.positive { background: var(--positive); }
.swatch.negative { background: var(--negative); }
.swatch.neutral { background: var(--neutral); }
.filters { display: flex; flex-wrap: wrap; gap: 0.35rem; margin: 0.2rem 0 0.7rem; }
.filters button.is-on {
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
}
.table-scroll {
  overflow: auto;
  max-height: 28rem;
  border-top: 1px solid var(--line);
}
table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
th, td {
  text-align: left;
  vertical-align: top;
  padding: 0.55rem 0.5rem;
  border-bottom: 1px solid var(--line);
}
th {
  position: sticky;
  top: 0;
  background: var(--card);
  z-index: 1;
  font-weight: 600;
  color: var(--muted);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
td:first-child { font-weight: 600; min-width: 8.5rem; }
td:nth-child(2), td:nth-child(3) { white-space: nowrap; }
td.quote { overflow-wrap: anywhere; }
a { color: var(--accent); }
.tone {
  display: inline-block;
  white-space: nowrap;
  font-weight: 600;
  font-size: 0.8rem;
  padding: 0.08rem 0.45rem;
  border-radius: 999px;
}
.tone.positive { color: var(--positive); background: #e7efe9; }
.tone.negative { color: var(--negative); background: #f6ecea; }
.tone.neutral { color: var(--neutral); background: #f1efec; }
.just { color: var(--muted); font-size: 0.8rem; display: block; margin-top: 0.2rem; font-weight: 400; }
.missing { color: var(--negative); font-weight: 600; }
.queries { list-style: none; margin: 0.4rem 0 0; padding: 0; max-height: 18rem; overflow: auto; }
.queries li { padding: 0.45rem 0; border-bottom: 1px solid var(--line); }
.queries .q { display: block; }
.queries .meta { display: block; color: var(--muted); font-size: 0.8rem; }
.queries li.is-error .meta { color: var(--negative); }
.queries .note { display: block; margin-top: 0.15rem; }
footer { color: var(--muted); font-size: 0.82rem; margin-top: 1.25rem; }
footer p { margin: 0.15rem 0; }
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}
@media (max-width: 860px) {
  .loop { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .setup { grid-template-columns: 1fr; }
  .setup .panel + .panel {
    border-left: 0;
    padding-left: 0;
    border-top: 1px solid var(--line);
    padding-top: 0.75rem;
  }
}
@media (max-width: 560px) {
  .loop { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .loop-wrap { position: static; }
  h1 { font-size: 1.45rem; }
}
@media (prefers-reduced-motion: reduce) {
  html.js-run .panel.shown { animation: none; }
}
@media print {
  html.js-run .panel { display: block !important; }
  .loop-wrap { position: static; }
  .actions, #replay, #skip-run { display: none; }
  .table-scroll, .queries { max-height: none; overflow: visible; }
}
"""

HEAD_JS = """
(function () {
  try {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    document.documentElement.classList.add("js-run");
  } catch (err) {}
})();
"""

RUN_JS = """
(function () {
  try {
    var root = document.documentElement;
    var steps = ["goal", "tools", "plan", "action", "observation", "memory", "stop"];
    var buttons = steps.map(function (id) {
      return document.querySelector('[data-step="' + id + '"]');
    });
    var panels = steps.map(function (id) {
      return document.querySelector('[data-panel="' + id + '"]');
    });
    var live = document.getElementById("live-status");
    var timer = null;
    var index = -1;
    var settled = false;
    var reduce = false;
    try {
      reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    } catch (err) {}

    function lineOf(i) {
      var panel = panels[i];
      if (!panel) return "";
      var node = panel.querySelector("[data-line]");
      return node ? node.textContent.replace(/\\s+/g, " ").trim() : "";
    }

    function setStatus(i) {
      if (!live || i < 0) return;
      var btn = buttons[i];
      var nameNode = btn ? btn.querySelector(".name") : null;
      var name = nameNode ? nameNode.textContent.trim() : steps[i];
      live.textContent = "Step " + (i + 1) + " of " + steps.length + ". " + name + ". " + lineOf(i);
    }

    function paint(i, collapse) {
      panels.forEach(function (panel, n) {
        if (!panel) return;
        panel.classList.toggle("shown", collapse ? n <= i : true);
        panel.classList.toggle("current", n === i);
      });
      buttons.forEach(function (btn, n) {
        if (!btn) return;
        btn.classList.toggle("now", n === i);
        btn.classList.toggle("done", collapse ? n < i : n !== i);
        btn.setAttribute("aria-current", n === i ? "step" : "false");
      });
      setStatus(i);
    }

    function scrollToStep(i) {
      var panel = panels[i];
      if (!panel) return;
      window.requestAnimationFrame(function () {
        panel.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "nearest" });
      });
    }

    function pause() {
      if (timer) {
        window.clearInterval(timer);
        timer = null;
      }
    }

    function settle() {
      pause();
      settled = true;
      root.classList.remove("js-run");
      root.classList.add("is-settled");
      panels.forEach(function (panel) {
        if (!panel) return;
        panel.classList.add("shown");
        panel.classList.remove("current");
      });
      buttons.forEach(function (btn) {
        if (!btn) return;
        btn.classList.add("done");
        btn.classList.remove("now");
        btn.setAttribute("aria-current", "false");
      });
      if (live) {
        live.textContent = "Run finished. Summary, tone strip, quoted articles, and search log are on the page.";
      }
    }

    function play() {
      if (reduce) {
        settle();
        return;
      }
      pause();
      settled = false;
      root.classList.add("js-run");
      root.classList.remove("is-settled");
      index = 0;
      paint(0, true);
      scrollToStep(0);
      timer = window.setInterval(function () {
        if (index >= steps.length - 1) {
          settle();
          return;
        }
        index += 1;
        paint(index, true);
        scrollToStep(index);
      }, 1600);
    }

    buttons.forEach(function (btn, i) {
      if (!btn) return;
      btn.addEventListener("click", function () {
        pause();
        if (settled) {
          paint(i, false);
          buttons.forEach(function (other, n) {
            if (!other) return;
            other.classList.add("done");
            other.classList.toggle("now", n === i);
          });
          scrollToStep(i);
          return;
        }
        index = i;
        paint(i, true);
        scrollToStep(i);
      });
    });

    var replay = document.getElementById("replay");
    if (replay) {
      replay.addEventListener("click", function () {
        window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
        play();
      });
    }
    var skip = document.getElementById("skip-run");
    if (skip) skip.addEventListener("click", settle);

    document.querySelectorAll("[data-tone-filter]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var tone = btn.getAttribute("data-tone-filter") || "all";
        var visible = 0;
        document.querySelectorAll("#quotes tbody tr").forEach(function (row) {
          if (row.getAttribute("data-empty")) return;
          var show = tone === "all" || row.getAttribute("data-tone") === tone;
          row.hidden = !show;
          if (show) visible += 1;
        });
        var empty = document.getElementById("filter-empty");
        if (empty) empty.hidden = tone === "all" || visible > 0;
        document.querySelectorAll("[data-tone-filter]").forEach(function (other) {
          var on = other === btn;
          other.classList.toggle("is-on", on);
          other.setAttribute("aria-pressed", on ? "true" : "false");
        });
      });
    });

    if (reduce || !root.classList.contains("js-run")) settle();
    else play();
  } catch (err) {
    document.documentElement.classList.remove("js-run");
    document.documentElement.classList.add("is-settled");
  }
})();
"""

LOOP_STEPS = (
    ("goal", "Goal", "the question"),
    ("tools", "Tools", "allowed moves"),
    ("plan", "Plan / reason", "before acting"),
    ("action", "Action", "searches run"),
    ("observation", "Observation", "what came back"),
    ("memory", "Memory", "what is kept"),
    ("stop", "Stop", "why it halted"),
)


def build_html(
    rows: list[dict[str, Any]],
    strip: list[dict[str, Any]],
    summary: str,
    search_log: list[dict[str, Any]],
    mode: str,
    backend: str,
    fallback_reason: str | None,
    generated: str,
    *,
    toolbar_html: str = "",
    notice: str | None = None,
    show_live: bool = False,
    live_backends: list[str] | None = None,
) -> str:
    tones = Counter(str(row.get("tone") or "neutral") for row in rows)
    undated = [row for row in rows if str(row.get("date") or "not found") == "not found"]
    banner = _banner_text(notice, fallback_reason)
    show_sample_link = show_live and (bool(banner) or mode == "live")

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Montenegro RES Law and first solar auction — media reception</title>
  <style>{CSS}</style>
  <script>{HEAD_JS}</script>
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <div class="wrap">
    <header class="top">
      <div class="top-text">
        <p class="kicker">IPDET Impact London · 28–29 September 2026</p>
        <h1>Montenegro RES Law and the first solar auction</h1>
        <p class="status">{html.escape(_status_line(rows, mode, backend, live_backends))}</p>
      </div>
      {_actions_html(show_live=show_live, show_sample_link=show_sample_link)}
    </header>
    <main id="main">
      {toolbar_html}
      {_banner_html(banner)}
      <nav class="loop-wrap" aria-label="Agent loop">
        <ol class="loop">
          {_loop_html()}
        </ol>
      </nav>
      <div id="live-status" class="sr-only" aria-live="polite"></div>
      <section class="card setup">
        {_goal_html()}
        {_tools_html(mode, backend, live_backends)}
        {_plan_html()}
      </section>
      {_action_html(search_log, mode, backend)}
      {_observation_html(rows, strip, tones, undated)}
      {_memory_html(summary)}
      {_stop_html(rows)}
    </main>
    <footer>
      <p>IPDET Impact London · 28–29 September 2026 · Filo Analytics</p>
      <p>Generated {html.escape(generated)} · {html.escape(mode)} / {html.escape(backend)}</p>
    </footer>
  </div>
  <script>{RUN_JS}</script>
</body>
</html>
"""
    return page


def html_from_result(
    result: dict[str, Any],
    *,
    toolbar_html: str = "",
    notice: str | None = None,
    show_live: bool = False,
    live_backends: list[str] | None = None,
) -> str:
    from montenegro_res_news.report import tone_by_month, two_line_summary

    rows = result["rows"]
    summary = two_line_summary(rows, mode=result["mode"])
    strip = tone_by_month(rows)
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return build_html(
        rows,
        strip,
        summary,
        result["log"],
        result["mode"],
        result["backend"],
        result.get("fallback"),
        generated,
        toolbar_html=toolbar_html,
        notice=notice,
        show_live=show_live,
        live_backends=live_backends,
    )


def _banner_text(notice: str | None, fallback: str | None) -> str | None:
    if notice:
        return notice
    if not fallback:
        return None
    if "No live web search was performed" in fallback:
        return None
    return fallback


def _banner_html(text: str | None) -> str:
    if not text:
        return ""
    return f"<p class='banner' role='status'>{html.escape(text)}</p>"


def _status_line(
    rows: list[dict[str, Any]],
    mode: str,
    backend: str,
    live_backends: list[str] | None,
) -> str:
    count = len(rows)
    if mode == "live":
        return f"Live search · {backend} · {count} articles"
    frozen = SAMPLE_FREEZE_DATE.strftime("%d %B %Y").lstrip("0")
    if live_backends:
        return (
            f"Classroom sample · {count} articles · frozen {frozen} · "
            f"live key set ({', '.join(live_backends)})"
        )
    return f"Classroom sample · {count} articles · frozen {frozen} · no API key"


def _actions_html(*, show_live: bool, show_sample_link: bool) -> str:
    parts = [
        "<div class='actions'>",
        "<button type='button' id='replay'>Replay run</button>",
        "<button type='button' id='skip-run'>Skip to results</button>",
    ]
    if show_live:
        parts.append(
            "<form method='post' action='/live'><button type='submit'>Try live search</button></form>"
        )
    if show_sample_link:
        parts.append("<a class='quiet' href='/'>Classroom sample</a>")
    parts.append("</div>")
    return "".join(parts)


def _loop_html() -> str:
    items = []
    for number, (step_id, label, gloss) in enumerate(LOOP_STEPS, start=1):
        items.append(
            "<li><button type='button' "
            f"data-step='{step_id}' aria-current='false'>"
            f"<span class='n'>{number}</span>"
            f"<span class='name'>{html.escape(label)}</span>"
            f"<span class='gloss'>{html.escape(gloss)}</span>"
            "</button></li>"
        )
    return "".join(items)


def _goal_html() -> str:
    return (
        "<div class='panel' data-panel='goal'>"
        "<h2>Goal</h2>"
        f"<p data-line>{html.escape(GOAL)}</p>"
        f"<p class='note'>{html.escape(SCOPE)}</p>"
        "</div>"
    )


def _tools_html(mode: str, backend: str, live_backends: list[str] | None) -> str:
    if mode == "live":
        extra = f"This run searched with {backend}, then quoted and labelled the pages."
    elif live_backends:
        names = ", ".join(live_backends)
        extra = (
            f"A live key is set ({names}). This view is still the checked-in sample "
            "until you try live search."
        )
    else:
        extra = "This run reads the checked-in sample. No API key."
    return (
        "<div class='panel' data-panel='tools'>"
        "<h2>Tools</h2>"
        "<p data-line>Search published pages, quote them, label tone and topic, then write.</p>"
        "<ul>"
        "<li>Search published news and official statements</li>"
        "<li>Quote the page, or write not found</li>"
        "<li>Label tone and topic from that quote</li>"
        "<li>Write a summary, a tone strip, and a table</li>"
        "</ul>"
        "<p class='note'>Social media is out. Inventing a row to reach 20 is out.</p>"
        f"<p class='note'>{html.escape(extra)}</p>"
        "</div>"
    )


def _plan_html() -> str:
    return (
        "<div class='panel' data-panel='plan'>"
        "<h2>Plan / reason</h2>"
        "<p data-line>Log every search. Label only from the quote. Write not found instead of inferring.</p>"
        "<p class='note'>If a live search is thin or fails, keep the checked-in sample. Do not pad the table.</p>"
        "</div>"
    )


def _action_html(search_log: list[dict[str, Any]], mode: str, backend: str) -> str:
    count = len(search_log)
    if count == 0:
        line = "No search was logged for this run."
    elif mode == "sample":
        line = f"{count} searches on the checked-in sample. No API key. No live call."
    else:
        line = f"{count} searches via {backend}."
    if search_log:
        body = f"<ol class='queries'>{_log_items(search_log)}</ol>"
    else:
        body = "<p class='note'>not found. This run did not log a search.</p>"
    return (
        "<section class='card panel' data-panel='action'>"
        "<p class='step-kicker'>Action</p>"
        "<h2>Search log</h2>"
        f"<p data-line>{html.escape(line)}</p>"
        "<p class='note'>Every query stays in the log, including empty passes and social-media exclusions.</p>"
        f"{body}"
        "</section>"
    )


def _log_items(search_log: list[dict[str, Any]]) -> str:
    items = []
    for entry in search_log:
        query = str(entry.get("query") or "not found")
        backend = str(entry.get("backend") or "not found")
        status = str(entry.get("status") or "not found")
        count = entry.get("result_count")
        count_label = "not found" if count is None else str(count)
        meta = f"{backend} · {count_label} hits · {status}"
        error = entry.get("error")
        if error:
            meta = f"{meta} · {error}"
        notes = entry.get("notes")
        notes_html = f"<span class='note'>{html.escape(str(notes))}</span>" if notes else ""
        css = " class='is-error'" if status == "error" else ""
        items.append(
            f"<li{css}><span class='q'>{html.escape(query)}</span>"
            f"<span class='meta'>{html.escape(meta)}</span>{notes_html}</li>"
        )
    return "".join(items)


def _observation_html(
    rows: list[dict[str, Any]],
    strip: list[dict[str, Any]],
    tones: Counter[str],
    undated: list[dict[str, Any]],
) -> str:
    if not rows:
        line = "Nothing usable came back. The table stays empty rather than filled with a guess."
    else:
        line = (
            f"{len(rows)} quoted articles: "
            f"{tones.get('positive', 0)} positive, "
            f"{tones.get('negative', 0)} negative, "
            f"{tones.get('neutral', 0)} neutral."
        )
    strip_html = _strip_html(strip) if strip else "<p class='note'>not found. No dated articles to plot.</p>"
    scroll_note = ""
    if len(strip) > 6:
        scroll_note = "<p class='note'>Scroll the strip sideways for later months.</p>"
    date_note = _undated_note(undated)
    filters = _filters_html(tones, len(rows)) if rows else ""
    return (
        "<section class='card panel' data-panel='observation'>"
        "<p class='step-kicker'>Observation</p>"
        f"<p data-line>{html.escape(line)}</p>"
        "<h2>Tone by month</h2>"
        f"{strip_html}{scroll_note}"
        "<h2>Quoted articles</h2>"
        "<p class='note'>Tone is how the piece receives the reform. The line under each label is the reason.</p>"
        f"{filters}"
        "<p id='filter-empty' class='note' hidden>No quoted article has this tone.</p>"
        f"{date_note}"
        f"{_table_html(rows)}"
        "</section>"
    )


def _undated_note(undated: list[dict[str, Any]]) -> str:
    if len(undated) == 1:
        outlet = str(undated[0].get("outlet") or "One row")
        text = f"{outlet} has no date: that page did not print one, so the cell stays not found."
        return f"<p class='note'>{html.escape(text)}</p>"
    if len(undated) > 1:
        return (
            f"<p class='note'>{len(undated)} dates stay not found because those pages did not print one.</p>"
        )
    return ""


def _filters_html(tones: Counter[str], total: int) -> str:
    buttons = [
        ("all", f"All {total}", True),
        ("positive", f"positive {tones.get('positive', 0)}", False),
        ("negative", f"negative {tones.get('negative', 0)}", False),
        ("neutral", f"neutral {tones.get('neutral', 0)}", False),
    ]
    parts = ["<div class='filters' role='group' aria-label='Filter by tone'>"]
    for tone, label, selected in buttons:
        pressed = "true" if selected else "false"
        css = " class='is-on'" if selected else ""
        parts.append(
            f"<button type='button' data-tone-filter='{tone}'{css} "
            f"aria-pressed='{pressed}'>{html.escape(label)}</button>"
        )
    parts.append("</div>")
    return "".join(parts)


def _strip_html(strip: list[dict[str, Any]]) -> str:
    max_count = 1
    for bucket in strip:
        max_count = max(
            max_count,
            int(bucket.get("positive", 0)),
            int(bucket.get("negative", 0)),
            int(bucket.get("neutral", 0)),
        )
    months = []
    for bucket in strip:
        wide = " wide" if len(str(bucket["month"])) > 7 else ""
        described = (
            f"{bucket['month']}: {int(bucket.get('positive', 0))} positive, "
            f"{int(bucket.get('negative', 0))} negative, {int(bucket.get('neutral', 0))} neutral"
        )
        bars = []
        for tone in ("positive", "negative", "neutral"):
            count = int(bucket.get(tone, 0))
            height = 2 if count == 0 else max(14, int(72 * (count / max_count)))
            tick = str(count) if count else ""
            bars.append(
                "<div class='col'>"
                f"<span class='tick {tone}'>{tick}</span>"
                f"<div class='bar {tone}' style='height:{height}px' title='{tone}: {count}'></div>"
                "</div>"
            )
        months.append(
            f"<div class='month{wide}' role='img' aria-label='{html.escape(described)}'>"
            f"<div class='bars'>{''.join(bars)}</div>"
            f"<label>{html.escape(str(bucket['month']))}</label>"
            "</div>"
        )
    legend = (
        "<p class='legend'>"
        "<span><span class='swatch positive'></span>positive</span>"
        "<span><span class='swatch negative'></span>negative</span>"
        "<span><span class='swatch neutral'></span>neutral</span>"
        "</p>"
    )
    return f"<div class='strip'>{''.join(months)}</div>{legend}"


def _table_html(rows: list[dict[str, Any]]) -> str:
    if not rows:
        body = (
            "<tr data-empty='1'><td colspan='6'>not found. "
            "No quoted article came back, and none was invented.</td></tr>"
        )
    else:
        body = "".join(_table_row(row) for row in rows)
    hint = ""
    if len(rows) > 8:
        hint = f"<p class='note'>Scroll inside the table for all {len(rows)} articles.</p>"
    return (
        f"{hint}"
        "<div class='table-scroll'>"
        "<table id='quotes'>"
        "<thead><tr>"
        "<th scope='col'>Outlet</th>"
        "<th scope='col'>Date</th>"
        "<th scope='col'>Link</th>"
        "<th scope='col'>Quote</th>"
        "<th scope='col'>Tone</th>"
        "<th scope='col'>Topic</th>"
        "</tr></thead>"
        f"<tbody>{body}</tbody>"
        "</table></div>"
    )


def _table_row(row: dict[str, Any]) -> str:
    url = str(row.get("url") or "not found")
    if url.startswith("http://") or url.startswith("https://"):
        link = f"<a href='{html.escape(url, quote=True)}'>source</a>"
    else:
        link = "not found"
    tone = str(row.get("tone") or "neutral")
    tone_class = tone if tone in {"positive", "negative", "neutral"} else "neutral"
    date_val = str(row.get("date") or "not found")
    date_html = html.escape(date_val)
    if date_val == "not found":
        date_html = f"<span class='missing'>{date_html}</span>"
    title = str(row.get("title") or "").strip()
    title_html = f"<span class='just'>{html.escape(title)}</span>" if title else ""
    return (
        f"<tr data-tone='{html.escape(tone_class, quote=True)}'>"
        f"<td>{html.escape(str(row.get('outlet') or 'not found'))}</td>"
        f"<td>{date_html}</td>"
        f"<td>{link}</td>"
        f"<td class='quote'>{html.escape(str(row.get('quote') or 'not found'))}{title_html}</td>"
        f"<td><span class='tone {tone_class}'>{html.escape(tone)}</span>"
        f"<span class='just'>{html.escape(str(row.get('tone_justification') or 'not found'))}</span></td>"
        f"<td>{html.escape(str(row.get('topic') or 'not found'))}"
        f"<span class='just'>{html.escape(str(row.get('topic_justification') or 'not found'))}</span></td>"
        "</tr>"
    )


def _memory_html(summary: str) -> str:
    paragraphs = "".join(
        f"<p class='lead'>{html.escape(part)}</p>" for part in _split_summary(summary)
    )
    return (
        "<section class='card panel summary' data-panel='memory'>"
        "<p class='step-kicker'>Memory</p>"
        "<h2>Two-line summary</h2>"
        "<p class='note' data-line>Kept from this run: the search log, the labels on each quote, and this summary.</p>"
        f"{paragraphs}"
        "</section>"
    )


def _stop_html(rows: list[dict[str, Any]]) -> str:
    count = len(rows)
    if count >= QUALITY_MIN_ARTICLES:
        line = (
            f"Stopped. {count} articles meet the target of at least {QUALITY_MIN_ARTICLES}. "
            "Each tone has a one-line reason, so the run does not search again."
        )
        extra = ""
    else:
        line = (
            f"Stopped. {count} articles is short of the target. "
            "The gap stays empty."
        )
        extra = (
            f"<p class='note'>Quality target is at least {QUALITY_MIN_ARTICLES} articles; "
            f"this run has {count}. Missing coverage is left empty rather than invented.</p>"
        )
    return (
        "<section class='card panel' data-panel='stop'>"
        "<p class='step-kicker'>Stop</p>"
        "<h2>Stop</h2>"
        f"<p data-line>{html.escape(line)}</p>"
        f"{extra}"
        "</section>"
    )


def _split_summary(summary: str) -> list[str]:
    parts = [part.strip() for part in summary.replace("  ", " ").split(". ") if part.strip()]
    if len(parts) <= 2:
        return [part if part.endswith(".") else part + "." for part in parts] or [summary]
    first = ". ".join(parts[: max(1, len(parts) // 2)]).rstrip(".") + "."
    second = ". ".join(parts[max(1, len(parts) // 2) :]).rstrip(".") + "."
    return [first, second]
