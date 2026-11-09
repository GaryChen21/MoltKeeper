# 🕷️ MoltKeeper — Jurnal Digital Siklus Molt Tarantula

**UTS Cloud Services — Multi-tier Web App (FastAPI + PostgreSQL + Docker)**

## Ide Proyek: Kenapa Unik?

MoltKeeper adalah **jurnal pencatatan siklus molt (ganti kulit) tarantula** —
ritual paling kritis dalam pemeliharaan tarantula. Saat molt, tarantula
sangat rapuh: harus puasa, tidak boleh diganggu, fangs baru perlu waktu
mengeras sebelum diberi pakan, dan pertumbuhan ukuran (leg span) hanya
bisa diukur tepat setelah molt.

Aplikasi seperti ini nyata dibutuhkan komunitas *hobbyist* tarantula, tetapi
hampir tidak ada yang dibuat secara khusus — jauh dari tema umum seperti
to-do list, e-commerce, atau blog. Setiap catatan molt (instar, leg span,
tanggal, catatan pasca-molt) tersimpan di PostgreSQL dan ditampilkan
melalui frontend web yang berbicara langsung dengan API backend.

## Fitur

- **GET /health** — status aplikasi + koneksi database (dipakai healthcheck)
- **GET /baca-data** — mengambil seluruh riwayat molt dari PostgreSQL
- **POST /tulis-data** — menyimpan satu catatan molt baru
- Frontend HTML/JS memanggil ketiga endpoint tersebut (polling status tiap 30 detik)
- Data bertahan antar restart container berkat **named volume**
- Tabel `catatan_molt` dibuat otomatis saat aplikasi start

## Arsitektur

```
[ Browser ]
     │  HTTP :8000
     ▼
[ service app — FastAPI/uvicorn ]        ┌────────────────────┐
   - Dockerfile multi-stage              │  [ service db ]    │
   - serve frontend statis + API         │  postgres:16.4     │
     ▼  psycopg (connection pool)        │  + healthcheck     │
     └────────── jaringan-moltkeeper ───▶│  + named volume    │
              (user-defined bridge)      └────────────────────┘
```

## Struktur Proyek

```
.
├── backend/
│   ├── main.py           # FastAPI: /health, /baca-data, /tulis-data
│   └── requirements.txt  # dependencies ter-pin versi
├── frontend/
│   └── index.html        # UI HTML/CSS/JS (dipanggil sebagai /static)
├── Dockerfile            # multi-stage build + komentar
├── docker-compose.yml    # 2 service, network, volume, healthcheck
├── .env                  # konfigurasi database (JANGAN di-commit asli)
├── .env.example          # template .env
└── .dockerignore
```

## Cara Menjalankan

Prasyarat: Docker Engine + Docker Compose v2.

```bash
# 1. Siapkan environment
cp .env.example .env     # lalu ubah password di dalamnya

# 2. Build + jalankan (app menunggu db sehat dulu)
docker compose up --build -d

# 3. Buka aplikasi
#    http://localhost:8000
#    Dokumentasi API otomatis: http://localhost:8000/docs

# 4. Cek log / status health
docker compose ps
docker compose logs -f app

# 5. Berhenti (data tetap aman di named volume pgdata)
docker compose down
```

## Endpoint

| Method | Path         | Fungsi                                          |
|--------|--------------|--------------------------------------------------|
| GET    | `/health`    | Cek API + koneksi PostgreSQL                     |
| GET    | `/baca-data` | Daftar semua catatan molt (urut terbaru)         |
| POST   | `/tulis-data`| Simpan catatan baru (JSON, validasi via Pydantic)|

Contoh POST:

```bash
curl -X POST http://localhost:8000/tulis-data \
  -H "Content-Type: application/json" \
  -d '{"nama_tarantula":"Mochnacz","spesies":"Grammostola pulchripes","instar":"7Fi","leg_span_cm":6.5,"tanggal_molt":"2026-11-09","catatan":"fangs baru, belum feeding"}'
```

## Detail Teknis yang Dipenuhi

**Dockerfile (multi-stage):**
- Base image `python:3.12.7-slim-bookworm` — tag versi spesifik, bukan `latest`
- Stage `builder`: install dependencies ke `/install` (dependency disalin sebelum source code → layer cache efektif)
- Stage `runtime`: hanya menyalin hasil build + source code, non-root user, `EXPOSE`, `HEALTHCHECK`
- `CMD` format exec (JSON array) → uvicorn sebagai PID 1 yang menerima SIGTERM dengan benar

**docker-compose.yml:**
- 2 service: `app` (FastAPI) dan `db` (PostgreSQL)
- User-defined network `jaringan-moltkeeper` (app memanggil db via nama service)
- Named volume `pgdata` untuk persistensi data
- Healthcheck database dengan `pg_isready`
- `depends_on: condition: service_healthy` → app menunggu db **benar-benar siap**
- Memuat file `.env` (`env_file` + interpolasi variabel)

## Teknologi

Python 3.12 · FastAPI · psycopg 3 (pool) · PostgreSQL 16 · Docker (multi-stage) · HTML/CSS/JS vanilla

---

## AI Usage Declaration

> Bagian ini mendeklarasikan penggunaan AI dalam pengerjaan UTS secara jujur sesuai proses yang benar-benar terjadi, dengan cakupan maksimal 50% dari total pengerjaan.

Saya menggunakan bantuan AI (**Claude Opus 5.5**) dalam pengerjaan UTS ini dengan cakupan sebagai berikut:

1. **Brainstorming ide proyek** – AI membantu menghasilkan dan mengevaluasi beberapa kandidat ide *niche*. Ide akhir **MoltKeeper (jurnal molt tarantula)** dipilih dari hasil diskusi tersebut karena unik dan spesifik.
2. **Boilerplate kode aplikasi** – AI membantu menyusun kerangka awal kode logika *backend* (FastAPI) dan tampilan *frontend* (HTML/JS) sederhana.

**Contoh Prompt Utama yang Digunakan:**
> *"Bertindaklah sebagai Fullstack Developer. Bantu saya membuat proyek Web App multi-tier. Berikan 1 ide proyek yang SANGAT UNIK dan anti-mainstream (jangan Task Manager/E-commerce). Buatkan juga boilerplate kode dasar untuk backend FastAPI (dengan 3 endpoint: GET /health, GET, POST) dan frontend HTML sederhana."*

**Pernyataan Independensi Infrastruktur:**
Seluruh bagian *containerization* yang menjadi kompetensi inti mata kuliah ini—termasuk merancang arsitektur container, menulis setiap baris `Dockerfile` (multi-stage build), menyusun konfigurasi `docker-compose.yml` (network, volume, healthcheck), dan menghubungkannya dengan database PostgreSQL—**murni saya kerjakan dan integrasikan sendiri secara manual** tanpa bantuan AI, lalu saya sesuaikan agar berjalan lancar di mesin *localhost* saya.