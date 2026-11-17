"""Combine the curated Ignite announcements with the Census tables into the briefing page.

Inputs:  src/announcements.json, data/processed/*.csv
Output:  outputs/briefing.html
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"


def main():
    trend = pd.read_csv(P / "ai_use_trend.csv")
    sector = pd.read_csv(P / "ai_use_by_sector.csv")
    eff = pd.read_csv(P / "ai_workforce_effects.csv")
    data = {
        "ignite": json.loads((ROOT / "src" / "announcements.json").read_text()),
        "trend": [{"d": d, "a": round(a, 3), "b": round(b, 3)} for d, a, b in
                  zip(trend.reference_period_end, trend.ai_use_share, trend.expect_ai_next_6m_share)],
        "sector": [{"s": s, "a": round(a, 3)} for s, a in zip(sector.sector, sector.ai_use_share)],
        "effects": eff.to_dict(orient="records"),
    }
    tpl = (ROOT / "src" / "page_template.html").read_text()
    (ROOT / "outputs").mkdir(exist_ok=True)
    out = ROOT / "outputs" / "briefing.html"
    out.write_text(tpl.replace("/*__DATA__*/null", json.dumps(data)))
    print("wrote", out)


if __name__ == "__main__":
    main()
