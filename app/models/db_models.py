from typing import Optional
"""
Model tabel database (SQLAlchemy ORM) -- BEDA dari schemas.py yang isinya
Pydantic (buat validasi request/response API).

InvestigationRecord = 1 baris = 1 hasil investigasi yang pernah dijalankan,
dipakai buat fitur "Riwayat Investigasi" di frontend.
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InvestigationRecord(Base):
    __tablename__ = "investigation_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    # Ringkasan input, biar gampang ditampilkan di daftar riwayat tanpa buka detail
    chat_text_snippet: Optional[Mapped[str]] = mapped_column(String, nullable=True)
    screenshot_path: Optional[Mapped[str]] = mapped_column(String, nullable=True)

    # Hasil dari AI Agent
    risk_score: Mapped[int] = mapped_column(Integer)
    risk_level: Mapped[str] = mapped_column(String)
    full_report: Mapped[dict] = mapped_column(JSON)  # simpan seluruh InvestigationReport asli
