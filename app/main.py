from dotenv import load_dotenv

load_dotenv()  # HARUS dipanggil SEBELUM import apapun dari app/,
# karena beberapa modul (misal ai_agent_client.py) baca env var saat di-import.

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers.investigate import router as investigate_router

import logging
import os

logger = logging.getLogger(__name__)

# Redam warning informational dari SDK google-genai soal "Automatic Function
# Calling (AFC)" -- ini bukan error, cuma saran gaya pemakaian API dari
# Google, dan gak ngaruh ke hasil analisis. Diredam biar log server lebih
# bersih. Kalau mau lihat lagi detail log dari SDK ini, ganti level di bawah
# jadi logging.WARNING atau logging.INFO.
logging.getLogger("google_genai").setLevel(logging.ERROR)

app = FastAPI(
    title="Digital Investigation Agent",
    description="AI Agent untuk investigasi awal dugaan penipuan digital",
    version="0.1.0",
)

# CORS: frontend (index.html) dibuka dari origin/port yang beda dari backend
# (misal file:// langsung, atau Live Server di port 5500), jadi browser bakal
# blokir request tanpa header CORS ini. Dibuka lebar (allow_origins=["*"])
# karena ini masih tahap development/hackathon -- kalau nanti sudah deploy ke
# domain tetap, sebaiknya dipersempit ke domain frontend aslinya saja.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(investigate_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Jaring pengaman terakhir -- nangkep error apapun yang gak keprediksi
    di endpoint manapun, supaya frontend SELALU dapet JSON yang rapi
    (bukan halaman error polos/500 kosong). Detail teknisnya tetap dicatat
    di log server (buat kita debug), TIDAK dikirim ke frontend (biar gak
    bocorin detail internal ke user)."""
    logger.exception("Unhandled error di %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Terjadi kesalahan tak terduga di server. Coba lagi, atau hubungi tim backend."},
    )


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health_check():
    """Cek server hidup. Buka http://127.0.0.1:8000/health setelah run."""
    return {"status": "ok"}


# Serve frontend (index.html) langsung dari FastAPI yang sama -- ini KHUSUS
# buat deployment single-service (misal Render), di mana index.html ada di
# folder static/ dan di-serve bareng backend-nya.
#
# Kalau frontend-nya di-serve terpisah sama platform hosting-nya sendiri
# (misal Vercel, yang otomatis serve index.html di root project sebagai
# static file lewat mekanismenya sendiri, TANPA folder static/), folder
# "static/" ini gak bakal ada sama sekali di environment itu. StaticFiles()
# bakal RAISE ERROR kalau folder yang di-mount gak ketemu -- makanya di-cek
# dulu keberadaannya sebelum di-mount, biar main.py yang SAMA bisa dipakai
# di kedua jenis deployment tanpa perlu diubah manual tiap pindah platform.
#
# HARUS didaftarkan PALING TERAKHIR (setelah semua route API di atas),
# karena StaticFiles(html=True) yang di-mount di "/" itu semacam catch-all --
# kalau didaftarkan duluan, dia bakal "nyamber" semua request sebelum sempat
# ke route API manapun.
if os.path.isdir("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")