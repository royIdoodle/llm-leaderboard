from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
import requests
from lxml import html

TERMINAL_BENCH_URL = "https://www.tbench.ai/leaderboard"
TERMINAL_BENCH_TABLE_XPATH = '//*[@id="nd-home-layout"]/div/div/div/div[1]/table'


def _parse_accuracy(cell_text: str) -> tuple[Optional[float], Optional[float]]:
    if not cell_text:
        return None, None
    text = cell_text.strip().replace("\u00b1", "±")
    try:
        # formats like: 60.3%± 1.1  or  50.5%± 0.5
        if "%" in text:
            value_part = text.split("%", 1)[0]
            value = float(value_part)
        else:
            value = float(text)
        err = None
        if "±" in text:
            err_part = text.split("±", 1)[1].strip()
            # remove any trailing text like %
            err_part = err_part.replace("%", "").strip()
            if err_part:
                err = float(err_part)
        return value, err
    except Exception:
        return None, None


def fetch_terminal_bench() -> List[Dict[str, Any]]:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
    }
    resp = requests.get(TERMINAL_BENCH_URL, headers=headers, timeout=30)
    resp.raise_for_status()

    doc = html.fromstring(resp.text)
    tables = doc.xpath(TERMINAL_BENCH_TABLE_XPATH)
    if not tables:
        return []
    table = tables[0]

    rows = table.xpath(".//tr")
    if not rows:
        return []

    # Identify columns from header
    header_cells = [" ".join("".join(c.itertext()).split()) for c in rows[0].xpath(".//th|.//td")]
    # Expected headers (example): Rank | Agent | Model | Date | Agent Org | Model Org | Accuracy
    results: List[Dict[str, Any]] = []

    for tr in rows[1:]:
        cells = tr.xpath(".//td")
        if not cells or len(cells) < 6:
            continue
        texts = [" ".join("".join(c.itertext()).split()) for c in cells]

        # Safe extraction by index based on known columns
        rank = None
        try:
            rank = int(texts[0]) if texts[0] else None
        except Exception:
            rank = None

        agent = texts[1] if len(texts) > 1 else None
        model = texts[2] if len(texts) > 2 else None
        date = texts[3] if len(texts) > 3 else None
        agent_org = texts[4] if len(texts) > 4 else None
        model_org = texts[5] if len(texts) > 5 else None

        score = None
        score_error = None
        if len(texts) > 6:
            score, score_error = _parse_accuracy(texts[6])
        elif "Accuracy" in " ".join(header_cells):
            # Try to find index dynamically
            try:
                idx = header_cells.index("Accuracy")
                if idx < len(texts):
                    score, score_error = _parse_accuracy(texts[idx])
            except Exception:
                pass

        org = agent_org or model_org

        results.append({
            "bench": "terminal-bench",
            "rank": rank,
            "agent": agent,
            "model": model,
            "date": date,
            "agent_org": agent_org,
            "model_org": model_org,
            "org": org,
            "score": score,
            "score_error": score_error,
            "raw": {"row": texts},
        })

    return results
