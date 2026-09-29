"""
analyze.py — jalankan deteksi, simpan hasil, buat alert.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import duckdb
import pandas as pd

from config import (DB_FILE, EWMA_SPAN, EWMA_THRESHOLD, IQR_K, MARTS, REPORTS,
                    STAGING, Z_THRESHOLD, MIN_OBS)
from detect import detect_all

MARTS_TABLES = ["mart_anomalies", "mart_series_stats", "mart_latest"]


def main() -> None:
    df = pd.read_parquet(STAGING / "live.parquet")
    print(f"[analyze] {len(df)} observasi dari {df.source.nunique()} sumber")

    res = detect_all(df, Z_THRESHOLD, EWMA_SPAN, EWMA_THRESHOLD, IQR_K, MIN_OBS)
    res = res.merge(df[["source", "nama", "unit"]].drop_duplicates("source"),
                    on="source", how="left")

    con = duckdb.connect(str(DB_FILE))
    con.execute("DROP TABLE IF EXISTS detections")
    con.execute("CREATE TABLE detections AS SELECT * FROM res")

    # marts: anomali final
    con.execute("DROP TABLE IF EXISTS mart_anomalies")
    con.execute("""CREATE TABLE mart_anomalies AS
        SELECT source, nama, unit, ts, value, n_methods, methods, score
        FROM detections WHERE is_anomaly ORDER BY ts""")

    # marts: statistik per sumber
    con.execute("DROP TABLE IF EXISTS mart_series_stats")
    con.execute("""CREATE TABLE mart_series_stats AS
        SELECT source, any_value(nama) nama, count(*) n,
               round(avg(value),3) mean, round(stddev_pop(value),3) std,
               round(min(value),3) min, round(max(value),3) max,
               sum(CASE WHEN is_anomaly THEN 1 ELSE 0 END) n_anomalies,
               max(ts) last_ts
        FROM detections GROUP BY source""")

    # marts: nilai terbaru
    con.execute("DROP TABLE IF EXISTS mart_latest")
    con.execute("""CREATE TABLE mart_latest AS
        SELECT source, nama, unit, ts, value FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY source ORDER BY ts DESC) rn
            FROM detections) WHERE rn = 1""")

    for t in MARTS_TABLES:
        n = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f"[analyze] {t:20} {n:5} baris")
        con.execute(f"""COPY {t} TO '{(MARTS / (t + '.parquet')).as_posix()}'
            (FORMAT PARQUET)""")

    # alert ringkas
    anom = con.execute("""SELECT source, nama, ts, value, n_methods, methods,
        score FROM mart_anomalies ORDER BY score DESC""").fetchall()
    con.close()

    payload = {"generated_at": datetime.now(timezone.utc).isoformat(),
               "thresholds": {"z": Z_THRESHOLD, "ewma_pct": EWMA_THRESHOLD,
                              "iqr_k": IQR_K},
               "count": len(anom),
               "anomalies": [{"source": r[0], "nama": r[1], "ts": str(r[2]),
                              "value": r[3], "n_methods": r[4],
                              "methods": r[5], "score": r[6]} for r in anom]}
    (REPORTS / "anomalies.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n[analyze] {len(anom)} anomali terdeteksi:")
    for r in anom[:10]:
        print(f"   {str(r[2])[:16]}  {r[1][:20]:20} {r[3]:>12,.2f}  "
              f"[{r[5]}] skor={r[6]}")


if __name__ == "__main__":
    main()
