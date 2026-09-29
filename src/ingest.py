"""
ingest.py — tarik data LIVE dari 3 sumber → staging (Parquet).

Idempoten (timpa). Retry + timeout. Normalisasi ke bentuk seragam:
  (source, ts, value, unit)
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

from config import SOURCES, STAGING

H = {"User-Agent": "anomaly-monitor/1.0", "Accept": "application/json"}


def _get(url, retries=3):
    last = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers=H), timeout=45) as r:
                return json.loads(r.read())
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(str(last)[:120])


def fetch_fx(spec) -> pd.DataFrame:
    d = _get(spec["url"])
    rows = [{"ts": k, "value": v.get("IDR")} for k, v in d.get("rates", {}).items()]
    df = pd.DataFrame(rows).dropna()
    return df


def fetch_crypto(spec) -> pd.DataFrame:
    d = _get(spec["url"])
    prices = d.get("prices", [])
    rows = [{"ts": datetime.fromtimestamp(ms / 1000, timezone.utc)
             .date().isoformat(), "value": v} for ms, v in prices]
    return pd.DataFrame(rows).dropna()


def fetch_weather(spec) -> pd.DataFrame:
    d = _get(spec["url"])
    h = d.get("hourly", {})
    times, vals = h.get("time", []), h.get("temperature_2m", [])
    rows = [{"ts": t, "value": v} for t, v in zip(times, vals) if v is not None]
    return pd.DataFrame(rows).dropna()


FETCHERS = {"fx": fetch_fx, "crypto": fetch_crypto, "weather": fetch_weather}


def main() -> None:
    t0 = time.time()
    all_frames = []
    print("[ingest] menarik data live dari 3 sumber")
    for key, spec in SOURCES.items():
        try:
            df = FETCHERS[spec["tipe"]](spec)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {key}: {str(e)[:70]}")
            continue
        if df.empty:
            print(f"  ! {key}: kosong")
            continue
        df["source"] = key
        df["nama"] = spec["nama"]
        df["unit"] = spec["satuan"]
        all_frames.append(df)
        print(f"  {key:10} {spec['nama']:20} {len(df):5} observasi")

    out = pd.concat(all_frames, ignore_index=True)
    # PENTING: format ts bercampur ('2023-12-29' & '2026-08-30T00:00').
    # pandas dengan satu format akan gagal untuk yang lain → pakai ISO8601.
    out["ts"] = pd.to_datetime(out["ts"], format="ISO8601", errors="coerce")
    n_nat = int(out["ts"].isna().sum())
    if n_nat:
        print(f"  ! {n_nat} timestamp gagal diparse — dibuang")
    out = out.dropna(subset=["ts", "value"]).sort_values(["source", "ts"])
    out.to_parquet(STAGING / "live.parquet", index=False)

    meta = {"run_at": datetime.now(timezone.utc).isoformat(),
            "rows": int(len(out)),
            "per_source": out["source"].value_counts().to_dict(),
            "duration_sec": round(time.time() - t0, 1)}
    (STAGING / "_ingest_meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[ingest] selesai: {len(out)} baris ({meta['duration_sec']}s)")


if __name__ == "__main__":
    main()
