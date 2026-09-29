"""
decide_actions.py — terapkan decision engine pada hasil deteksi anomali.

Tujuan: mengubah daftar anomali menjadi PRIORITAS AKSI terukur.
Sinyal per anomali:
  · severity   — seberapa ekstrem (dari skor |z|, dinormalisasi)
  · consensus  — berapa metode setuju (1..3 → 0..1) = kepercayaan
  · criticality— seberapa penting sumbernya (konfigurasi bisnis)
Bobot: severity 0.45, consensus 0.35, criticality 0.20.
Tier aksi: segera (>=0.66) · investigasi (>=0.4) · pantau (>=0.2) · abaikan.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import duckdb
import pandas as pd

from config import DB_FILE, MARTS
from decision import decide, normalize

# Seberapa "penting" tiap sumber (bobot keputusan bisnis).
SOURCE_CRITICALITY = {"usd_idr": 1.0, "btc_usd": 0.7, "jkt_temp": 0.4}
WEIGHTS = {"severity": 0.45, "consensus": 0.35, "criticality": 0.20}
THRESHOLDS = {"segera": 0.66, "investigasi": 0.40, "pantau": 0.20}

OUT = "mart_decisions"


def main() -> None:
    con = duckdb.connect(str(DB_FILE))
    rows = con.execute("""SELECT source, nama, ts, value, n_methods, score
        FROM detections WHERE is_anomaly ORDER BY score DESC""").fetchall()
    if not rows:
        print("[decision] tidak ada anomali → tidak ada keputusan")
        con.close()
        return

    scores = [r[5] for r in rows]
    lo, hi = min(scores), max(scores)
    payload = []
    for (src, nama, ts, val, nmet, sc) in rows:
        signals = {
            "severity": normalize(sc, lo, max(hi, lo + 1e-9)),
            "consensus": normalize(nmet, 1, 3),
            "criticality": SOURCE_CRITICALITY.get(src, 0.5),
        }
        payload.append({"id": f"{src}@{ts}", "signals": signals,
                        "weights": WEIGHTS, "thresholds": THRESHOLDS,
                        "source": src, "nama": nama, "ts": str(ts),
                        "value": val, "n_methods": nmet})

    df = decide(payload)
    # sertakan metadata
    meta = pd.DataFrame(payload)[["id", "source", "nama", "ts", "value",
                                  "n_methods"]]
    df = df.merge(meta, on="id", how="left")

    con.execute(f"DROP TABLE IF EXISTS {OUT}")
    con.execute(f"CREATE TABLE {OUT} AS SELECT * FROM df")
    n = con.execute(f"SELECT count(*) FROM {OUT}").fetchone()[0]
    con.execute(f"""COPY {OUT} TO '{(MARTS / (OUT + '.parquet')).as_posix()}'
        (FORMAT PARQUET)""")
    con.close()

    print(f"[decision] {n} anomali diberi skor keputusan")
    for tier in ["segera", "investigasi", "pantau", "abaikan"]:
        c = int((df.tier == tier).sum())
        print(f"   {tier:12} {c}")
    print("\n[decision] aksi prioritas tertinggi:")
    for _, r in df.head(6).iterrows():
        print(f"   [{r['tier']:11}] skor={r['skor']:.2f}  {r['nama'][:18]:18} "
              f"{r['value']:>12,.1f}")
        print(f"      {r['justifikasi']}")


if __name__ == "__main__":
    main()
