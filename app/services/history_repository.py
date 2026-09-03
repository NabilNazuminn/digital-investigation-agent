"""
History Repository -- fungsi buat simpan & ambil riwayat investigasi dari
database. Endpoint (investigate.py) manggil fungsi-fungsi di sini, gak
perlu tau detail SQLAlchemy-nya langsung.
"""

from __future__ import annotations

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.db_models import InvestigationRecord


def save_investigation(
    db: Session,
    chat_text: str | None,
    screenshot_path: str | None,
    report: dict,
) -> InvestigationRecord:
    """Simpan 1 hasil investigasi ke database. `report` = dict hasil dari
    ai_agent_client.run_investigation() (sudah berisi risk_score, risk_level, dll)."""
    snippet = (chat_text or "")[:200] or None  # simpan cuplikan aja, biar hemat

    record = InvestigationRecord(
        chat_text_snippet=snippet,
        screenshot_path=screenshot_path,
        risk_score=report["risk_score"],
        risk_level=report["risk_level"],
        full_report=report,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_investigations(db: Session, limit: int = 20) -> list[InvestigationRecord]:
    """Ambil riwayat investigasi terbaru, buat halaman 'Riwayat Investigasi'."""
    return (
        db.query(InvestigationRecord)
        .order_by(desc(InvestigationRecord.created_at))
        .limit(limit)
        .all()
    )


def get_investigation(db: Session, investigation_id: str) -> InvestigationRecord | None:
    """Ambil 1 hasil investigasi lengkap berdasarkan id."""
    return db.query(InvestigationRecord).filter(InvestigationRecord.id == investigation_id).first()


def delete_investigation(db: Session, investigation_id: str) -> bool:
    """Hapus 1 riwayat investigasi berdasarkan id. Return True kalau berhasil dihapus,
    False kalau id tidak ditemukan."""
    record = get_investigation(db, investigation_id)
    if record is None:
        return False
    db.delete(record)
    db.commit()
    return True


def delete_investigations_by_ids(db: Session, ids: list[str]) -> int:
    """Hapus sejumlah riwayat investigasi berdasarkan daftar id.
    Return jumlah record yang berhasil dihapus."""
    deleted = (
        db.query(InvestigationRecord)
        .filter(InvestigationRecord.id.in_(ids))
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted


def delete_all_investigations(db: Session) -> int:
    """Hapus SEMUA riwayat investigasi. Return jumlah record yang dihapus."""
    deleted = db.query(InvestigationRecord).delete(synchronize_session=False)
    db.commit()
    return deleted
