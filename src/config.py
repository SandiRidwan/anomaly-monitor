"""
config.py — konfigurasi anomaly monitor (satu sumber kebenaran).

Project: Multi-Source Anomaly Monitor
Fokus: memantau data LIVE dari 3 sumber (kurs, kripto, cuaca) dan mendeteksi
anomali otomatis dengan metode statistik (z-score, EWMA, IQR) + alert.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STAGING = DATA / "staging"
MARTS = DATA / "marts"
DB = ROOT / "db"
REPORTS = ROOT / "reports"
for _p in (STAGING, MARTS, DB, REPORTS):
    _p.mkdir(parents=True, exist_ok=True)

DB_FILE = DB / "monitor.duckdb"

# ---- Sumber data LIVE (publik) ---------------------------------------------
SOURCES = {
    "usd_idr": {
        "tipe": "fx",
        "url": "https://api.frankfurter.app/2023-01-01..?from=USD&to=IDR",
        "nama": "Kurs USD/IDR",
        "satuan": "IDR",
    },
    "btc_usd": {
        "tipe": "crypto",
        "url": ("https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
                "?vs_currency=usd&days=90&interval=daily"),
        "nama": "Harga Bitcoin USD",
        "satuan": "USD",
    },
    "jkt_temp": {
        "tipe": "weather",
        "url": ("https://api.open-meteo.com/v1/forecast?latitude=-6.2"
                "&longitude=106.8&hourly=temperature_2m&past_days=30"),
        "nama": "Suhu Jakarta (°C)",
        "satuan": "°C",
    },
}

# ---- Parameter deteksi anomali ---------------------------------------------
# Z-score pada RESIDUAL (detrend lokal): |z| > ambang → anomali.
Z_THRESHOLD = 2.5
# EWMA: deviasi relatif dari EWMA lampau melebihi ambang → anomali.
EWMA_SPAN = 14
EWMA_THRESHOLD = 0.08      # 8% (longgar; hindari false positive fluktuasi harian)
# IQR pada RESIDUAL: di luar [Q1 - k*IQR, Q3 + k*IQR] → anomali.
IQR_K = 2.0
# Minimal observasi sebelum deteksi (hindari false positive di awal).
MIN_OBS = 10

# ---- Palet warna -----------------------------------------------------------
COLORS = {
    "primary": "#1F5C3D", "accent": "#E4A11B", "dark": "#1B2A33",
    "grey": "#8B9AA6", "red": "#C0392B", "blue": "#2E6F95",
    "purple": "#6A4C93", "teal": "#2A9D8F",
}
