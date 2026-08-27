# ini file untuk models nya (Pydantic models) yang dipakai di AI agent

from pydantic import BaseModel, Field
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RedFlagItem(BaseModel):
    type: str = Field(description="Tipe red flag yang terdeteksi")
    description: str = Field(description="Deskripsi spesifik yang mereferensi evidence")
    severity: str = Field(description="low, medium, atau high")
    evidence_reference: str = Field(description="Bukti mana yang mendukung red flag ini")


class InvestigationReport(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    evidence_summary: str
    red_flags: list[RedFlagItem]
    reasoning: str
    recommendation: list[str]
    confidence: Confidence
    missing_evidence: list[str] = Field(default_factory=list)


class UnifiedContext(BaseModel):
    """Struktur data yang diharapkan dari backend FastAPI."""
    conversation_texts: list[str] = Field(default_factory=list)
    extracted_urls: list[str] = Field(default_factory=list)
    extracted_phone_numbers: list[str] = Field(default_factory=list)
    extracted_account_numbers: list[str] = Field(default_factory=list)
    extracted_emails: list[str] = Field(default_factory=list)
    url_check_results: dict = Field(default_factory=dict)
    phone_check_results: dict = Field(default_factory=dict)
    account_check_results: dict = Field(default_factory=dict)
    email_check_results: dict = Field(default_factory=dict)
    ocr_text: str = Field(default="not_available")