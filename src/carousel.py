"""Render a LinkedIn document carousel (PDF, 1080x1350 per page) plus PNGs of each slide.

Inputs:  src/announcements.json, data/processed/*.csv
Outputs: outputs/linkedin_carousel.pdf, outputs/slides/slide_XX.png
"""
import json
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
OUT = ROOT / "outputs"

BG, INK, INK2, MUTED, RULE = "#f5f6f8", "#101418", "#4b5260", "#7c8391", "#dfe3e9"
BLUE, BLUE_INK, WASH, ORANGE, MUTE_BAR = "#2a78d6", "#1c5cab", "#e8f1fc", "#eb6834", "#c4cedb"
W, H = 10.8, 13.5  # inches at 100 dpi -> 1080x1350

plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK})


def page(n, total):
    fig = plt.figure(figsize=(W, H), dpi=100, facecolor=BG)
    fig.text(0.07, 0.955, "MICROSOFT IGNITE 2026  ·  BUSINESS BRIEFING", fontsize=13, color=BLUE_INK, fontweight="bold")
    fig.text(0.93, 0.955, f"{n}/{total}", fontsize=13, color=MUTED, ha="right")
    fig.add_artist(plt.Line2D([0.07, 0.93], [0.94, 0.94], color=INK, lw=2))
    return fig


def wrap(t, w):
    return "\n".join(textwrap.wrap(t, w))


def cover(fig, s):
    fig.text(0.07, 0.80, "Microsoft wants to\ngive your business\nan AI workforce.", fontsize=54, fontweight="bold", va="top", linespacing=1.15)
    fig.text(0.07, 0.47, f"Only {s:.0%} of US firms use AI today.".replace("%", "%"), fontsize=34, color=BLUE_INK, fontweight="bold")
    fig.text(0.07, 0.40, "5 shifts from Ignite Day 1 that business leaders\nshould plan for, and what to do on Monday.", fontsize=22, color=INK2, va="top", linespacing=1.4)
    fig.text(0.07, 0.08, "Data: Microsoft Ignite 2026 Book of News · U.S. Census Bureau BTOS (Oct 2026)", fontsize=13, color=MUTED)
    fig.text(0.93, 0.08, "Swipe  →", fontsize=18, color=INK, ha="right", fontweight="bold")


def shift_slide(fig, i, sh):
    fig.text(0.07, 0.88, f"0{i}", fontsize=26, color=BLUE_INK, fontweight="bold", va="top")
    fig.text(0.07, 0.83, wrap(sh["title"], 26), fontsize=42, fontweight="bold", va="top", linespacing=1.15)
    y = 0.64
    fig.text(0.07, y, "ANNOUNCED", fontsize=13, color=MUTED, fontweight="bold")
    y -= 0.045
    for name, status, _ in sh["announced"][:3]:
        fig.text(0.07, y, wrap(name, 40), fontsize=20, color=INK, va="top", fontweight="bold")
        lines = len(textwrap.wrap(name, 40))
        fig.text(0.93, y, status.upper(), fontsize=12, color=INK2, va="top", ha="right",
                 bbox=dict(boxstyle="round,pad=0.35", fc="none", ec=INK2, lw=1))
        y -= 0.04 * lines + 0.012
    ax = fig.add_axes([0.05, 0.07, 0.90, 0.25]); ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, color=WASH, transform=ax.transAxes))
    fig.text(0.09, 0.295, "DO ON MONDAY", fontsize=13, color=BLUE_INK, fontweight="bold")
    fig.text(0.09, 0.265, wrap(sh["monday"], 46), fontsize=21, color=INK, va="top", linespacing=1.45)


def trend_slide(fig, trend, sector):
    fig.text(0.07, 0.88, "Reality check", fontsize=26, color=BLUE_INK, fontweight="bold", va="top")
    fig.text(0.07, 0.83, "AI use is rising, but it's\nstill a minority of firms", fontsize=40, fontweight="bold", va="top", linespacing=1.15)
    ax = fig.add_axes([0.10, 0.42, 0.72, 0.26], facecolor=BG)
    x = range(len(trend))
    ax.plot(x, trend.ai_use_share * 100, color=BLUE, lw=3)
    ax.scatter([len(trend) - 1], [trend.ai_use_share.iloc[-1] * 100], color=BLUE, s=80, zorder=3)
    ax.annotate(f"{trend.ai_use_share.iloc[-1]:.0%}", (len(trend) - 1, trend.ai_use_share.iloc[-1] * 100),
                xytext=(12, -6), textcoords="offset points", fontsize=22, fontweight="bold")
    ax.annotate(f"{trend.ai_use_share.iloc[0]:.0%}", (0, trend.ai_use_share.iloc[0] * 100),
                xytext=(0, -30), textcoords="offset points", fontsize=18, color=INK2)
    ax.set_ylim(0, 30); ax.set_xticks([0, len(trend) - 1]); ax.set_xticklabels(["Nov 2025", "Oct 2026"], fontsize=14, color=INK2)
    ax.set_yticks([10, 20, 30]); ax.set_yticklabels(["10%", "20%", "30%"], fontsize=13, color=MUTED)
    for s in ax.spines.values(): s.set_visible(False)
    ax.grid(axis="y", color=RULE); ax.set_axisbelow(True); ax.tick_params(length=0)
    fig.text(0.07, 0.72, "Share of US businesses that used AI in the last two weeks", fontsize=15, color=INK2)
    hi, lo = sector.iloc[0], sector.iloc[-1]
    fig.text(0.07, 0.31, "Biggest gap is by industry", fontsize=20, fontweight="bold")
    fig.text(0.07, 0.27, f"{hi.ai_use_share:.0%}", fontsize=44, fontweight="bold", color=BLUE_INK, va="top")
    fig.text(0.07, 0.19, wrap(hi.sector, 24), fontsize=16, color=INK2, va="top")
    fig.text(0.52, 0.27, f"{lo.ai_use_share:.0%}", fontsize=44, fontweight="bold", color=INK2, va="top")
    fig.text(0.52, 0.19, wrap(lo.sector, 24), fontsize=16, color=INK2, va="top")
    fig.text(0.07, 0.06, "Source: U.S. Census Bureau, Business Trends and Outlook Survey, two weeks to 18 Oct 2026", fontsize=12, color=MUTED)


def jobs_slide(fig, eff):
    g = lambda q, a: eff[(eff.question.str.startswith(q)) & (eff.answer == a)].share.iloc[0]
    fig.text(0.07, 0.88, "Reality check", fontsize=26, color=BLUE_INK, fontweight="bold", va="top")
    fig.text(0.07, 0.83, "AI hasn't cut jobs\nat most firms (yet)", fontsize=40, fontweight="bold", va="top", linespacing=1.15)
    fig.text(0.07, 0.68, "Effect of AI over the last six months, as reported by US businesses", fontsize=15, color=INK2)
    rows = [("Headcount increased", g("Effect of AI on headcount", "Increased"), BLUE),
            ("Headcount decreased", g("Effect of AI on headcount", "Decreased"), ORANGE),
            ("Hiring increased", g("Effect of AI on new hiring", "Increased"), BLUE),
            ("Hiring decreased", g("Effect of AI on new hiring", "Decreased"), ORANGE)]
    ax = fig.add_axes([0.40, 0.36, 0.48, 0.28], facecolor=BG)
    for i, (lab, v, c) in enumerate(rows):
        ax.barh(i, v * 100, color=c, height=0.55)
        ax.text(v * 100 + 0.15, i, f"{v:.1%}", va="center", fontsize=20, fontweight="bold")
        fig.text(0.38, 0.36 + 0.28 * (1 - (i + 0.5) / 4), lab, fontsize=18, color=INK, ha="right", va="center")
    ax.set_ylim(3.6, -0.6); ax.set_xlim(0, 9); ax.axis("off")
    nc = g("Effect of AI on headcount", "No change")
    fig.text(0.07, 0.27, f"{nc:.0%} say AI made no difference\nto their headcount.", fontsize=28, fontweight="bold", va="top", linespacing=1.3)
    fig.text(0.07, 0.15, "The agent era is still in the planning stage for most firms.\nThe companies that plan for it now set the pace.", fontsize=18, color=INK2, va="top", linespacing=1.45)
    fig.text(0.07, 0.06, "Source: U.S. Census Bureau, Business Trends and Outlook Survey, two weeks to 18 Oct 2026", fontsize=12, color=MUTED)


def cta(fig):
    fig.text(0.07, 0.80, "Which shift matters\nmost for your team?", fontsize=50, fontweight="bold", va="top", linespacing=1.15)
    items = ["01  Agents get a line manager", "02  Copilot becomes the front door", "03  Pay for usage, not just seats",
             "04  Works beyond Microsoft tools", "05  Govern agents, not just people"]
    for i, t in enumerate(items):
        fig.text(0.07, 0.56 - i * 0.06, t, fontsize=24, color=INK)
    fig.text(0.07, 0.17, "Full briefing, charts and open data: link in the comments.", fontsize=20, color=BLUE_INK, fontweight="bold")
    fig.text(0.07, 0.06, "Sources: Microsoft Ignite 2026 Book of News · U.S. Census Bureau BTOS", fontsize=12, color=MUTED)


def main():
    ign = json.loads((ROOT / "src" / "announcements.json").read_text())
    trend = pd.read_csv(P / "ai_use_trend.csv")
    sector = pd.read_csv(P / "ai_use_by_sector.csv")
    eff = pd.read_csv(P / "ai_workforce_effects.csv")
    (OUT / "slides").mkdir(parents=True, exist_ok=True)
    builders = [lambda f: cover(f, trend.ai_use_share.iloc[-1])]
    builders += [(lambda f, i=i, s=s: shift_slide(f, i, s)) for i, s in enumerate(ign["shifts"], 1)]
    builders += [lambda f: trend_slide(f, trend, sector), lambda f: jobs_slide(f, eff), cta]
    with PdfPages(OUT / "linkedin_carousel.pdf") as pdf:
        for n, b in enumerate(builders, 1):
            fig = page(n, len(builders)); b(fig)
            pdf.savefig(fig, facecolor=BG); fig.savefig(OUT / "slides" / f"slide_{n:02d}.png", facecolor=BG)
            plt.close(fig)
    print("wrote", len(builders), "slides")


if __name__ == "__main__":
    main()
