"""test_anomaly.py — uji deteksi anomali & pipeline (CI-friendly, offline)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd

from detect import detect_all, detect_series, ewma_flags, iqr_flags, zscore_flags

FAILS, PASSES = [], []


def check(name, cond, detail=""):
    (PASSES if cond else FAILS).append(name if cond else f"{name} — {detail}")
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + ("" if cond else f"  {detail}"))


def main() -> int:
    print("[test] uji deteksi anomali\n")

    # 1. seri datar → tak ada anomali
    flat = pd.Series([10.0] * 50)
    check("seri konstan → 0 z-anomali", zscore_flags(flat, 2.5).sum() == 0)

    # 2. sunspike jelas → terdeteksi z-score
    s = pd.Series([10.0] * 25 + [100.0] + [10.0] * 24)
    check("spike tunggal terdeteksi z", zscore_flags(s, 2.5).sum() >= 1)
    check("spike tunggal terdeteksi iqr", iqr_flags(s, 2.0).sum() >= 1)

    # 3. deteksi penuh menandai spike (mayoritas)
    res = detect_series(s, 2.5, 14, 0.08, 2.0, 10)
    check("spike → is_anomaly", res["is_anomaly"].sum() >= 1)
    check("kolom lengkap", {"z_flag", "ewma_flag", "iqr_flag", "n_methods",
                            "is_anomaly", "methods", "score"}.issubset(res.columns))

    # 4. min_obs: seri pendek → tidak mendeteksi
    short = pd.Series([1.0, 2.0, 3.0])
    rs = detect_series(short, 2.5, 14, 0.08, 2.0, 10)
    check("seri < min_obs → tidak ada anomali", rs["is_anomaly"].sum() == 0)

    # 5. EWMA menangkap pergeseran level bertahap
    shift = pd.Series(list(np.linspace(10, 10, 30)) + list(np.linspace(20, 20, 20)))
    check("EWMA menangkap pergeseran level", ewma_flags(shift, 14, 0.08).sum() >= 1)

    # 6. detrend: tren naik mulus TIDAK dianggap anomali
    trend = pd.Series(np.linspace(100, 200, 200))
    rt = detect_series(trend, 2.5, 14, 0.08, 2.0, 10)
    check("tren mulus → tidak dianggap anomali",
          rt["is_anomaly"].sum() <= 2, f"{rt['is_anomaly'].sum()} anomali")

    # 7. detect_all multi-source
    df = pd.DataFrame({
        "source": ["a"] * 50 + ["b"] * 50,
        "ts": pd.date_range("2024-01-01", periods=50).tolist() * 2,
        "value": list(np.linspace(10, 11, 49)) + [500.0] + [5.0] * 50,
    })
    da = detect_all(df)
    check("detect_all menangani multi-source", "source" in da.columns)
    check("detect_all menemukan spike di 'a'",
          da[(da.source == "a")].is_anomaly.sum() >= 1)

    print(f"\n[test] {len(PASSES)} lulus, {len(FAILS)} gagal")
    if FAILS:
        print("GAGAL:")
        for f in FAILS:
            print("  -", f)
        return 1
    print("[test] SEMUA UJI LULUS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
