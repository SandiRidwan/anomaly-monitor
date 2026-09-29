"""explanations.py — narasi Kenapa · Tujuan · Dampak tiap elemen."""

from __future__ import annotations

EXPLAIN: dict[str, dict] = {
    "kpi": {
        "judul": "Ringkasan Pemantauan",
        "kenapa": "Butuh gambaran cepat: berapa sumber dipantau, berapa anomali.",
        "tujuan": "Menjawab: apakah ada yang perlu perhatian sekarang?",
        "dampak": "Menentukan apakah perlu investigasi lanjutan.",
        "baca": "Jumlah anomali dari konsensus ≥2 metode.",
    },
    "series": {
        "judul": "Tren & Anomali per Sumber",
        "kenapa": "Grafik menunjukkan konteks; titik merah = anomali yang terdeteksi.",
        "tujuan": "Menjawab: kapan & seberapa ekstrem penyimpangan terjadi?",
        "dampak": "Dasar investigasi penyebab lonjakan/penurunan.",
        "baca": "Garis = nilai; titik merah = anomali (mayoritas metode setuju).",
    },
    "methods": {
        "judul": "Perbandingan Metode Deteksi",
        "kenapa": "Tak ada satu metode yang benar untuk semua pola. Konsensus "
                  "mengurangi false positive.",
        "tujuan": "Menjawab: metode mana yang menandai titik mana?",
        "dampak": "Transparansi: auditor dapat melihat dasar setiap anomali.",
        "baca": "Batang = jumlah flag per metode; anomali final = ≥2 metode.",
    },
    "top": {
        "judul": "Peringkat Anomali Terparah",
        "kenapa": "Tidak semua anomali sama penting. Peringkat membantu prioritas.",
        "tujuan": "Menjawab: mana yang paling ekstrem & harus didahulukan?",
        "dampak": "Fokus tim pada penyimpangan berdampak terbesar.",
        "baca": "Diurutkan skor (|z|); lebih tinggi = lebih ekstrem.",
    },
    "method": {
        "judul": "Metodologi",
        "kenapa": "Hasil harus dapat ditelusuri & direproduksi.",
        "tujuan": "Menjelaskan 3 metode + sumber data live.",
        "dampak": "Dapat dipercaya & disesuaikan ambangnya.",
        "baca": "Lihat docs/ADR.md.",
    },
}


def text(key: str) -> str:
    e = EXPLAIN.get(key)
    if not e:
        return ""
    p = [f"**{e['judul']}**", f"- **Kenapa:** {e['kenapa']}",
         f"- **Tujuan:** {e['tujuan']}", f"- **Dampak:** {e['dampak']}"]
    if e.get("baca"):
        p.append(f"- **Cara baca:** {e['baca']}")
    return "\n".join(p)


def render(key: str, expanded: bool = False, st=None) -> None:
    if st is None:
        import streamlit as st  # noqa
    e = EXPLAIN.get(key)
    if not e:
        return
    with st.expander(f"💡 {e['judul']} — Kenapa · Tujuan · Dampak",
                     expanded=expanded):
        st.markdown(
            f"**🔎 Kenapa** — {e['kenapa']}\n\n"
            f"**🎯 Tujuan** — {e['tujuan']}\n\n"
            f"**📈 Dampak** — {e['dampak']}")
        if e.get("baca"):
            st.caption(f"👁️ Cara baca: {e['baca']}")


def audit(verbose: bool = True) -> bool:
    ok = True
    for k, v in EXPLAIN.items():
        miss = [f for f in ("kenapa", "tujuan", "dampak") if not v.get(f)]
        if miss:
            ok = False
            if verbose:
                print(f"  MISSING {k}: {miss}")
    if verbose:
        print(f"Penjelasan: {len(EXPLAIN)} | "
              f"{'SEMUA LENGKAP' if ok else 'ADA YANG KURANG'}")
    return ok


if __name__ == "__main__":
    raise SystemExit(0 if audit() else 1)
