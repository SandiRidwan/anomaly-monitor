
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


# --- Decision engine: keputusan terukur (skor + tier + justifikasi) ---
register(
    "decision",
    kesimpulan=(
        "Selain narasi, sistem kini menghasilkan SKOR KEPUTUSAN numerik per item "
        "(anomali/negara/ticker/metrik) berbasis sinyal berbobot, lalu memetakan "
        "ke TIER AKSI via ambang. Keputusan dapat dibandingkan & diurutkan."),
    rekomendasi=[
        "Jalankan item dengan tier prioritas tertinggi lebih dulu.",
        "Sesuaikan bobot sinyal & ambang tier di config sesuai kebijakan organisasi.",
        "Audit tiap keputusan lewat skor & justifikasi terukurnya.",
    ],
    risiko=(
        "Keputusan tanpa skor terukur cenderung subjektif & tidak konsisten. "
        "Namun skor pun bisa salah bila formulasi sinyal keliru — karena itu "
        "setiap keputusan menyertakan justifikasi yang dapat diaudit."),
    tingkat="tinggi",
)


# --------------------------------------------------------------------------
# Chart ECharts (v2) — insight & rekomendasi.
# --------------------------------------------------------------------------

register(
    "echarts_calendar",
    kesimpulan=(
        "Kalender frekuensi anomali memetakan KAPAN anomali menumpuk. Pola yang "
        "terlihat (mis. mengelompok di hari/pekan tertentu) menunjukkan anomali "
        "tidak acak — sering terkait rilis data ekonomi, jadwal pasar, atau "
        "peristiwa kalender. Ini mengubah pertanyaan dari 'apa' menjadi 'kapan "
        "waspada'."),
    rekomendasi=[
        "Naikkan sensitivitas pemantauan pada periode berisiko yang teridentifikasi.",
        "Cek apakah klaster bertepatan dengan event terjadwal (rilis CPI, FOMC, "
        "libur pasar) — bila ya, itu ekspektasi, bukan kejutan.",
        "Untuk klaster di luar event, selidiki penyebab struktural (perubahan "
        "kebijakan, gangguan pasokan data).",
    ],
    risiko=(
        "Tanpa pandangan temporal, tim bereaksi ad-hoc. Anomali yang sesungguhnya "
        "musiman bisa diperlakukan sebagai kejutan, memicu alarm berlebihan "
        "pada periode yang sebenarnya dapat diantisipasi."),
    tingkat="sedang",
)

register(
    "echarts_scores",
    kesimpulan=(
        "Boxplot skor anomali per sumber membandingkan SEBARAN & TINGKAT "
        "keparahan anomali antar-sumber. Sumber dengan kotak lebih tinggi dan "
        "ekor lebih panjang menghasilkan anomali lebih ekstrem/beragam; sumber "
        "dengan sebaran sempit relatif lebih stabil. Perbedaan ini penting: "
        "ambang tunggal untuk semua sumber akan salah kalibrasi."),
    rekomendasi=[
        "Kalibrasi ambang per sumber, bukan satu ambang global — sebaran tiap "
        "sumber berbeda.",
        "Selidiki sumber dengan banyak pencilan ekstrem lebih dulu (risiko "
        "operasional tertinggi).",
        "Audit apakah pencilan berasal dari lonjakan nyata atau kualitas data "
        "buruk (mis. gap API).",
    ],
    risiko=(
        "Ambang seragam membuat sumber bervolatilitas tinggi terus memicu alarm "
        "(alert fatigue) sementara sumber tenang melewatkan anomali nyata. "
        "Keduanya menurunkan kepercayaan pada sistem."),
    tingkat="sedang",
)


# --------------------------------------------------------------------------
# Perbaikan: key yang dipanggil dashboard tapi belum terdaftar (kotak insight
# sebelumnya kosong diam-diam).
# --------------------------------------------------------------------------

register(
    "series",
    kesimpulan=(
        "Tren per sumber mempertemukan nilai mentah dengan titik anomali yang "
        "ditandai. Terlihat apakah anomali berdiri sendiri (spike tunggal) atau "
        "bagian dari pergeseran level — dua hal dengan tindak lanjut berbeda."),
    rekomendasi=[
        "Anomali spike tunggal → verifikasi cepat, lalu pantau singkat.",
        "Anomali beruntun pada satu sumber → selidiki perubahan rezim "
        "(kebijakan, gangguan pasokan data), bukan sekadar satu titik.",
        "Bandingkan antar-sumber: kejutan serentak sering menandakan pemicu "
        "makro, bukan masalah data.",
    ],
    risiko=(
        "Membaca satu titik anomali tanpa konteks tren bisa memicu reaksi "
        "berlebihan. Sebaliknya, mengabaikan anomali beruntun berarti melewatkan "
        "pergeseran regime yang nyata."),
    tingkat="sedang",
)
