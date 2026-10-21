"""Builds the results-slide figures (inline SVG) from the Paper 1 model outputs.

Reads the CSVs written by the analysis repo (r/outputs/results) and replaces the
figure blocks marked <!-- fig:NAME --> ... <!-- /fig:NAME --> in index.html.

Usage: python3 scripts/make_results_figures.py [r/outputs/results] [r2/outputs/results]
"""
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
INDEX = HERE.parent / "index.html"

NAVY = "#2a4e6e"
RED = "#a6192e"
MAGENTA = "#80225f"
GREY = "#b9b4a6"
INK = "#373a36"
LINE = "#c9c6bd"


def rows(path, **match):
    with open(path, newline="") as f:
        return [r for r in csv.DictReader(f) if all(r.get(k) == v for k, v in match.items())]


def fmt(v, nd=2):
    s = f"{v:.{nd}f}"
    return s.replace("-", "−")


def coef_panel(items, x0, width, lo, hi, ticks, top, row_h, title=None, offsets=(0,)):
    """items: list of rows; each row is a list of (est, low, high, sig, colour) per series."""
    sx = lambda v: x0 + (v - lo) / (hi - lo) * width
    out = []
    bottom = top + row_h * len(items)
    if title:
        out.append(f'<text class="fig-panel" x="{x0 + width / 2:.0f}" y="{top - 22:.0f}">{title}</text>')
    out.append(f'<line class="fig-zero" x1="{sx(0):.1f}" y1="{top - 6}" x2="{sx(0):.1f}" y2="{bottom}" />')
    out.append(f'<line class="fig-axis" x1="{x0}" y1="{bottom}" x2="{x0 + width}" y2="{bottom}" />')
    for t in ticks:
        out.append(f'<line class="fig-axis" x1="{sx(t):.1f}" y1="{bottom}" x2="{sx(t):.1f}" y2="{bottom + 7}" />')
        out.append(f'<text class="fig-tick" x="{sx(t):.1f}" y="{bottom + 30}">{fmt(t, 1)}</text>')
    for i, series in enumerate(items):
        yc = top + row_h * i + row_h / 2
        for (est, low, high, sig, col), dy in zip(series, offsets):
            y = yc + dy
            out.append(f'<line x1="{sx(low):.1f}" y1="{y:.1f}" x2="{sx(high):.1f}" y2="{y:.1f}" stroke="{col}" stroke-width="3" />')
            for xv in (low, high):
                out.append(f'<line x1="{sx(xv):.1f}" y1="{y - 7:.1f}" x2="{sx(xv):.1f}" y2="{y + 7:.1f}" stroke="{col}" stroke-width="3" />')
            fill = col if sig else "#ffffff"
            out.append(f'<circle cx="{sx(est):.1f}" cy="{y:.1f}" r="9" fill="{fill}" stroke="{col}" stroke-width="3" />')
    return out, bottom


def row_labels(labels, x, top, row_h):
    return [f'<text class="fig-row" x="{x}" y="{top + row_h * i + row_h / 2 + 8:.0f}">{t}</text>' for i, t in enumerate(labels)]


def svg(w, h, parts, label):
    return (f'<svg class="fig" viewBox="0 0 {w} {h}" role="img" aria-label="{label}">' + "".join(parts) + "</svg>")


def fig_overall(res):
    data = {r["outcome_key"]: r for r in rows(res / "03_midpoint_comparison.csv")}
    lo, hi, x0, width = 1, 7, 190, 1000
    sx = lambda v: x0 + (v - lo) / (hi - lo) * width
    parts, top, row_h = [], 20, 90
    labels = [("att", "Attitudes"), ("intent", "Intentions")]
    bottom = top + row_h * 2
    parts.append(f'<line class="fig-zero" x1="{sx(4):.1f}" y1="{top - 6}" x2="{sx(4):.1f}" y2="{bottom}" />')
    parts.append(f'<line class="fig-axis" x1="{x0}" y1="{bottom}" x2="{x0 + width}" y2="{bottom}" />')
    for t in range(1, 8):
        parts.append(f'<line class="fig-axis" x1="{sx(t):.1f}" y1="{bottom}" x2="{sx(t):.1f}" y2="{bottom + 7}" />')
        parts.append(f'<text class="fig-tick" x="{sx(t):.1f}" y="{bottom + 30}">{t}</text>')
    parts.append(f'<text class="fig-axis-title" x="{x0 + width / 2}" y="{bottom + 66}">Mean rating (1 = strongly disagree, 7 = strongly agree)</text>')
    parts.append(f'<text class="fig-note" x="{sx(4) + 10:.1f}" y="{top + 6}">Scale midpoint</text>')
    for i, (key, name) in enumerate(labels):
        r = data[key]
        m, l, h = float(r["mean"]), float(r["ci95_low"]), float(r["ci95_high"])
        y = top + row_h * i + row_h / 2
        parts.append(f'<text class="fig-row" x="0" y="{y + 8:.0f}">{name}</text>')
        parts.append(f'<line x1="{sx(l):.1f}" y1="{y}" x2="{sx(h):.1f}" y2="{y}" stroke="{NAVY}" stroke-width="3" />')
        for xv in (l, h):
            parts.append(f'<line x1="{sx(xv):.1f}" y1="{y - 8}" x2="{sx(xv):.1f}" y2="{y + 8}" stroke="{NAVY}" stroke-width="3" />')
        parts.append(f'<circle cx="{sx(m):.1f}" cy="{y}" r="10" fill="{NAVY}" />')
        parts.append(f'<text class="fig-val" x="{sx(h) + 18:.1f}" y="{y + 7}">{fmt(m)}</text>')
    stats = " &#183; ".join(
        f'{name}: <i>M</i> = {fmt(float(data[k]["mean"]))}, 95% CI [{fmt(float(data[k]["ci95_low"]))}, {fmt(float(data[k]["ci95_high"]))}], <i>d</i> = {fmt(float(data[k]["d"]))}'
        for k, name in labels)
    return svg(1220, bottom + 80, parts, "Mean attitudes and intentions with 95% confidence intervals, both above the scale midpoint of 4"), stats


def fig_tool(res):
    order = [("pu", "Perceived usefulness"), ("peou", "Perceived ease of use"), ("trust", "Trust"),
             ("privacy", "Privacy concerns"), ("oversight", "Human oversight preferences"), ("environ", "Environmental concerns")]
    eff = {r["outcome_key"]: r for r in rows(res / "04_model_a_effects.csv", effect="Tool type (overall)")}
    items = []
    for k, _ in order:
        r = eff[k]
        items.append([(float(r["estimate"]), float(r["ci95_low"]), float(r["ci95_high"]), float(r["p_fdr"]) < .05, NAVY)])
    top, row_h, x0 = 20, 62, 330
    parts = row_labels([t for _, t in order], 0, top, row_h)
    p, bottom = coef_panel(items, x0, 440, -0.2, 0.6, [-0.2, 0, 0.2, 0.4, 0.6], top, row_h)
    parts += p
    parts.append(f'<text class="fig-axis-title" x="{x0 + 220}" y="{bottom + 66}">Difference (bespoke − general-purpose), <tspan font-style="italic">b</tspan></text>')
    return svg(800, bottom + 80, parts, "Coefficient plot of bespoke minus general-purpose differences with 95% confidence intervals")


def fig_comfort(res):
    cats = ["1 Much less comfortable", "2 Slightly less comfortable", "3 About the same", "4 Slightly more comfortable", "5 Much more comfortable"]
    cols = [NAVY, "#7f98ad", GREY, "#b07a9d", MAGENTA]
    data = {}
    for r in rows(res / "07_comfort_distribution.csv"):
        data.setdefault(r["respondent_type"], {})[r["response"]] = float(r["percent"])
    parts, x0, width, top, bar_h, gap = [], 170, 480, 20, 54, 34
    for i, (key, name) in enumerate([("Adult", "Adults"), ("Parent", "Parents/carers")]):
        y = top + i * (bar_h + gap)
        parts.append(f'<text class="fig-row" x="0" y="{y + bar_h / 2 + 8:.0f}">{name}</text>')
        x = x0
        for c, col in zip(cats, cols):
            w = data[key][c] / 100 * width
            parts.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{bar_h}" fill="{col}" />')
            if data[key][c] >= 8:
                parts.append(f'<text class="fig-bar-val" x="{x + w / 2:.1f}" y="{y + bar_h / 2 + 7:.0f}">{data[key][c]:.0f}%</text>')
            x += w
    ky = top + 2 * (bar_h + gap) + 6
    keys = ["Much less", "Slightly less", "Same", "Slightly more", "Much more"]
    kx_pos = [x0, x0 + 96, x0 + 210, x0 + 282, x0 + 400]
    for j, (k, col) in enumerate(zip(keys, cols)):
        kx = kx_pos[j]
        parts.append(f'<rect x="{kx}" y="{ky}" width="16" height="16" fill="{col}" />')
        parts.append(f'<text class="fig-key" x="{kx + 22}" y="{ky + 14}">{k}</text>')
    parts.append(f'<text class="fig-axis-title" x="{x0 + width / 2}" y="{ky + 56}">Comfort using bespoke vs general-purpose tools</text>')
    return svg(680, ky + 70, parts, "Stacked bars of comfort with bespoke versus general-purpose tools for adults and parents")


def two_panel(res_rows, order, terms, lo, hi, ticks, label_w, panel_w, label, sig_key="p", offsets=(-9, 9), series=None, row_h_override=None):
    top, row_h, gap = 56, row_h_override or 58, 50
    parts = row_labels([t for t in order], 0, top, row_h)
    bottom = top
    for j, (outcome, title) in enumerate([("att", "Attitudes"), ("intent", "Intentions")]):
        by = {r["term"]: r for r in res_rows if r["outcome_key"] == outcome}
        items = []
        for t in terms:
            row = []
            for suffix, col in series:
                r = by[t + suffix]
                row.append((float(r["estimate"]), float(r["ci95_low"]), float(r["ci95_high"]), float(r[sig_key]) < .05, col))
            items.append(row)
        p, bottom = coef_panel(items, label_w + j * (panel_w + gap), panel_w, lo, hi, ticks, top, row_h, title=title,
                               offsets=offsets if len(series) > 1 else (0,))
        parts += p
    width = label_w + 2 * panel_w + gap
    parts.append(f'<text class="fig-axis-title" x="{label_w + panel_w + gap / 2}" y="{bottom + 66}">Unstandardised coefficient, <tspan font-style="italic">b</tspan></text>')
    return svg(width + 40, bottom + 80, parts, label)


def fig_predictors(res):
    order = ["Perceived usefulness", "Perceived ease of use", "Trust", "Privacy concerns", "Human oversight preferences", "Environmental concerns"]
    terms = ["pu", "peou", "trust", "privacy", "oversight", "environ"]
    data = rows(res / "05_model_b_coefficients.csv", step="S3")
    return two_panel(data, order, terms, -0.5, 1.0, [-0.5, 0, 0.5, 1.0], 330, 380,
                     "Between- and within-person coefficients predicting attitudes and intentions, with 95% confidence intervals",
                     series=[("_btw", NAVY), ("_wth", RED)])


def fig_characteristics(res):
    order = ["Bespoke AI (vs general-purpose)", "Parent/carer (vs adult)", "Age", "Female (vs male)", "Education",
             "GenAI use frequency", "Digital technology confidence", "Used GenAI for mental health"]
    terms = ["ai_typeBespoke AI", "respondent_typeParent", "age_c", "gender_adjFemale", "education_c",
             "genai_freq_c", "tech_conf_c", "ai_mh_useYes"]
    data = rows(res / "06_model_c_coefficients.csv", step="C1")
    out = two_panel(data, order, terms, -0.75, 1.75, [-0.5, 0, 0.5, 1.0, 1.5], 360, 370,
                    "Coefficients for participant characteristics predicting attitudes and intentions, with 95% confidence intervals",
                    sig_key="p_fdr", series=[("", NAVY)], row_h_override=48)
    # Group bubbles (revealed as fragments): rows 1-4 demographics, rows 5-7 prior experience.
    top, row_h, right = 56, 48, 1150
    bubbles = []
    for cls, label, first, last in [("grp-demo", "Demographics", 1, 4), ("grp-exp", "Prior experience", 5, 7)]:
        y0, y1 = top + row_h * first + 4, top + row_h * (last + 1) - 9
        bubbles.append(
            f'<g class="grp-bubble {cls} fragment">'
            f'<rect x="-10" y="{y0}" width="{right + 20}" height="{y1 - y0}" rx="22" />'
            f'<text class="grp-label" x="{right + 26}" y="{(y0 + y1) / 2 + 7:.0f}">{label}</text></g>')
    head, rest = out.split(">", 1)
    head = head.replace('viewBox="0 0 1190 ', 'viewBox="-14 0 1394 ')
    return head + ">" + "".join(bubbles) + rest


def fig_students(res, res2):
    """Community vs student means with 95% CIs. A second build (class "st-open" on the figure
    wrapper) slides the x axis down and reveals the student breakdown by prior use."""
    p1 = {r["outcome_key"]: r for r in rows(res / "03_midpoint_comparison.csv")}
    p2 = rows(res2 / "03_descriptive_baselines.csv")
    def p2row(key, comp):
        return next(r for r in p2 if r["outcome_key"] == key and r["comparison"].startswith(comp))
    groups = [
        ("Community sample", lambda k: p1[k], GREY, ""),
        ("Students", lambda k: p2row(k, "Overall"), MAGENTA, ""),
        ("No prior use", lambda k: p2row(k, "Prior GenAI use for own mental health: No"), MAGENTA, "st-extra"),
        ("Prior use", lambda k: p2row(k, "Prior GenAI use for own mental health: Yes"), MAGENTA, "st-extra"),
    ]
    top, row_h, label_w, panel_w, gap = 56, 62, 300, 440, 60
    lo, hi = 1, 7
    bottom = top + row_h * len(groups)
    shift = row_h * 2  # distance the axis travels when the breakdown opens
    base, extra, axis, mids = [], [], [], []
    for i, (name, _, _, cls) in enumerate(groups):
        indent = 36 if cls else 0
        (extra if cls else base).append(f'<text class="fig-row" x="{indent}" y="{top + row_h * i + row_h / 2 + 8:.0f}">{name}</text>')
    for j, (key, title) in enumerate([("att", "Attitudes"), ("intent", "Intentions")]):
        x0 = label_w + j * (panel_w + gap)
        sx = lambda v, x0=x0: x0 + (v - lo) / (hi - lo) * panel_w
        base.append(f'<text class="fig-panel" x="{x0 + panel_w / 2:.0f}" y="{top - 22}">{title}</text>')
        mids.append(f'<line class="fig-zero st-mid" x1="{sx(4):.1f}" y1="{top - 6}" x2="{sx(4):.1f}" y2="{bottom}" />')
        axis.append(f'<line class="fig-axis" x1="{x0}" y1="{bottom}" x2="{x0 + panel_w}" y2="{bottom}" />')
        for t in range(1, 8):
            axis.append(f'<line class="fig-axis" x1="{sx(t):.1f}" y1="{bottom}" x2="{sx(t):.1f}" y2="{bottom + 7}" />')
            axis.append(f'<text class="fig-tick" x="{sx(t):.1f}" y="{bottom + 30}">{t}</text>')
        for i, (_, get, col, cls) in enumerate(groups):
            r = get(key)
            m = float(r.get("mean") or r["estimate"])
            l, h = float(r["ci95_low"]), float(r["ci95_high"])
            y = top + row_h * i + row_h / 2
            out = extra if cls else base
            out.append(f'<line x1="{sx(l):.1f}" y1="{y}" x2="{sx(h):.1f}" y2="{y}" stroke="{col}" stroke-width="3" />')
            for xv in (l, h):
                out.append(f'<line x1="{sx(xv):.1f}" y1="{y - 7}" x2="{sx(xv):.1f}" y2="{y + 7}" stroke="{col}" stroke-width="3" />')
            out.append(f'<circle cx="{sx(m):.1f}" cy="{y}" r="9" fill="{col}" />')
            if m < 4:
                out.append(f'<text class="fig-val-small" x="{sx(l) - 12:.1f}" y="{y + 6}" text-anchor="end">{fmt(m)}</text>')
            else:
                out.append(f'<text class="fig-val-small" x="{sx(h) + 12:.1f}" y="{y + 6}">{fmt(m)}</text>')
    axis.append(f'<text class="fig-axis-title" x="{label_w + panel_w + gap / 2}" y="{bottom + 66}">Mean rating (1&#8211;7), dashed line = scale midpoint</text>')
    collapsed = (bottom - shift - (top - 6)) / (bottom - (top - 6))
    parts = (base
             + [f'<g class="st-mids" style="--st-collapsed: {collapsed:.4f}">' + "".join(mids) + "</g>"]
             + [f'<g class="st-axis" style="--st-shift: {shift}px">' + "".join(axis) + "</g>"]
             + ['<g class="st-extra">' + "".join(extra) + "</g>"])
    return svg(label_w + 2 * panel_w + gap + 60, bottom + 80, parts,
               "Mean attitudes and intentions with 95% confidence intervals for the community and student samples, then for students by prior AI use")


def fig_overall_portrait(res):
    """Vertical dot-and-CI plot of overall attitudes and intentions on the 1-7 scale."""
    data = {r["outcome_key"]: r for r in rows(res / "03_midpoint_comparison.csv")}
    x_axis, top, height = 80, 30, 440
    sy = lambda v: top + (7 - v) / 6 * height
    bottom = top + height
    parts = [f'<line class="fig-axis" x1="{x_axis}" y1="{top}" x2="{x_axis}" y2="{bottom}" />']
    for t in range(1, 8):
        parts.append(f'<line class="fig-axis" x1="{x_axis - 7}" y1="{sy(t):.1f}" x2="{x_axis}" y2="{sy(t):.1f}" />')
        parts.append(f'<text class="fig-tick" x="{x_axis - 18}" y="{sy(t) + 7:.1f}" text-anchor="end">{t}</text>')
    parts.append(f'<line class="fig-zero" x1="{x_axis}" y1="{sy(4):.1f}" x2="440" y2="{sy(4):.1f}" />')
    parts.append(f'<text class="fig-note" x="438" y="{sy(4) + 24:.1f}" text-anchor="end">Scale midpoint</text>')
    parts.append(f'<line class="fig-axis" x1="{x_axis}" y1="{bottom}" x2="440" y2="{bottom}" />')
    for x, (key, name) in zip((190, 330), [("att", "Attitudes"), ("intent", "Intentions")]):
        r = data[key]
        m, l, h = float(r["mean"]), float(r["ci95_low"]), float(r["ci95_high"])
        parts.append(f'<line x1="{x}" y1="{sy(h):.1f}" x2="{x}" y2="{sy(l):.1f}" stroke="{NAVY}" stroke-width="3" />')
        for yv in (l, h):
            parts.append(f'<line x1="{x - 9}" y1="{sy(yv):.1f}" x2="{x + 9}" y2="{sy(yv):.1f}" stroke="{NAVY}" stroke-width="3" />')
        parts.append(f'<circle cx="{x}" cy="{sy(m):.1f}" r="11" fill="{NAVY}" />')
        parts.append(f'<text class="fig-val" x="{x}" y="{sy(h) - 16:.1f}" text-anchor="middle">{fmt(m)}</text>')
        parts.append(f'<text class="fig-row" x="{x}" y="{bottom + 34}" text-anchor="middle">{name}</text>')
    parts.append(f'<text class="fig-axis-title" transform="translate(20 {top + height / 2}) rotate(-90)">Mean rating (1&#8211;7)</text>')
    return svg(460, bottom + 50, parts, "Mean attitudes and intentions with 95% confidence intervals, both above the scale midpoint of 4")


def fig_tool_compact(res):
    order = [("pu", "Usefulness"), ("peou", "Ease of use"), ("trust", "Trust"),
             ("privacy", "Privacy concerns"), ("oversight", "Oversight"), ("environ", "Environmental")]
    eff = {r["outcome_key"]: r for r in rows(res / "04_model_a_effects.csv", effect="Tool type (overall)")}
    items = [[(float(eff[k]["estimate"]), float(eff[k]["ci95_low"]), float(eff[k]["ci95_high"]), float(eff[k]["p_fdr"]) < .05, NAVY)] for k, _ in order]
    top, row_h, x0 = 30, 70, 190
    parts = row_labels([t for _, t in order], 0, top, row_h)
    p, bottom = coef_panel(items, x0, 270, -0.2, 0.6, [-0.2, 0, 0.2, 0.4, 0.6], top, row_h)
    parts += p
    parts.append(f'<text class="fig-axis-title" x="{x0 + 135}" y="{bottom + 66}">Bespoke − general-purpose</text>')
    return svg(480, bottom + 80, parts, "Coefficient plot of bespoke minus general-purpose differences with 95% confidence intervals")


def fig_comfort_portrait(res):
    cats = ["1 Much less comfortable", "2 Slightly less comfortable", "3 About the same", "4 Slightly more comfortable", "5 Much more comfortable"]
    keys = ["Much less", "Slightly less", "Same", "Slightly more", "Much more"]
    cols = [NAVY, "#7f98ad", GREY, "#b07a9d", MAGENTA]
    data = {}
    for r in rows(res / "07_comfort_distribution.csv"):
        data.setdefault(r["respondent_type"], {})[r["response"]] = float(r["percent"])
    top, height, bar_w = 30, 440, 96
    bottom = top + height
    parts = []
    for x, (key, name) in zip((40, 170), [("Adult", "Adults"), ("Parent", "Parents")]):
        y = bottom
        for c, col in zip(cats, cols):
            h = data[key][c] / 100 * height
            y -= h
            parts.append(f'<rect x="{x}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" fill="{col}" />')
            if data[key][c] >= 8:
                parts.append(f'<text class="fig-bar-val" x="{x + bar_w / 2}" y="{y + h / 2 + 7:.1f}">{data[key][c]:.0f}%</text>')
        parts.append(f'<text class="fig-row" x="{x + bar_w / 2}" y="{bottom + 34}" text-anchor="middle">{name}</text>')
    ky = top + 20
    for j, (k, col) in enumerate(reversed(list(zip(keys, cols)))):
        parts.append(f'<rect x="306" y="{ky + j * 40}" width="20" height="20" fill="{col}" />')
        parts.append(f'<text class="fig-key-lg" x="336" y="{ky + j * 40 + 17}">{k}</text>')
    return svg(470, bottom + 50, parts, "Stacked bars of comfort with bespoke versus general-purpose tools for adults and parents")


def replace(html, name, content):
    start, end = f"<!-- fig:{name} -->", f"<!-- /fig:{name} -->"
    a, b = html.index(start) + len(start), html.index(end)
    return html[:a] + content + html[b:]


def main():
    res = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Repositories/attitudes-ai-mental-health/r/outputs/results"
    html = INDEX.read_text()
    html = replace(html, "overall", fig_overall_portrait(res))
    html = replace(html, "tool", fig_tool_compact(res))
    html = replace(html, "comfort", fig_comfort_portrait(res))
    html = replace(html, "predictors", fig_predictors(res))
    html = replace(html, "characteristics", fig_characteristics(res))
    res2 = Path(sys.argv[2]) if len(sys.argv) > 2 else res.parent.parent.parent / "r2/outputs/results"
    if "<!-- fig:students -->" in html:
        html = replace(html, "students", fig_students(res, res2))
    INDEX.write_text(html)
    print("Updated results figures in", INDEX.name)


if __name__ == "__main__":
    main()
