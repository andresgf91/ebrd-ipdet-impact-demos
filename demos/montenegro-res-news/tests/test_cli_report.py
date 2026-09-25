from pathlib import Path

from montenegro_res_news.cli import main
from montenegro_res_news.report import CSS, write_outputs


def test_sample_cli(tmp_path, capsys):
    code = main(["--sample", "--outdir", str(tmp_path)])
    assert code == 0
    assert (tmp_path / "report.html").is_file()
    assert (tmp_path / "table.csv").is_file()
    assert (tmp_path / "search_log.json").is_file()
    html = (tmp_path / "report.html").read_text(encoding="utf-8")
    assert "Montenegro RES Law" in html
    assert "#0b0" not in html.lower()
    out = capsys.readouterr().out
    assert "mode=sample" in out


def test_html_is_workshop_not_cyberpunk():
    assert "var(--paper): #f7f5f1" in CSS.replace(" ", "") or "#f7f5f1" in CSS
    assert "neon" not in CSS.lower()
    assert "#00ff" not in CSS.lower()
    assert "Georgia" in CSS


def test_write_outputs_tone_strip(tmp_path: Path):
    rows = [
        {
            "outlet": "A",
            "date": "2025-07-01",
            "url": "https://example.com/a",
            "quote": "q",
            "tone": "positive",
            "tone_justification": "because",
            "topic": "investor interest",
            "topic_justification": "because",
            "title": "t",
        }
    ]
    paths = write_outputs(rows, [], tmp_path, mode="live", backend="test")
    html = paths["html"].read_text(encoding="utf-8")
    assert "Tone by month" in html
    assert "2025-07" in html
