"""Parse the U.S. Census Bureau's Business Trends and Outlook Survey (BTOS) into tidy CSVs.

BTOS asks a representative sample of ~1.2M US employer businesses every two weeks
whether they used AI in the last two weeks. Since 2026 the questionnaire calls it
"Super Intelligence or SI (formerly referred to as Artificial Intelligence or AI)";
the question is otherwise the same.

Inputs  (download from https://www.census.gov/hfp/btos/data_downloads):
  data/raw/census/National.xlsx, data/raw/census/Sector.xlsx
Outputs:
  data/processed/ai_use_trend.csv, ai_use_by_sector.csv, ai_workforce_effects.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "census"
OUT = ROOT / "data" / "processed"
BASE = "https://www.census.gov/hfp/btos/downloads"

Q_USE, Q_USE_NEXT6M, Q_GENAI_STAFF, Q_HEADCOUNT, Q_HIRING = 7, 28, 8, 9, 10

NAICS = {
    "21": "Mining, oil & gas", "22": "Utilities", "23": "Construction", "31": "Manufacturing",
    "42": "Wholesale trade", "44": "Retail trade", "48": "Transportation & warehousing",
    "51": "Information (media, software, telecom)", "52": "Finance & insurance", "53": "Real estate",
    "54": "Professional, scientific & technical services", "56": "Admin & support services",
    "61": "Educational services", "62": "Health care & social assistance",
    "71": "Arts, entertainment & recreation", "72": "Accommodation & food services", "81": "Other services",
}


def download():
    RAW.mkdir(parents=True, exist_ok=True)
    for f in ("National", "Sector"):
        r = requests.get(f"{BASE}/{f}.xlsx", headers={"User-Agent": "Mozilla/5.0"}, timeout=120)
        r.raise_for_status()
        (RAW / f"{f}.xlsx").write_bytes(r.content)


def pct(v):
    return None if v in (".", "S", None) or pd.isna(v) else float(str(v).rstrip("%")) / 100


def period_cols(df):
    return [c for c in df.columns if str(c)[:2] == "20"]


def build():
    nat = pd.read_excel(RAW / "National.xlsx", sheet_name="Response Estimates")
    dates = pd.read_excel(RAW / "National.xlsx", sheet_name="Collection and Reference Dates")
    dates = dates.dropna(subset=["Smpdt"]).assign(Smpdt=lambda d: d.Smpdt.astype(int).astype(str))
    ref_end = dict(zip(dates.Smpdt, pd.to_datetime(dates["Ref End"]).dt.date.astype(str)))

    def row(df, qid, ans="Yes"):
        return df[(df["Question ID"] == qid) & (df["Answer"] == ans)].iloc[0]

    cols = period_cols(nat)
    use, nxt = row(nat, Q_USE), row(nat, Q_USE_NEXT6M)
    trend = pd.DataFrame({
        "period": cols,
        "reference_period_end": [ref_end.get(str(c)) for c in cols],
        "ai_use_share": [pct(use[c]) for c in cols],
        "expect_ai_next_6m_share": [pct(nxt[c]) for c in cols],
    }).dropna(subset=["ai_use_share"]).sort_values("period")
    trend.to_csv(OUT / "ai_use_trend.csv", index=False)

    latest = cols[0]
    effects = []
    for qid, label in [(Q_HEADCOUNT, "Effect of AI on headcount (last 6 months)"),
                       (Q_HIRING, "Effect of AI on new hiring (last 6 months)"),
                       (Q_GENAI_STAFF, "Employees used generative AI for work (last 2 weeks)")]:
        for _, r in nat[nat["Question ID"] == qid].iterrows():
            effects.append({"question": label, "answer": r["Answer"], "share": pct(r[latest]), "period": latest})
    pd.DataFrame(effects).to_csv(OUT / "ai_workforce_effects.csv", index=False)

    sec = pd.read_excel(RAW / "Sector.xlsx", sheet_name="Response Estimates")
    s_latest = period_cols(sec)[0]
    s = sec[(sec["Question ID"] == Q_USE) & (sec["Answer"] == "Yes")]
    by_sector = pd.DataFrame({
        "naics": s.Sector.astype(str), "sector": s.Sector.astype(str).map(NAICS),
        "ai_use_share": s[s_latest].map(pct), "period": s_latest,
    }).dropna().sort_values("ai_use_share", ascending=False)
    by_sector.to_csv(OUT / "ai_use_by_sector.csv", index=False)
    return trend, by_sector, pd.DataFrame(effects), ref_end.get(str(latest))


if __name__ == "__main__":
    if "--refresh" in sys.argv:
        download()
    OUT.mkdir(parents=True, exist_ok=True)
    t, s, e, ref = build()
    print("latest reference period ends", ref)
    print(t.tail(3).to_string(index=False)); print(s.to_string(index=False)); print(e.to_string(index=False))
