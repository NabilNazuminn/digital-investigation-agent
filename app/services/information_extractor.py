"""
Information Extractor (box 4 di diagram arsitektur).

Tugasnya: dari teks mentah (chat_text dan/atau ocr_text), temukan entitas
penting -- URL, domain, nomor telepon, nomor rekening, email -- pakai regex.
Ini murni pattern matching, BUKAN AI/LLM (itu tugas AI Agent di step selanjutnya).

Batasan yang perlu disadari (biar gak kaget pas testing/demo):
- Nomor rekening SUSAH dibedakan dari angka lain secara pasti pakai regex
  saja (gak ada format baku antar bank). Fungsi di bawah pakai heuristik:
  urutan 9-16 digit yang BUKAN nomor telepon. Ini akan ada false positive/
  false negative -- normal untuk pendekatan regex, dan proposal sendiri
  sudah mengakui verifikasi rekening masih pakai data simulasi.
- Regex ini didesain untuk pola Indonesia (nomor HP awalan 08/+62).
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from app.models.schemas import ExtractedEntities

URL_PATTERN = re.compile(r"https?://[^\s<>\"']+")
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_PATTERN = re.compile(r"(?:\+62|62|0)8[1-9][0-9]{6,10}")
# Urutan 9-16 digit (boleh ada spasi/strip di sela), dipakai sebagai kandidat nomor rekening
ACCOUNT_CANDIDATE_PATTERN = re.compile(r"\b\d[\d\s-]{7,15}\d\b")


def _dedupe(items: list[str]) -> list[str]:
    """Hilangkan duplikat, tetap jaga urutan kemunculan pertama."""
    return list(dict.fromkeys(items))


def _extract_domain(url: str) -> str | None:
    try:
        netloc = urlparse(url).netloc
        return netloc or None
    except ValueError:
        return None


def extract_entities_from_text(text: str) -> ExtractedEntities:
    """Ekstrak semua entitas dari SATU string teks (chat_text atau ocr_text)."""
    urls = _dedupe(URL_PATTERN.findall(text))
    domains = _dedupe([d for u in urls if (d := _extract_domain(u))])
    emails = _dedupe(EMAIL_PATTERN.findall(text))
    phones = _dedupe(PHONE_PATTERN.findall(text))

    # Kandidat rekening: urutan digit yang BUKAN nomor telepon (biar gak dobel-hitung)
    phone_spans = {m.span() for m in PHONE_PATTERN.finditer(text)}
    account_candidates = []
    for m in ACCOUNT_CANDIDATE_PATTERN.finditer(text):
        if m.span() in phone_spans:
            continue
        cleaned = re.sub(r"[\s-]", "", m.group())
        if 9 <= len(cleaned) <= 16:
            account_candidates.append(cleaned)

    return ExtractedEntities(
        urls=urls,
        domains=domains,
        phone_numbers=phones,
        bank_accounts=_dedupe(account_candidates),
        emails=emails,
    )


def merge_with_manual_input(
    auto: ExtractedEntities,
    manual_urls: list[str],
    manual_phone_numbers: list[str],
    manual_bank_accounts: list[str],
    manual_emails: list[str],
) -> ExtractedEntities:
    """Gabungkan hasil auto-extract dengan entitas yang user isi manual di form
    (kalau ada). User-provided dianggap lebih terpercaya, jadi ditaruh duluan."""
    return ExtractedEntities(
        ocr_text=auto.ocr_text,
        urls=_dedupe(manual_urls + auto.urls),
        domains=auto.domains,
        phone_numbers=_dedupe(manual_phone_numbers + auto.phone_numbers),
        bank_accounts=_dedupe(manual_bank_accounts + auto.bank_accounts),
        emails=_dedupe(manual_emails + auto.emails),
    )


def extract_all_entities(
    chat_text: str | None,
    ocr_text: str | None,
    manual_urls: list[str] | None = None,
    manual_phone_numbers: list[str] | None = None,
    manual_bank_accounts: list[str] | None = None,
    manual_emails: list[str] | None = None,
) -> ExtractedEntities:
    """Entry point utama dipanggil dari endpoint: gabungkan chat_text + ocr_text
    + input manual jadi satu ExtractedEntities."""
    combined_text = " ".join(filter(None, [chat_text, ocr_text]))
    auto = extract_entities_from_text(combined_text)
    auto.ocr_text = ocr_text

    return merge_with_manual_input(
        auto,
        manual_urls or [],
        manual_phone_numbers or [],
        manual_bank_accounts or [],
        manual_emails or [],
    )
