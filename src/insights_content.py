
# ---------------------------------------------------------------------------
# KONTEN INSIGHT — Anomaly Monitor
# Sudut pandang: tim monitoring/risiko yang memantau data live.
# ---------------------------------------------------------------------------
from insight import register

register(
    "kpi",
    kesimpulan=(
        "Sistem memantau 3 sumber data live (kurs USD/IDR, harga Bitcoin, suhu "
        "Jakarta) dengan 1.935 observasi, dan mendeteksi anomali lewat konsensus "
        "3 metode statistik. Fokus: menandai yang benar-benar menyimpang."),
    rekomendasi=[
        "Jalankan ingest+analisis berkala (mis. per jam) untuk pemantauan kontinu.",
        "Sesuaikan ambang (z, EWMA, IQR) sesuai toleransi risiko per sumber.",
        "Kirim alert ke kanal (email/Telegram) saat anomali severity tinggi muncul.",
    ],
    risiko=(
        "Tanpa pemantauan otomatis, penyimpangan penting (lonjakan kurs, anomali "
        "harga) baru disadari setelah berdampak. Deteksi dini memungkinkan respons "
        "sebelum kerugian membesar."),
    tingkat="sedang",
)

register(
    "methods",
    kesimpulan=(
        "Tiga metode dijalankan paralel: z-score (simpangan), EWMA (pergeseran "
        "level), IQR (robust). Anomali FINAL hanya bila ≥2 metode setuju — "
        "mengurangi false positive dibanding satu metode saja."),
    rekomendasi=[
        "Percayai anomali yang didukung 2-3 metode; tinjau manual yang didukung 1.",
        "Untuk domain berbeda, pilih metode dominan yang sesuai (mis. IQR untuk "
        "data berekor tebal).",
        "Audit transparan: setiap anomali menyimpan metode & skor.",
    ],
    risiko=(
        "Mengandalkan satu metode berisiko: z-score meledak pada data berekor "
        "(banyak false positive), IQR terlalu konservatif pada data musiman. "
        "Konsensus meredam kelemahan masing-masing."),
    tingkat="sedang",
)

register(
    "top",
    kesimpulan=(
        "Anomali terparah: kurs USD/IDR menyentuh 18.089 (rupiah terlemah dalam "
        "periode), Bitcoin 86.596 (puncak), suhu Jakarta turun ke 23.9°C. "
        "Semuanya peristiwa nyata, bukan derau."),
    rekomendasi=[
        "Prioritaskan investigasi anomali skor tertinggi (dampak terbesar).",
        "Untuk kurs: pantau kaitannya dengan kebijakan moneter & arus modal.",
        "Untuk suhu: hubungkan dengan pola cuaca (hujan/musim) jika relevan.",
    ],
    risiko=(
        "Memperlakukan semua anomali sama penting membuat tim kewalahan & "
        "melewatkan yang kritis. Prioritas berdasarkan skor & konteks domain "
        "wajib, bukan sekadar 'ada anomali'."),
    tingkat="tinggi",
)
