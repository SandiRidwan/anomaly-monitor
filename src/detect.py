"""
detect.py — DETEKSI ANOMALI (inti project).

Tiga metode statistik komplementer:
  1. Z-SCORE       — seberapa jauh dari rata-rata (dalam simpangan baku).
                     Cocok untuk data ~normal, deteksi lonjakan tunggal.
  2. EWMA          — exponential weighted moving average; menangkap PERGESERAN
                     level (anomali bertahap), tahan terhadap tren.
  3. IQR (Tukey)   — berbasis kuartil; ROBUST terhadap outlier (tidak
                     terpengaruh nilai ekstrem seperti z-score).

Prinsip: TIDAK ada metode tunggal yang benar untuk semua pola. Kami menjalankan
ketiganya dan menandai titik yang terdeteksi oleh MAYORITAS → mengurangi
false positive. Setiap anomali disertai metode & skor, sehingga dapat diaudit.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _detrend(s: pd.Series) -> pd.Series:
    """
    Ubah seri menjadi PERUBAHAN (first difference) untuk deteksi anomali.

    Mengapa: anomaly detection yang baik menandai PERUBAHAN MENDADAK, bukan
    level. Seri tren mulus (naik konstan) punya delta kecil & stabil → tidak
    dianggap anomali (benar). Spike mendadak → delta besar → anomali.
    Titik pertama NaN (tak ada delta).
    """
    return s.diff()


def zscore_flags(s: pd.Series, threshold: float) -> pd.Series:
    """Anomali bila |z| residual > threshold (residual = nilai - tren lokal)."""
    if len(s) < 3 or s.std(ddof=0) == 0:
        return pd.Series(False, index=s.index)
    resid = _detrend(s)
    sd = resid.std(ddof=0)
    if not sd or np.isnan(sd):
        return pd.Series(False, index=s.index)
    z = resid / sd
    return (z.abs() > threshold).fillna(False)


def ewma_flags(s: pd.Series, span: int, threshold: float) -> pd.Series:
    """Anomali bila deviasi relatif dari EWMA lampau > threshold."""
    if len(s) < span + 1:
        return pd.Series(False, index=s.index)
    # EWMA dari nilai SEBELUM titik (shift 1) agar tidak 'menyerap' anomali
    baseline = s.ewm(span=span, adjust=False).mean().shift(1)
    dev = (s - baseline).abs() / baseline.abs().replace(0, np.nan)
    return (dev > threshold).fillna(False)


def iqr_flags(s: pd.Series, k: float) -> pd.Series:
    """
    Anomali (Tukey) berbasis kuartil pada RESIDUAL (detrend lokal).
    Tepi seri diabaikan (NaN) agar tidak false positive.
    """
    if len(s) < 4:
        return pd.Series(False, index=s.index)
    resid = _detrend(s).dropna()
    if len(resid) < 4:
        return pd.Series(False, index=s.index)
    q1, q3 = resid.quantile(0.25), resid.quantile(0.75)
    iqr = q3 - q1
    if iqr > 0:
        lo, hi = q1 - k * iqr, q3 + k * iqr
        flags = (resid < lo) | (resid > hi)
    else:
        # Sebaran mayoritas nol (seri hampir konstan + sedikit spike).
        # IQR dan MAD keduanya nol → skala sebaran tidak dapat diestimasi.
        med = resid.median()
        dev = (resid - med).abs()
        pos = dev[dev > 0]
        if len(pos) == 0:
            return pd.Series(False, index=s.index)
        # Bila mayoritas (>50%) residual PERSIS nol → derau nol; setiap
        # simpangan nyata adalah anomali. Jika tidak, pakai ambang relatif.
        frac_zero = (dev == 0).mean()
        if frac_zero > 0.5:
            flags = dev > 0
        else:
            flags = dev > pos.median() * k
    return flags.reindex(s.index).fillna(False)


def detect_series(s: pd.Series, z_thr: float, ewma_span: int,
                  ewma_thr: float, iqr_k: float, min_obs: int) -> pd.DataFrame:
    """
    Jalankan 3 metode pada satu seri. Kembalikan DataFrame per titik dengan
    flag tiap metode + verdict (mayoritas) + skor.
    """
    out = pd.DataFrame({"value": s.astype(float)})
    if len(s) < min_obs:
        out["z_flag"] = out["ewma_flag"] = out["iqr_flag"] = False
        out["n_methods"] = 0
        out["is_anomaly"] = False
        out["methods"] = ""
        out["score"] = 0.0
        return out

    out["z_flag"] = zscore_flags(s, z_thr).values
    out["ewma_flag"] = ewma_flags(s, ewma_span, ewma_thr).values
    out["iqr_flag"] = iqr_flags(s, iqr_k).values
    out["n_methods"] = out[["z_flag", "ewma_flag", "iqr_flag"]].sum(axis=1)
    # Mayoritas (>=2 metode) = anomali final
    out["is_anomaly"] = out["n_methods"] >= 2
    out["methods"] = out.apply(
        lambda r: ",".join([m for m, f in [("z", r.z_flag), ("ewma", r.ewma_flag),
                                           ("iqr", r.iqr_flag)] if f]), axis=1)
    # skor kontinu: |z-score| (untuk peringkat keparahan)
    if s.std(ddof=0) > 0:
        out["score"] = ((s - s.mean()) / s.std(ddof=0)).abs().round(2).values
    else:
        out["score"] = 0.0
    return out


def detect_all(df: pd.DataFrame, z_thr=3.0, ewma_span=14, ewma_thr=0.05,
               iqr_k=1.5, min_obs=10) -> pd.DataFrame:
    """Deteksi anomali untuk SEMUA sumber dalam satu DataFrame panel."""
    frames = []
    for src, g in df.groupby("source"):
        g = g.sort_values("ts").reset_index(drop=True)
        # gunakan index posisi (0..n-1) agar aman terhadap ts duplikat
        s = pd.Series(g["value"].values, index=range(len(g)))
        res = detect_series(s, z_thr, ewma_span, ewma_thr, iqr_k, min_obs)
        res["source"] = src
        res["ts"] = g["ts"].values
        frames.append(res)
    return pd.concat(frames, ignore_index=True)
