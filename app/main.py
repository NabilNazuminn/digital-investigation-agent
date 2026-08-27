from dotenv import load_dotenv

load_dotenv()  # HARUS dipanggil SEBELUM import apapun dari app/,
# karena beberapa modul (misal ai_agent_client.py) baca env var saat di-import.

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import init_db
from app.routers.investigate import router as investigate_router

import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Digital Investigation Agent",
    description="AI Agent untuk investigasi awal dugaan penipuan digital",
    version="0.1.0",
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
