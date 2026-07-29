import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from config.settings import METRICS_CONFIG
from repository.repository import Repository
from transforms.gold_transforms import compute_metric_scores


st.set_page_config(page_title="דירוג מניות · מסוף ניקוד", layout="wide", page_icon="📈")

# ---------------------------------------------------------------------------
# עיצוב: פלטה + טיפוגרפיה + סרט טיקר גולל (החתימה הויזואלית של הדשבורד)
# ---------------------------------------------------------------------------
BG = "#0B1120"
SURFACE = "#141C2F"
TEXT = "#E7EAF3"
MUTED = "#8892A6"
GOLD = "#E8B84B"
TEAL = "#3FD6C0"
ROSE = "#E85D6B"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    color: {TEXT};
}}

h1, h2, h3 {{
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: -0.01em;
}}

.mono {{
    font-family: 'JetBrains Mono', monospace;
}}

/* --- סרט טיקר גולל --- */
.ticker-wrap {{
    width: 100%;
    overflow: hidden;
    background: {SURFACE};
    border: 1px solid rgba(232,184,75,0.25);
    border-radius: 10px;
    padding: 10px 0;
    margin-bottom: 28px;
}}
.ticker-move {{
    display: inline-block;
    white-space: nowrap;
    animation: ticker-scroll 28s linear infinite;
}}
@keyframes ticker-scroll {{
    0%   {{ transform: translateX(0%); }}
    100% {{ transform: translateX(-50%); }}
}}
.ticker-item {{
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 15px;
    padding: 0 28px;
}}
.ticker-symbol {{ color: {TEXT}; font-weight: 600; }}
.ticker-up {{ color: {TEAL}; }}
.ticker-down {{ color: {ROSE}; }}

@media (prefers-reduced-motion: reduce) {{
    .ticker-move {{ animation: none; }}
}}

.rank-badge {{
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    color: {GOLD};
    font-size: 13px;
}}
</style>
""", unsafe_allow_html=True)

st.title("📈 דירוג מניות לפי מדדים פיננסיים")
st.caption(" השוואת צמיחה רבעונית בין המניות, מנורמלת ומשוקללת לציון אחד  (Quarterly Normalized YoY) ")

repo = Repository()
 

@st.cache_data
def load_metrics_table():
    return repo.load_streamlit("gold", "metrics")


try:
    metrics_table = load_metrics_table()
except Exception:
    st.error(
        "לא ניתן לטעון את טבלת gold_metrics. ודא שהרצת קודם את "
        "`python -m pipelines.run_gold` כדי לייצר אותה."
    )
    st.stop()

# ---------------------------------------------------------------------------
# סייד-בר: משקלים
# ---------------------------------------------------------------------------
st.sidebar.header("⚖️ משקלים למדדים")
st.sidebar.caption("שנה משקל למדד - הציונים והגרפים מתעדכנים מיד")

weights = {}
for key, cfg in METRICS_CONFIG.items():
    weights[key] = st.sidebar.slider(
        cfg["name"], min_value=0.0, max_value=3.0, value=1.0, step=0.1, key=f"weight_{key}"
    )

if st.sidebar.button("🔄 אפס למשקל שווה"):
    for key in METRICS_CONFIG:
        st.session_state[f"weight_{key}"] = 1.0
    st.rerun()

scores_table = compute_metric_scores(metrics_table, METRICS_CONFIG, weights=weights)
scores_table = scores_table.sort_values("final_score", ascending=False).reset_index(drop=True)

# ---------------------------------------------------------------------------
# סרט טיקר גולל - בראש העמוד, לפני הכל
# ---------------------------------------------------------------------------
ticker_items = ""
for _, row in scores_table.iterrows():
    direction = "ticker-up" if row["final_score"] >= 5 else "ticker-down"
    arrow = "▲" if row["final_score"] >= 5 else "▼"
    ticker_items += (
        f'<span class="ticker-item"><span class="ticker-symbol">{row["ticker"]}</span> '
        f'<span class="{direction}">{arrow} {row["final_score"]:.2f}</span></span>'
    )

st.markdown(
    f'<div class="ticker-wrap"><div class="ticker-move">{ticker_items}{ticker_items}</div></div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# גרפים - לפני הטבלה
# ---------------------------------------------------------------------------
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("דירוג לפי ציון סופי")
    bar_colors = [GOLD if i == 0 else TEAL if v >= 5 else ROSE
                  for i, v in enumerate(scores_table["final_score"])]
    fig_bar = go.Figure(go.Bar(
        x=scores_table["final_score"],
        y=scores_table["ticker"],
        orientation="h",
        marker_color=bar_colors,
        text=[f"{v:.2f}" for v in scores_table["final_score"]],
        textposition="outside",
    ))
    fig_bar.update_layout(
        plot_bgcolor=SURFACE, paper_bgcolor=SURFACE,
        font=dict(color=TEXT, family="Inter"),
        xaxis=dict(range=[0, 10], gridcolor="rgba(255,255,255,0.08)", title="ציון סופי"),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.subheader("השוואת מדדים בין המניות")
    score_cols = [c for c in scores_table.columns if c.endswith("_score") and c != "final_score"]
    labels = [METRICS_CONFIG[c.replace("_score", "")]["name"] for c in score_cols]

    fig_radar = go.Figure()
    palette = [GOLD, TEAL, ROSE, "#7C9CE8"]
    for i, (_, row) in enumerate(scores_table.iterrows()):
        fig_radar.add_trace(go.Scatterpolar(
            r=[row[c] for c in score_cols] + [row[score_cols[0]]],
            theta=labels + [labels[0]],
            name=row["ticker"],
            line=dict(color=palette[i % len(palette)]),
            fill="toself",
            opacity=0.5,
        ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor=SURFACE,
            radialaxis=dict(range=[0, 10], gridcolor="rgba(255,255,255,0.15)"),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.15)"),
        ),
        paper_bgcolor=SURFACE,
        font=dict(color=TEXT, family="Inter", size=11),
        margin=dict(l=30, r=30, t=20, b=20),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

if not scores_table.empty:
    best = scores_table.iloc[0]
    st.success(f"🏆 המניה המובילה לפי המשקלים הנוכחיים: **{best['ticker']}** — ציון סופי {best['final_score']:.2f}")

# ---------------------------------------------------------------------------
# הטבלה - אחרי הגרפים
# ---------------------------------------------------------------------------
st.subheader("טבלת ציונים מלאה")

display_cols = ["ticker"] + score_cols + ["final_score"]
styled = (
    scores_table[display_cols]
    .style
    .background_gradient(cmap="RdYlGn", subset=score_cols + ["final_score"], vmin=0, vmax=10)
    .format({c: "{:.2f}" for c in score_cols + ["final_score"]})
)
st.dataframe(styled, use_container_width=True)

with st.expander("מה המשמעות של כל מדד?"):
    for key, cfg in METRICS_CONFIG.items():
        direction = "ככל שעלה יותר משנה שעברה" if cfg["higher_is_better"] else "ככל שירד יותר משנה שעברה"
        st.write(f"**{cfg['name']}** — {direction}, כך הציון גבוה יותר")