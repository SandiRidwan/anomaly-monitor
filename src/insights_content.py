
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
        {
            "aksi": "Jadwalkan ingest+analisis berkala untuk pemantauan kontinu",
            "langkah": [
                "Jalankan penarikan data dari 3 sumber live (kurs USD/IDR via "
                "Frankfurter, harga Bitcoin via CoinGecko, suhu Jakarta via "
                "Open-Meteo) secara berkala, mis. per jam.",
                "Pada tiap siklus, jalankan konsensus 3 metode (z-score pada "
                "perubahan, EWMA, IQR/Tukey) atas 1.935 observasi historis.",
                "Simpan hasil tiap run agar jumlah anomali (baseline 33) dan "
                "trennya dapat dibandingkan antar-periode.",
            ],
            "metrik": "Konsistensi jadwal run (>=98% siklus berhasil) & latensi "
                      "deteksi < 1 jam dari kejadian.",
            "pemilik": "Tim Monitoring / Data Engineer",
        },
        {
            "aksi": "Kalibrasi ambang statistik sesuai toleransi risiko per sumber",
            "langkah": [
                "Tetapkan ambang per sumber, bukan global, mengingat sebaran "
                "kurs, Bitcoin, dan suhu Jakarta berbeda nyata.",
                "Untuk data berekor tebal (Bitcoin) perlebar z-score dan "
                "andalkan IQR; untuk data musiman (suhu) sesuaikan EWMA.",
                "Terapkan aturan konsensus: anomali final hanya bila didukung "
                ">=2 dari 3 metode, untuk menekan false positive.",
            ],
            "metrik": "Rasio false positive turun (<5%) & tidak ada anomali nyata "
                      "yang hilang dari daftar final.",
            "pemilik": "Data Analyst / Risk Owner",
        },
        {
            "aksi": "Kirim alert otomatis ke kanal saat anomali severity tinggi",
            "langkah": [
                "Pasang pemicu notifikasi (email/Telegram) khusus untuk anomali "
                "final yang lolos konsensus >=2 metode.",
                "Tentukan tingkat severity (mis. berbasis skor keputusan) agar "
                "hanya anomali berdampak besar yang mengirim alert.",
                "Sertakan konteks pada tiap alert: sumber, nilai, metode "
                "pendukung, dan skor.",
            ],
            "metrik": "Waktu respons dari alert ke tindak lanjut < 30 menit & "
                      "tingkat alert fatigue (alert tidak ditindak) < 10%.",
            "pemilik": "Tim Monitoring / On-call Engineer",
        },
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
        {
            "aksi": "Prioritaskan anomali hasil konsensus, tinjau manual yang tunggal",
            "langkah": [
                "Terima langsung anomali final yang didukung >=2 dari 3 metode "
                "(z-score, EWMA, IQR) sebagai sinyal andal.",
                "Masukkan anomali yang hanya didukung 1 metode ke antrean "
                "tinjauan manual sebelum ditindaklanjuti.",
                "Catat pada tiap anomali berapa dan metode mana saja yang "
                "mendukungnya.",
            ],
            "metrik": ">=90% anomali berlabel final berasal dari konsensus & "
                      "tinjauan manual selesai < 24 jam.",
            "pemilik": "Data Analyst / Tim Monitoring",
        },
        {
            "aksi": "Pilih metode dominan sesuai karakter domain data",
            "langkah": [
                "Untuk data berekor tebal (harga Bitcoin) utamakan IQR (Tukey) "
                "yang robust terhadap pencilan ekstrem.",
                "Untuk deteksi pergeseran level bertahap (kurs USD/IDR) "
                "andalkan EWMA.",
                "Untuk simpanan perubahan mendadak (suhu Jakarta) gunakan "
                "z-score pada perubahan antar-observasi.",
            ],
            "metrik": "Setiap sumber punya konfigurasi metode eksplisit & jumlah "
                      "false positive per sumber terdokumentasi.",
            "pemilik": "Data Analyst",
        },
        {
            "aksi": "Jaga auditabilitas: simpan metode & skor tiap anomali",
            "langkah": [
                "Rekam untuk setiap anomali: sumber, timestamp, nilai, dan "
                "sumbangan skor tiap metode.",
                "Bertahankan 10 uji otomatis (offline) sebagai jaring agar logika "
                "konsensus tidak rusak saat diubah.",
                "Ekspor jejak audit agar dapat direproduksi kapan pun.",
            ],
            "metrik": "100% anomali punya jejak metode+skor & 10 uji otomatis "
                      "lulus pada setiap perubahan kode.",
            "pemilik": "Data Engineer / QA",
        },
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
        {
            "aksi": "Investigasi anomali skor tertinggi lebih dulu",
            "langkah": [
                "Urutkan 33 anomali final berdasarkan skor keputusan dan mulai "
                "dari yang tertinggi.",
                "Tandai tiga peristiwa ekstrem sebagai prioritas: kurs USD/IDR "
                "menyentuh 18.089, Bitcoin puncak 86.596, suhu Jakarta 23.9°C.",
                "Alokasikan sesi investigasi terjadwal khusus untuk anomali "
                "puncak ini.",
            ],
            "metrik": "Tiga anomali teratas terselesaikan investigasinya < 48 jam "
                      "sejak terdeteksi.",
            "pemilik": "Tim Monitoring / Risk Owner",
        },
        {
            "aksi": "Kaitkan anomali kurs dengan konteks moneter & arus modal",
            "langkah": [
                "Bandingkan lonjakan kurs USD/IDR (18.089) dengan rilis data "
                "ekonomi atau jadwal bank sentral pada tanggal terkait.",
                "Periksa apakah pergerakan selaras dengan tren arus modal "
                "regional.",
                "Catat temuan sebagai konteks pada entri anomali kurs.",
            ],
            "metrik": "Setiap anomali kurs besar punya catatan konteks makro & "
                      "hipotesis penyebab.",
            "pemilik": "Analis Makro / Data Analyst",
        },
        {
            "aksi": "Hubungkan anomali suhu dengan pola cuaca/musim",
            "langkah": [
                "Cocokkan penurunan suhu Jakarta ke 23.9°C dengan data curah "
                "hujan atau pola musim yang relevan.",
                "Klasifikasikan sebagai kejutan atau variasi musiman yang dapat "
                "diantisipasi.",
                "Simpan klasifikasi untuk memperhalus ambang deteksi suhu.",
            ],
            "metrik": "Anomali suhu terklasifikasi (musiman vs kejutan) > 90% & "
                      "dipakai untuk kalibrasi berikutnya.",
            "pemilik": "Data Analyst",
        },
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
        {
            "aksi": "Eksekusi item pada tier prioritas tertinggi lebih dulu",
            "langkah": [
                "Kelompokkan item (anomali/negara/ticker/metrik) ke tier aksi "
                "berdasarkan skor keputusan numerik.",
                "Proses tier tertinggi lebih dulu; tahan tier rendah sampai "
                "kapasitas tersedia.",
                "Tinjau ulang antrean tiap ada skor baru yang mengubah tier.",
            ],
            "metrik": "Tidak ada item tier tertinggi menganggur > 24 jam & SLA "
                      "per tier terpenuhi.",
            "pemilik": "Manajer Monitoring / Risk Owner",
        },
        {
            "aksi": "Kalibrasi bobot sinyal & ambang tier sesuai kebijakan organisasi",
            "langkah": [
                "Tetapkan bobot sinyal yang membentuk skor keputusan di config, "
                "bukan di kode.",
                "Sesuaikan ambang batas antar-tier mengikuti toleransi risiko "
                "dan kapasitas tim.",
                "Uji dampak perubahan bobot terhadap daftar 33 anomali sebelum "
                "menerapkannya.",
            ],
            "metrik": "Semua parameter bobot/ambang tersimpan di config & "
                      "perubahannya melewati uji regresi.",
            "pemilik": "Data Analyst / Pemilik Kebijakan",
        },
        {
            "aksi": "Audit setiap keputusan lewat skor & justifikasinya",
            "langkah": [
                "Sertakan pada tiap keputusan: skor numerik, tier, dan "
                "justifikasi yang mendasarinya.",
                "Lakukan tinjauan berkala atas keputusan yang menyimpang dari "
                "ekspektasi.",
                "Koreksi formulasi sinyal bila justifikasi menunjukkan bias "
                "sistematis.",
            ],
            "metrik": "100% keputusan punya skor+justifikasi & temuan audit "
                      "ditindaklanjuti < 1 minggu.",
            "pemilik": "QA / Internal Audit",
        },
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
        {
            "aksi": "Naikkan sensitivitas pemantauan pada periode berisiko",
            "langkah": [
                "Identifikasi dari kalender frekuensi kapan anomali menumpuk "
                "(hari/pekan tertentu).",
                "Turunkan ambang deteksi pada jendela waktu tersebut agar "
                "penyimpangan kecil pun tertangkap.",
                "Siapkan tim on-call tambahan pada periode itu.",
            ],
            "metrik": "Waktu deteksi pada periode berisiko memendek & tidak ada "
                      "anomali terlewat pada jendela tersebut.",
            "pemilik": "Tim Monitoring",
        },
        {
            "aksi": "Cocokkan klaster anomali dengan event terjadwal",
            "langkah": [
                "Samakan tanggal klaster dengan kalender event (rilis CPI, FOMC, "
                "libur pasar).",
                "Bila bertepatan, klasifikasikan sebagai ekspektasi, bukan "
                "kejutan, dan turunkan prioritas.",
                "Catat hasilnya agar menjadi konteks untuk periode serupa di "
                "masa depan.",
            ],
            "metrik": ">=90% klaster ber-event terklasifikasi benar & tidak lagi "
                      "memicu alert berlebihan.",
            "pemilik": "Data Analyst",
        },
        {
            "aksi": "Selidiki klaster di luar event untuk penyebab struktural",
            "langkah": [
                "Telusuri klaster tanpa event pendamping untuk perubahan "
                "kebijakan atau gangguan pasokan data.",
                "Bedakan gangguan teknis (gap API dari Frankfurter/CoinGecko/"
                "Open-Meteo) dari pergeseran nyata.",
                "Dokumentasikan temuan sebagai rekomendasi perbaikan proses.",
            ],
            "metrik": "Setiap klaster non-event punya akar penyebab & rencana "
                      "perbaikan terdokumentasi.",
            "pemilik": "Data Engineer / Data Analyst",
        },
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
        {
            "aksi": "Kalibrasi ambang per sumber, bukan satu ambang global",
            "langkah": [
                "Baca sebaran & panjang ekor skor anomali pada boxplot untuk "
                "masing-masing dari 3 sumber.",
                "Tetapkan ambang khusus per sumber sesuai sebarannya (kurs, "
                "Bitcoin, suhu berbeda karakter).",
                "Terapkan kalibrasi ini ke aturan konsensus >=2 metode.",
            ],
            "metrik": "Tidak ada satu ambang global dipakai & jumlah alarm palsu "
                      "per sumber turun.",
            "pemilik": "Data Analyst",
        },
        {
            "aksi": "Selidiki sumber dengan pencilan ekstrem terbanyak lebih dulu",
            "langkah": [
                "Urutkan sumber berdasarkan jumlah & keparahan pencilan pada "
                "boxplot.",
                "Mulai investigasi dari sumber berisiko operasional tertinggi.",
                "Kaitkan temuan dengan 33 anomali final yang terdeteksi.",
            ],
            "metrik": "Sumber paling ekstrem selesai ditinjau lebih dulu & "
                      "temuannya terdokumentasi.",
            "pemilik": "Tim Monitoring",
        },
        {
            "aksi": "Audit asal pencilan: lonjakan nyata atau kualitas data",
            "langkah": [
                "Periksa apakah pencilan berasal dari lonjakan pasar nyata atau "
                "dari gap/kualitas API publik.",
                "Validasi silang dengan sumber kedua saat ragu.",
                "Tandai pencilan akibat kualitas data agar dikecualikan dari "
                "pelaporan.",
            ],
            "metrik": ">=95% pencilan terklasifikasi benar (nyata vs artefak data).",
            "pemilik": "Data Engineer / QA",
        },
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
        {
            "aksi": "Tangani anomali spike tunggal dengan verifikasi cepat",
            "langkah": [
                "Untuk anomali tunggal, verifikasi nilai cepat terhadap sumber "
                "aslinya.",
                "Lanjutkan dengan pantauan singkat untuk memastikan tidak "
                "berlanjut.",
                "Tutup kasus bila tidak ada anomali susulan.",
            ],
            "metrik": "Anomali spike tunggal terverifikasi < 30 menit & tidak "
                      "berkembang jadi insiden.",
            "pemilik": "Tim Monitoring",
        },
        {
            "aksi": "Selidiki perubahan rezim pada anomali beruntun satu sumber",
            "langkah": [
                "Bila satu sumber (mis. kurs atau Bitcoin) menunjukkan anomali "
                "beruntun, periksa perubahan rezim.",
                "Cari pemicu struktural: perubahan kebijakan atau gangguan "
                "pasokan data.",
                "Perbarui ambang sumber itu bila memang terjadi pergeseran "
                "level permanen.",
            ],
            "metrik": "Setiap rangkaian anomali beruntun punya diagnosis rezim & "
                      "ambang yang diperbarui.",
            "pemilik": "Data Analyst / Risk Owner",
        },
        {
            "aksi": "Bandingkan antar-sumber untuk mendeteksi pemicu makro",
            "langkah": [
                "Periksa apakah anomali muncul serentak di lebih dari satu "
                "sumber.",
                "Bila serentak, curigai pemicu makro umum alih-alih masalah "
                "data tunggal.",
                "Naikkan tingkat keparahan insiden dan lakukan investigasi "
                "lintas sumber.",
            ],
            "metrik": "Kejutan serentak terdeteksi lintas sumber & dieskalasi "
                      "< 1 jam.",
            "pemilik": "Tim Monitoring / Risk Owner",
        },
    ],
    risiko=(
        "Membaca satu titik anomali tanpa konteks tren bisa memicu reaksi "
        "berlebihan. Sebaliknya, mengabaikan anomali beruntun berarti melewatkan "
        "pergeseran regime yang nyata."),
    tingkat="sedang",
)
