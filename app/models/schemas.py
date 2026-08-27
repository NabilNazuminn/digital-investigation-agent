"""
Skema data (Pydantic models) untuk Digital Investigation Agent.

Ini adalah "kontrak bentuk data" yang dipakai di seluruh pipeline:
Ingestion & Extraction -> Verification & Enrichment -> Context Analysis (LLM)
-> Risk Scoring -> Report Generation

Kalau bingung alur datanya kemana, cek balik file ini dulu.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. INPUT: apa yang dikirim user ke endpoint /investigate
# ---------------------------------------------------------------------------

class EvidenceType(str, Enum):
    CHAT_TEXT = "chat_text"
    SCREENSHOT = "screenshot"
    URL = "url"
    PHONE_NUMBER = "phone_number"
    BANK_ACCOUNT = "bank_account"
    EMAIL = "email"


class InvestigationRequest(BaseModel):
    """Payload mentah dari user. Semua field optional karena user boleh
    kirim kombinasi apa saja (misal cuma teks chat, atau cuma screenshot)."""

    chat_text: Optional[str] = Field(
        default=None, description="Salinan percakapan / chat log mentah"
    )
    screenshot_base64: Optional[str] = Field(
        default=None, description="Screenshot dalam base64, diproses via OCR"
    )
    urls: List[str] = Field(default_factory=list)
    phone_numbers: List[str] = Field(default_factory=list)
    bank_accounts: List[str] = Field(default_factory=list)
    emails: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 2. HASIL TAHAP INGESTION & EXTRACTION
# ---------------------------------------------------------------------------

class ExtractedEntities(BaseModel):
    """Hasil setelah OCR + entity parsing. Semua entitas sudah dinormalisasi
    (format nomor telepon/rekening seragam, domain sudah diambil dari URL)."""

    ocr_text: Optional[str] = None
    urls: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    phone_numbers: List[str] = Field(default_factory=list)
    bank_accounts: List[str] = Field(default_factory=list)
    emails: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 3. HASIL TAHAP VERIFICATION & ENRICHMENT
# ---------------------------------------------------------------------------

class VerificationStatus(str, Enum):
    VALID = "valid"
    SUSPICIOUS = "suspicious"
    NOT_FOUND = "not_found"
    UNCHECKED = "unchecked"  # dipakai kalau API eksternal timeout/gagal


class DomainCheckResult(BaseModel):
    domain: str
    status: VerificationStatus
    detail: Optional[str] = None  # contoh: "flagged by Safe Browsing"


class BankAccountCheckResult(BaseModel):
    account_number: str
    status: VerificationStatus
    detail: Optional[str] = None  # contoh: "3 laporan penipuan tercatat"


class VerificationResults(BaseModel):
    domain_checks: List[DomainCheckResult] = Field(default_factory=list)
    bank_account_checks: List[BankAccountCheckResult] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 4. UNIFIED CONTEXT PAYLOAD (proposal bab 4.5)
#    Paket gabungan semua hasil sebelum dikirim ke LLM
# ---------------------------------------------------------------------------

class UnifiedContextPayload(BaseModel):
    raw_chat_text: Optional[str] = None
    extracted_entities: ExtractedEntities
    verification_results: VerificationResults


# ---------------------------------------------------------------------------
# 5. HASIL CONTEXT ANALYSIS (LLM)
# ---------------------------------------------------------------------------

class RedFlagType(str, Enum):
    URGENCY_OR_THREAT = "urgency_or_threat"
    UNREALISTIC_OFFER = "unrealistic_offer"
    IDENTITY_IMPERSONATION = "identity_impersonation"
    SUSPICIOUS_DOMAIN = "suspicious_domain"
    FLAGGED_BANK_ACCOUNT = "flagged_bank_account"
    OTHER = "other"


class RedFlag(BaseModel):
    type: RedFlagType
    description: str


class LLMAnalysisResult(BaseModel):
    """Output terstruktur dari LLM setelah menganalisis Unified Context Payload."""

    red_flags: List[RedFlag] = Field(default_factory=list)
    reasoning_summary: str


# ---------------------------------------------------------------------------
# 6. RISK SCORING (fungsi murni Python, bukan LLM — lihat proposal tabel 4.1)
# ---------------------------------------------------------------------------

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class RiskAssessment(BaseModel):
    score: int = Field(ge=0, le=100)
    level: RiskLevel


# ---------------------------------------------------------------------------
# 7. OUTPUT AKHIR: Investigation Report (proposal bab 3.5 & 4.6)
# ---------------------------------------------------------------------------

class InvestigationReport(BaseModel):
    risk_assessment: RiskAssessment
    red_flags: List[RedFlag]
    verified_evidence: VerificationResults
    reasoning_summary: str
    recommendations: List[str]
