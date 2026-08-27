"""
Evidence Aggregator (box 6 di diagram arsitektur).

Tugasnya SATU: mengubah data yang sudah dikumpulkan modul-modul Nabil
(OCR, ekstraksi entitas, hasil cek eksternal) menjadi bentuk `UnifiedContext`
yang PERSIS sesuai kontrak AI Agent milik team leader (lihat ai_agent/models.py).

Kalau nanti ada error "field tidak dikenali" atau semacamnya saat manggil
AI Agent, cek dulu di sini — kemungkinan besar sumbernya di fungsi ini.
"""

from __future__ import annotations

from ai_agent.models import UnifiedContext

from app.models.schemas import ExtractedEntities, VerificationResults


def _domain_checks_to_dict(verification: VerificationResults) -> dict:
    """AI Agent minta url_check_results sebagai dict, bukan list -> ubah bentuknya."""
    return {
        check.domain: {"status": check.status.value, "detail": check.detail}
        for check in verification.domain_checks
    }


def _account_checks_to_dict(verification: VerificationResults) -> dict:
    return {
        check.account_number: {"status": check.status.value, "detail": check.detail}
        for check in verification.bank_account_checks
    }


def build_unified_context(
    chat_text: str | None,
    extracted: ExtractedEntities,
    verification: VerificationResults,
) -> UnifiedContext:
    """Rakit semua evidence jadi satu UnifiedContext siap dikirim ke AI Agent.

    Nabil belum punya modul phone/email checker eksternal (belum ada di proposal),
    jadi phone_check_results & email_check_results sengaja dikosongkan (dict kosong)
    dulu -- AI Agent tetap bisa jalan tanpa itu, cuma confidence-nya mungkin lebih rendah.
    """
    return UnifiedContext(
        conversation_texts=[chat_text] if chat_text else [],
        extracted_urls=extracted.urls,
        extracted_phone_numbers=extracted.phone_numbers,
        extracted_account_numbers=extracted.bank_accounts,
        extracted_emails=extracted.emails,
        url_check_results=_domain_checks_to_dict(verification),
        phone_check_results={},
        account_check_results=_account_checks_to_dict(verification),
        email_check_results={},
        ocr_text=extracted.ocr_text or "not_available",
    )
