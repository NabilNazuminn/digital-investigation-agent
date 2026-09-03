from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import logging

from app.database import get_db
from app.models.schemas import InvestigationRequest
from app.services.ai_agent_client import run_investigation
from app.services.evidence_aggregator import build_unified_context
from app.services.external_checker import run_external_checks
from app.services.file_storage import save_screenshot
from app.services.history_repository import get_investigation, list_investigations, save_investigation
from app.services.information_extractor import extract_all_entities
from app.services.ocr_processor import OCRError, extract_text_from_screenshot
from app.services.validation import ValidationError, validate_request

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/investigate")
def investigate(req: InvestigationRequest, db: Session = Depends(get_db)):
    """Endpoint utama. Alur saat ini: validasi -> (simpan screenshot) -> aggregate
    -> panggil AI Agent -> simpan hasil ke database -> return ke frontend.

    TODO(step 3): ganti ExtractedEntities/VerificationResults kosong di bawah
    dengan hasil OCR + entity parsing + cek reputasi eksternal yang sebenarnya.
    Untuk sekarang, urls/phone_numbers/bank_accounts/emails yang user kirim
    manual sudah dipakai langsung (belum lewat OCR)."""

    try:
        validate_request(req)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    screenshot_path = save_screenshot(req.screenshot_base64) if req.screenshot_base64 else None

    ocr_text: Optional[str] = None
    ocr_warning: Optional[str] = None
    if req.screenshot_base64:
        try:
            ocr_text = extract_text_from_screenshot(req.screenshot_base64)
        except OCRError as exc:
            # Sengaja TIDAK menggagalkan seluruh request kalau OCR error (misal
            # API key belum diisi) -- tetap lanjut pakai chat_text/input manual
            # yang ada, sesuai proposal 4.7 (degradasi, bukan hard-fail).
            ocr_warning = str(exc)

    extracted = extract_all_entities(
        chat_text=req.chat_text,
        ocr_text=ocr_text,
        manual_urls=req.urls,
        manual_phone_numbers=req.phone_numbers,
        manual_bank_accounts=req.bank_accounts,
        manual_emails=req.emails,
    )
    verification = run_external_checks(
        urls=extracted.urls,
        bank_accounts=extracted.bank_accounts,
    )

    context = build_unified_context(req.chat_text, extracted, verification)
    report = run_investigation(context)

    # Hasil analisis AI ini sudah "jadi" -- jangan sampai gagal simpan ke
    # riwayat (misal koneksi DB Neon sempat putus) bikin hasil yang sudah
    # sukses ini ikut ke-buang jadi error 500 ke frontend. Simpan ke DB tetap
    # dicoba, tapi kalau gagal, tetap return laporan aslinya ke user --
    # cuma dikasih tanda kalau riwayatnya gak sempat kesimpan.
    try:
        save_investigation(db, req.chat_text, screenshot_path, report)
    except Exception as exc:  # noqa: BLE001 -- sengaja luas, ini fallback terakhir biar hasil AI gak hilang
        logger.error("Gagal simpan riwayat investigasi ke database: %s", exc)
        db.rollback()
        report["history_saved"] = False
        report["history_warning"] = "Hasil analisis berhasil, tapi gagal disimpan ke riwayat (masalah koneksi database)."

    if ocr_warning:
        report["ocr_warning"] = ocr_warning  # info transparansi ke frontend, bukan error fatal

    return report


@router.get("/investigations")
def get_history(limit: int = 20, db: Session = Depends(get_db)):
    """Riwayat investigasi terbaru, buat halaman 'Riwayat Investigasi' di frontend."""
    records = list_investigations(db, limit=limit)
    return [
        {
            "id": r.id,
            "created_at": r.created_at,
            "chat_text_snippet": r.chat_text_snippet,
            "risk_score": r.risk_score,
            "risk_level": r.risk_level,
        }
        for r in records
    ]


@router.get("/investigations/{investigation_id}")
def get_history_detail(investigation_id: str, db: Session = Depends(get_db)):
    """Detail lengkap 1 hasil investigasi (termasuk full report dari AI Agent)."""
    record = get_investigation(db, investigation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Investigasi tidak ditemukan.")
    return {
        "id": record.id,
        "created_at": record.created_at,
        "chat_text_snippet": record.chat_text_snippet,
        "screenshot_path": record.screenshot_path,
        "report": record.full_report,
    }
