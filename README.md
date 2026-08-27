# Digital Investigation Agent — Backend

Backend FastAPI untuk BISA AI National AI Agent Challenge 2026.
Tugas backend ini: terima bukti dari user, proses (OCR, ekstraksi, cek
reputasi), lalu panggil AI Agent (dibuat rekan tim) untuk analisis & risk
scoring, dan kembalikan hasilnya.

## Struktur folder

```
digital-investigation-agent/
├── app/                        <- Punya Nabil (backend)
│   ├── main.py                 <- Entry point FastAPI
│   ├── models/
│   │   └── schemas.py          <- Bentuk data (Pydantic) untuk input & hasil ekstraksi
│   ├── routers/
│   │   └── investigate.py      <- Endpoint POST /investigate
│   └── services/
│       ├── validation.py       <- Validasi input (box 2: Data Validation)
│       ├── evidence_aggregator.py  <- Susun evidence jadi UnifiedContext (box 6)
│       └── ai_agent_client.py  <- Panggil AI Agent (asli / stub)
│
├── ai_agent/                   <- Punya team leader (JANGAN diedit di sini,
│                                    kalau ada update minta zip baru & timpa folder ini)
│   ├── agent.py                <- Entry point AI Agent
│   ├── models.py                <- Bentuk data UnifiedContext & InvestigationReport
│   └── ...
│
├── requirements.txt
├── .env.example                <- Salin jadi .env, isi API key
└── .gitignore
```

## Modul yang masih perlu dibuat (lihat services/)

- `ocr_processor.py` — box 3, baca teks dari screenshot
- `information_extractor.py` — box 4, ekstrak URL/rekening/telepon/email dari teks
- `external_checker.py` — box 5, cek reputasi ke Google Safe Browsing dkk
- `database.py` — koneksi PostgreSQL untuk simpan riwayat investigasi
- `file_storage.py` — simpan screenshot yang diupload user

## Cara jalanin

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # lalu isi API key di dalamnya
uvicorn app.main:app --reload
```

Buka `http://127.0.0.1:8000/docs` untuk halaman testing endpoint interaktif.

## Mode stub (dev tanpa API key)

Selama `USE_AI_AGENT_STUB=true` di `.env`, endpoint `/investigate` akan
mengembalikan hasil dummy (bentuknya tetap sama persis dengan hasil asli)
tanpa perlu `GEMINI_API_KEY`. Ganti ke `false` kalau sudah siap pakai AI
Agent + Gemini beneran.
