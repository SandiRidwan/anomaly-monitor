<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=900&size=30&duration=3000&pause=1000&color=C0392B&center=true&vCenter=true&width=940&height=70&lines=MULTI-SOURCE+ANOMALY+MONITOR" alt="Anomaly Monitor" />

![Python](https://img.shields.io/badge/Python-3.10+-1F5C3D?style=for-the-badge&logo=python&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-SQL-FFF000?style=for-the-badge&logo=duckdb&logoColor=black)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Tests](https://img.shields.io/badge/tests-10-2E6F95?style=for-the-badge)

</div>

---

## 🚨 Apa ini?

**Deteksi anomali realtime** dari data live — memantau **3 sumber** (kurs
USD/IDR, harga Bitcoin, suhu Jakarta) dan menandai penyimpangan otomatis.

**Bukan satu metode** — tiga metode statistik dijalankan paralel, dan anomali
hanya dinyatakan bila **≥2 metode setuju** (konsensus) → menekan false positive.

```bash
python src/run_pipeline.py     # tarik data live → deteksi → tests
streamlit run app/dashboard.py
```

---

## 🔬 Tiga metode (konsensus)

| Metode | Menangkap | Kekuatan |
|---|---|---|
| **Z-score** | lonjakan mendadak | sensitif pada delta |
| **EWMA** | pergeseran level bertahap | tahan tren |
| **IQR (Tukey)** | penyimpangan ekstrem | robust terhadap outlier |

**Aturan final:** anomali bila ≥2 dari 3 metode menandai → kurangi false
positive. Setiap anomali menyimpan **metode & skor** (auditable).

---

## 📊 Temuan nyata (dari data live)

| Tanggal | Sumber | Nilai | Metode |
|---|---|---|---|
| 2026-07-08 | Kurs USD/IDR | **18.089** | z+iqr |
| 2026-09-22 | Bitcoin | **86.596** | z+ewma+iqr (3!) |
| 2026-09-28 | Suhu Jakarta | **23.9°C** | z+ewma+iqr |

33 anomali terdeteksi dari 1.935 observasi — semuanya peristiwa nyata
(rupiah terlemah, puncak BTC, penurunan suhu mendadak).

---

## 🏗️ Arsitektur

```
 3 API live (Frankfurter · CoinGecko · Open-Meteo)
              │
        ingest.py ─► staging (Parquet)
              │
   detect.py (z-score · EWMA · IQR) ─► analyze.py ─► marts
              │
     dashboard.py · anomalies.json · tests
```

| Lapisan | File | Peran |
|---|---|---|
| **Ingest** | `src/ingest.py` | 3 sumber live → normalisasi |
| **Deteksi** | `src/detect.py` | ★ 3 metode + konsensus |
| **Analisis** | `src/analyze.py` | marts + alert JSON |
| **Tests** | `tests/test_anomaly.py` | 10 uji (offline) |
| **Serve** | `app/dashboard.py` | Streamlit |

---

## 🧪 Kualitas (10 uji)

```
PASS  spike tunggal terdeteksi z & iqr
PASS  tren mulus → tidak dianggap anomali   ← penting!
PASS  EWMA menangkap pergeseran level
PASS  deteksi di tepi seri (titik terbaru)  ← untuk realtime
[test] 10 lulus, 0 gagal
```

**Pelajaran teknis:** deteksi harus bekerja pada **perubahan (delta)**, bukan
level — agar tren mulus tidak salah dianggap anomali, sementara lonjakan
mendadak (termasuk di titik terbaru) tetap tertangkap.

---

## ⚠️ Keterbatasan (jujur)

- **Ambang tetap** (z=2.5, EWMA=8%, IQR=2.0) — bukan adaptif per musim/domain.
- **Bergantung ketersediaan API** live (bisa timeout/gagal sementara).
- **Diuji pada snapshot** data historis, bukan operasi 24/7 produksi.
- Data live dapat direvisi; deteksi berbasis snapshot saat ingest.

---

## 🚀 Quick Start

```bash
pip install -r requirements.txt
python src/run_pipeline.py
streamlit run app/dashboard.py
```

---

## 🛠️ Tech Stack

| Layer | Teknologi |
|---|---|
| **Data live** | Frankfurter · CoinGecko · Open-Meteo |
| **Statistik** | pandas (z-score, EWMA, IQR) |
| **Database** | DuckDB |
| **Dashboard** | Streamlit + Plotly |
| **Tests** | uji kustom (offline) |

---

<!-- INSIGHTS:START -->
## 💡 Insight & Rekomendasi (per analisis)

_Setiap analisis disertai kesimpulan, rekomendasi tindakan, dan risiko bila diabaikan — bukan sekadar angka._

### 🟠 TOP
**Kesimpulan.** Anomali terparah: kurs USD/IDR menyentuh 18.089 (rupiah terlemah dalam periode), Bitcoin 86.596 (puncak), suhu Jakarta turun ke 23.9°C. Semuanya peristiwa nyata, bukan derau.

**Rekomendasi tindakan:**
- Prioritaskan investigasi anomali skor tertinggi (dampak terbesar).
- Untuk kurs: pantau kaitannya dengan kebijakan moneter & arus modal.
- Untuk suhu: hubungkan dengan pola cuaca (hujan/musim) jika relevan.

**⚠️ Risiko bila diabaikan.** Memperlakukan semua anomali sama penting membuat tim kewalahan & melewatkan yang kritis. Prioritas berdasarkan skor & konteks domain wajib, bukan sekadar 'ada anomali'.

### 🔵 KPI / Ringkasan
**Kesimpulan.** Sistem memantau 3 sumber data live (kurs USD/IDR, harga Bitcoin, suhu Jakarta) dengan 1.935 observasi, dan mendeteksi anomali lewat konsensus 3 metode statistik. Fokus: menandai yang benar-benar menyimpang.

**Rekomendasi tindakan:**
- Jalankan ingest+analisis berkala (mis. per jam) untuk pemantauan kontinu.
- Sesuaikan ambang (z, EWMA, IQR) sesuai toleransi risiko per sumber.
- Kirim alert ke kanal (email/Telegram) saat anomali severity tinggi muncul.

**⚠️ Risiko bila diabaikan.** Tanpa pemantauan otomatis, penyimpangan penting (lonjakan kurs, anomali harga) baru disadari setelah berdampak. Deteksi dini memungkinkan respons sebelum kerugian membesar.

### 🔵 Methods
**Kesimpulan.** Tiga metode dijalankan paralel: z-score (simpangan), EWMA (pergeseran level), IQR (robust). Anomali FINAL hanya bila ≥2 metode setuju — mengurangi false positive dibanding satu metode saja.

**Rekomendasi tindakan:**
- Percayai anomali yang didukung 2-3 metode; tinjau manual yang didukung 1.
- Untuk domain berbeda, pilih metode dominan yang sesuai (mis. IQR untuk data berekor tebal).
- Audit transparan: setiap anomali menyimpan metode & skor.

**⚠️ Risiko bila diabaikan.** Mengandalkan satu metode berisiko: z-score meledak pada data berekor (banyak false positive), IQR terlalu konservatif pada data musiman. Konsensus meredam kelemahan masing-masing.

<!-- INSIGHTS:END -->

## 👤 Author

<div align="center">

**Sandi Ridwan** — Data Analyst · Automation Architect · Python

📍 Palu, Central Sulawesi, Indonesia

[![Upwork](https://img.shields.io/badge/Upwork-Hire_Me-6A4C93?style=for-the-badge&logo=upwork&logoColor=white)](https://www.upwork.com/freelancers/~011f6d0fbb4a372974)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/sandi-ridwan)

</div>

## 📄 License

MIT — Educational & portfolio. Data dari API publik.
