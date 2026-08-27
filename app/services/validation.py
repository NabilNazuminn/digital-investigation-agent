"""
Validasi & sanitasi input awal (proposal bab 4.3).

Semua fungsi di sini murni Python (gak manggil LLM atau API luar) —
tugasnya cuma mastiin data yang masuk masuk akal sebelum diproses lebih jauh.
"""

from __future__ import annotations

import base64
import binascii
from typing import List

from app.models.schemas import EvidenceType, InvestigationRequest

MAX_SCREENSHOT_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB, sesuaikan kalau perlu
ALLOWED_IMAGE_PREFIXES = ("data:image/png", "data:image/jpg", "data:image/jpeg")


class ValidationError(Exception):
    """Dilempar kalau input gagal validasi. Pesannya langsung bisa
    ditampilkan ke user (bahasa Indonesia, jelas apa yang salah)."""


def has_any_evidence(req: InvestigationRequest) -> bool:
    """Cek apakah user ngirim setidaknya satu jenis bukti."""
    return any(
        [
            req.chat_text,
            req.screenshot_base64,
            req.urls,
            req.phone_numbers,
            req.bank_accounts,
            req.emails,
        ]
    )


def validate_screenshot(screenshot_base64: str) -> None:
    """Cek format & ukuran screenshot. Raise ValidationError kalau gak valid."""
    if not screenshot_base64.startswith(ALLOWED_IMAGE_PREFIXES):
        raise ValidationError(
            "Format gambar tidak didukung. Gunakan PNG, JPG, atau JPEG."
        )

    # Pisahkan header data URI ("data:image/png;base64,") dari data aslinya
    try:
        _, encoded_data = screenshot_base64.split(",", 1)
        raw_bytes = base64.b64decode(encoded_data, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValidationError(
            "Data gambar rusak atau tidak bisa dibaca. Coba upload ulang."
        ) from exc

    if len(raw_bytes) > MAX_SCREENSHOT_SIZE_BYTES:
        raise ValidationError(
            f"Ukuran gambar melebihi batas {MAX_SCREENSHOT_SIZE_BYTES // (1024 * 1024)} MB."
        )


def validate_request(req: InvestigationRequest) -> None:
    """Validasi utama yang dipanggil endpoint. Raise ValidationError kalau invalid."""
    if not has_any_evidence(req):
        raise ValidationError(
            "Tidak ada bukti yang diberikan. Sertakan minimal salah satu: "
            "teks chat, screenshot, URL, nomor telepon, atau nomor rekening."
        )

    if req.screenshot_base64:
        validate_screenshot(req.screenshot_base64)


def classify_evidence_types(req: InvestigationRequest) -> List[EvidenceType]:
    """Tentukan jenis-jenis bukti apa saja yang ada di request ini.
    Dipakai orchestrator nanti buat tau modul mana yang perlu dipanggil."""
    types: List[EvidenceType] = []
    if req.chat_text:
        types.append(EvidenceType.CHAT_TEXT)
    if req.screenshot_base64:
        types.append(EvidenceType.SCREENSHOT)
    if req.urls:
        types.append(EvidenceType.URL)
    if req.phone_numbers:
        types.append(EvidenceType.PHONE_NUMBER)
    if req.bank_accounts:
        types.append(EvidenceType.BANK_ACCOUNT)
    if req.emails:
        types.append(EvidenceType.EMAIL)
    return types
