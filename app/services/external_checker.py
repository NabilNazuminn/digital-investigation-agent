"""
External Checker (box 5 di diagram arsitektur).

Dua sumber cek reputasi:
1. URL/domain -> Google Safe Browsing API (ASLI, API gratis dari Google).
2. Nomor rekening -> data SIMULASI (bukan API asli), karena cekrekening.id
   tidak punya API publik resmi -- proposal sendiri sudah mengakui
   keterbatasan ini di bab 4.2.

Kalau Safe Browsing API gagal (timeout, key salah, kuota habis), status
dikembalikan sebagai UNCHECKED (bukan error yang menggagalkan seluruh
request) -- konsisten dengan filosofi error handling proposal 4.7:
sistem harus tetap jalan dalam mode degradasi, bukan collapse total.
"""

from __future__ import annotations

import logging
import os
from urllib.parse import urlparse

import httpx

from app.models.schemas import (
    BankAccountCheckResult,
    DomainCheckResult,
    VerificationResults,
    VerificationStatus,
)

logger = logging.getLogger(__name__)

SAFE_BROWSING_URL = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
SAFE_BROWSING_TIMEOUT_SECONDS = 5.0

# Data simulasi -- daftar nomor rekening "contoh" yang dianggap sudah pernah
# dilaporkan, dipakai untuk demo/testing selama belum ada API rekening resmi.
# Ganti/lengkapi sesuai skenario uji di proposal (tabel 4.2) kalau perlu.
SIMULATED_FLAGGED_ACCOUNTS = {
    "1234567890123": "Tercatat 3 laporan penipuan (data simulasi)",
    "9876543210": "Tercatat 1 laporan penipuan (data simulasi)",
}


def _domain_from_url(url: str) -> str:
    return urlparse(url).netloc or url


def check_urls(urls: list[str]) -> list[DomainCheckResult]:
    """Cek reputasi tiap URL ke Google Safe Browsing. 1 request untuk semua
    URL sekaligus (lebih efisien daripada 1 request per URL)."""
    if not urls:
        return []

    api_key = os.getenv("GOOGLE_SAFE_BROWSING_API_KEY")
    if not api_key:
        return [
            DomainCheckResult(
                domain=_domain_from_url(u),
                status=VerificationStatus.UNCHECKED,
                detail="GOOGLE_SAFE_BROWSING_API_KEY tidak ditemukan.",
            )
            for u in urls
        ]

    payload = {
        "client": {"clientId": "digital-investigation-agent", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": [
                "MALWARE",
                "SOCIAL_ENGINEERING",
                "UNWANTED_SOFTWARE",
                "POTENTIALLY_HARMFUL_APPLICATION",
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": u} for u in urls],
        },
    }

    try:
        response = httpx.post(
            SAFE_BROWSING_URL,
            params={"key": api_key},
            json=payload,
            timeout=SAFE_BROWSING_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        logger.warning("Safe Browsing API gagal: %s", exc)
        return [
            DomainCheckResult(
                domain=_domain_from_url(u),
                status=VerificationStatus.UNCHECKED,
                detail=f"Safe Browsing API gagal: {exc}",
            )
            for u in urls
        ]

    flagged_urls = {match["threat"]["url"] for match in data.get("matches", [])}

    return [
        DomainCheckResult(
            domain=_domain_from_url(u),
            status=VerificationStatus.SUSPICIOUS if u in flagged_urls else VerificationStatus.VALID,
            detail="Ditandai berbahaya oleh Google Safe Browsing." if u in flagged_urls else None,
        )
        for u in urls
    ]


def check_bank_accounts(account_numbers: list[str]) -> list[BankAccountCheckResult]:
    """Cek rekening ke data SIMULASI (bukan API asli -- lihat docstring di atas)."""
    results = []
    for acc in account_numbers:
        if acc in SIMULATED_FLAGGED_ACCOUNTS:
            results.append(
                BankAccountCheckResult(
                    account_number=acc,
                    status=VerificationStatus.SUSPICIOUS,
                    detail=SIMULATED_FLAGGED_ACCOUNTS[acc],
                )
            )
        else:
            results.append(
                BankAccountCheckResult(
                    account_number=acc,
                    status=VerificationStatus.NOT_FOUND,
                    detail="Tidak ditemukan di data simulasi (bukan berarti aman -- cekrekening.id tidak punya API publik).",
                )
            )
    return results


def run_external_checks(urls: list[str], bank_accounts: list[str]) -> VerificationResults:
    """Entry point utama dipanggil dari endpoint."""
    return VerificationResults(
        domain_checks=check_urls(urls),
        bank_account_checks=check_bank_accounts(bank_accounts),
    )
