"""
decision.py — DECISION ENGINE (mesin keputusan terukur).

Berbeda dari 'Insight & Rekomendasi' (narasi kualitatif), modul ini mengubah
SINYAL menjadi SKOR KEPUTUSAN numerik, lalu memetakan ke tier AKSI via ambang —
sehingga keputusan dapat dibandingkan, diurutkan, dan diaudit.

Kerangka (5 langkah):
  1. SIGNAL   — kumpulkan sinyal (fitur) dari data.
  2. SCORE    — gabungkan sinyal berbobot (0..1) → skor keputusan.
  3. THRESHOLD— bandingkan skor dengan ambang (configurable).
  4. TIER     — petakan ke aksi diskret (mis. segera/investigasi/pantau).
  5. JUSTIFY  — hasilkan alasan terukur (kontribusi tiap sinyal).

Skor = Σ (bobot_i × nilai_i dinormalisasi), bobot dijumlahkan = 1.
"""
from __future__ import annotations

import pandas as pd


def normalize(x: float, lo: float, hi: float) -> float:
    """Normalisasi linear ke [0,1]; aman bila lo==hi."""
    if hi == lo:
        return 0.0
    v = (x - lo) / (hi - lo)
    return max(0.0, min(1.0, v))


def score_signals(signals: dict[str, float],
                  weights: dict[str, float]) -> tuple[float, dict]:
    """
    Gabungkan sinyal (sudah dinormalisasi 0..1) dengan bobot.
    Kembalikan (skor_total 0..1, kontribusi_per_sinyal).
    """
    total_w = sum(weights.get(k, 0) for k in signals) or 1.0
    contrib = {k: round(weights.get(k, 0) / total_w * v, 4)
               for k, v in signals.items()}
    skor = round(sum(contrib.values()), 4)
    return skor, contrib


def tier_of(score: float, thresholds: dict[str, float]) -> str:
    """
    Petakan skor ke tier. `thresholds` = {nama_tier: ambang_bawah}, mis.
    {"segera": 0.7, "investigasi": 0.4, "pantau": 0.0}. Pilih tier tertinggi
    yang ambangnya <= skor.
    """
    for tier, lo in sorted(thresholds.items(), key=lambda kv: -kv[1]):
        if score >= lo:
            return tier
    return "abaikan"


def justify(contrib: dict[str, float], tier: str) -> str:
    """Buat alasan terukur: sinyal mana paling berkontribusi."""
    if not contrib:
        return f"Skor rendah → {tier}."
    top = sorted(contrib.items(), key=lambda kv: -kv[1])[:2]
    parts = [f"{k} (+{v:.3f})" for k, v in top if v > 0]
    return (f"Tier '{tier}' didorong oleh: " + ", ".join(parts)) if parts \
        else f"Tier '{tier}'."


def decide(rows: list[dict]) -> pd.DataFrame:
    """
    rows: daftar dict, tiap baris punya:
      {"id": ..., "signals": {nama: nilai01}, "weights": {nama: bobot},
       "thresholds": {tier: ambang}}
    Kembalikan DataFrame dengan skor, tier, justifikasi, dan kontribusi.
    """
    out = []
    for r in rows:
        skor, contrib = score_signals(r["signals"], r["weights"])
        tier = tier_of(skor, r["thresholds"])
        rec = {
            "id": r.get("id"),
            "skor": skor,
            "tier": tier,
            "justifikasi": justify(contrib, tier),
            **{f"sig_{k}": v for k, v in r["signals"].items()},
        }
        # teruskan kolom meta (selain kunci internal) agar tidak hilang
        for k, v in r.items():
            if k not in ("signals", "weights", "thresholds"):
                rec[k] = v
        out.append(rec)
    return pd.DataFrame(out).sort_values("skor", ascending=False)


def audit(rows_expected: int | None = None, out: pd.DataFrame | None = None,
          verbose: bool = True) -> bool:
    """Uji dasar: skor dalam [0,1], tiap baris punya tier & justifikasi."""
    ok = True
    if out is not None:
        bad = out[(out.skor < 0) | (out.skor > 1)].shape[0]
        if bad:
            ok = False
            verbose and print(f"  skor di luar [0,1]: {bad}")
        miss = out[out.tier.isna() | (out.tier == "")].shape[0]
        if miss:
            ok = False
            verbose and print(f"  tier kosong: {miss}")
    if verbose:
        n = len(out) if out is not None else 0
        print(f"Decision engine: {n} keputusan | "
              f"{'OK' if ok else 'MASALAH'}")
    return ok
