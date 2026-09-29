"""
dashboard.py — Streamlit: Anomaly Monitor.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from config import COLORS as C, DB_FILE, MARTS, REPORTS  # noqa: E402
import explanations as X  # noqa: E402
import insights_content  # noqa: E402,F401
import insight as INS  # noqa: E402

st.set_page_config(page_title="Anomaly Monitor", page_icon="🚨", layout="wide")


def _src():
    if DB_FILE.exists():
        return "db"
    if (MARTS / "mart_anomalies.parquet").exists():
        return "marts"
    return "none"


_S = _src()
if _S == "none":
    st.error("Data belum ada. Jalankan: `python src/run_pipeline.py`")
    st.stop()


@st.cache_data(show_spinner="Memuat hasil deteksi...")
def q(name):
    if _S == "db":
        con = duckdb.connect(str(DB_FILE), read_only=True)
        df = con.execute(f"SELECT * FROM {name}").df()
        # detections = seluruh titik + flag
        if name == "detections":
            pass
        con.close()
        return df
    p = MARTS / f"{name}.parquet"
    return pd.read_parquet(p) if p.exists() else pd.DataFrame()


def style(fig, h=420):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=54, b=10),
                      paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#D5DBE1"),
                      title=dict(font=dict(size=16, color="#fff")),
                      legend=dict(bgcolor="rgba(0,0,0,0)"))
    fig.update_xaxes(gridcolor="#2A3038", zeroline=False)
    fig.update_yaxes(gridcolor="#2A3038", zeroline=False)
    return fig


def kpi(col, label, value, sub, color):
    col.markdown(
        f"""<div style="background:#1A1F2B;border-left:4px solid {color};
        padding:14px 16px;border-radius:10px;height:118px;">
        <div style="color:#9AA7B4;font-size:.76rem;text-transform:uppercase;
        letter-spacing:.06em;">{label}</div>
        <div style="color:{color};font-size:1.55rem;font-weight:700;
        margin-top:6px;">{value}</div>
        <div style="color:#6B7885;font-size:.75rem;">{sub}</div></div>""",
        unsafe_allow_html=True)


anom = q("mart_anomalies")
stats = q("mart_series_stats")
latest = q("mart_latest")
# detections tidak di-commit (besar) — ambil dari DB bila ada, jika tidak
det = q("detections") if _S == "db" else pd.DataFrame()
try:
    api_anom = json.loads((REPORTS / "anomalies.json").read_text())
except Exception:
    api_anom = {"count": 0, "anomalies": []}

st.markdown(
    f"""<div style="background:linear-gradient(100deg,{C['primary']},{C['red']});
    padding:22px 26px;border-radius:14px;margin-bottom:18px;">
    <div style="font-size:1.7rem;font-weight:800;color:white;">
    🚨 Multi-Source Anomaly Monitor</div>
    <div style="color:#D7E4DC;font-size:.9rem;margin-top:4px;">
    Deteksi anomali realtime dari data live (kurs · kripto · cuaca) ·
    3 metode statistik · by <b>Sandi Ridwan</b></div></div>""",
    unsafe_allow_html=True)

X.render("kpi", st=st)
n_src = int(stats["source"].nunique()) if len(stats) else 0
n_obs = int(stats["n"].sum()) if len(stats) else 0
n_anom = int(len(anom))
k1, k2, k3, k4 = st.columns(4)
kpi(k1, "Sumber dipantau", f"{n_src}", "kurs/kripto/cuaca", C["primary"])
kpi(k2, "Observasi", f"{n_obs:,}", "data live", C["blue"])
kpi(k3, "Anomali", f"{n_anom}", "konsensus ≥2 metode", C["red"])
kpi(k4, "Metode", "3", "z · ewma · iqr", C["purple"])
INS.box("kpi", st=st)

t1, t2, t3 = st.tabs(["📈 Tren & Anomali", "🔬 Metode", "📖 Metodologi"])

with t1:
    X.render("series", st=st)
    sel = st.selectbox("Sumber", stats["source"].tolist()) if len(stats) else None
    if sel and _S == "db" and not det.empty:
        d = det[det.source == sel].copy()
        d["ts"] = pd.to_datetime(d["ts"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=d["ts"], y=d["value"], mode="lines",
                                 name=sel, line=dict(color=C["blue"], width=1.5)))
        a = d[d["is_anomaly"]]
        fig.add_trace(go.Scatter(x=a["ts"], y=a["value"], mode="markers",
                                 name="anomali", marker=dict(color=C["red"],
                                 size=10, symbol="x")))
        style(fig, 420).update_layout(title=f"{sel} — anomali ditandai",
                                      yaxis_title="nilai")
        st.plotly_chart(fig, use_container_width=True)
    else:
        # fallback: tunjukkan anomali saja (detections tak tersedia)
        if len(anom):
            a = anom[anom.source == sel] if sel else anom
            st.dataframe(a, use_container_width=True, hide_index=True)
        else:
            st.info("Rincian tren per titik perlu DB lengkap "
                    "(jalankan pipeline penuh).")
    INS.box("series", st=st)

    X.render("top", st=st)
    if len(anom):
        top = anom.head(15).copy()
        top["label"] = top["ts"].astype(str).str[:16] + " · " + top["nama"]
        fig = px.bar(top.iloc[::-1], x="score", y="label", orientation="h",
                     color="n_methods", color_continuous_scale="Reds",
                     text=top["n_methods"].astype(str) + " metode")
        style(fig, 460).update_layout(coloraxis_showscale=False,
                                      title="Anomali Terparah (skor |z|)",
                                      xaxis_title="skor", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    INS.box("top", st=st)

with t2:
    X.render("methods", st=st)
    if _S == "db" and not det.empty:
        m = det.groupby("source")[["z_flag", "ewma_flag", "iqr_flag"]].sum().reset_index()
        fig = px.bar(m, x="source", y=["z_flag", "ewma_flag", "iqr_flag"],
                     barmode="group", title="Jumlah flag per metode")
        style(fig, 380).update_layout(xaxis_title="", yaxis_title="flag")
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(stats, use_container_width=True, hide_index=True)

with t3:
    X.render("method", st=st)
    st.markdown("#### Tiga metode deteksi")
    st.markdown(
        "- **Z-score (pada perubahan)** — seberapa jauh delta dari rata-rata delta.\n"
        "- **EWMA** — deteksi pergeseran level (anomali bertahap).\n"
        "- **IQR (Tukey)** — robust terhadap outlier; tangani seri hampir konstan.\n\n"
        "**Aturan final:** anomali = didukung **≥2 dari 3** metode → kurangi "
        "false positive. Setiap anomali menyimpan metode & skor (auditable).\n\n"
        "**Sumber:** 3 API publik tanpa key (Frankfurter, CoinGecko, Open-Meteo).")
    st.code("""
 ingest.py ─► staging (Parquet) ─► detect.py (3 metode) ─► analyze.py ─► marts
                                          │
                        dashboard.py · anomalies.json · tests
    """, language="text")
    st.markdown(
        "- **Batas jujur:** ambang tetap (bukan adaptif per musim); data live "
        "bergantung ketersediaan API; deteksi diuji pada data historis, bukan "
        "produksi 24/7.")

st.markdown(
    f"""<hr style="border-color:#2A3038;">
    <div style="color:#8B9AA6;font-size:.8rem;text-align:center;">
    🚨 Multi-Source Anomaly Monitor · sumber live publik · DuckDB + scipy/pandas ·
    oleh <b>Sandi Ridwan</b><br>Analisis edukasional.</div>""",
    unsafe_allow_html=True)
