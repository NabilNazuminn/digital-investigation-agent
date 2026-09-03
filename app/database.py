"""
Koneksi database (PostgreSQL). Pakai SQLAlchemy supaya kode ini generik --
tinggal ganti DATABASE_URL di .env, gak perlu ubah kode.

Untuk development kalau belum sempat setup Postgres beneran, bisa
sementara pakai SQLite (lihat .env.example) -- SQLAlchemy tetap jalan sama.
"""

from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./dev.db"
# Sengaja pakai "or", BUKAN os.getenv(key, default) -- soalnya kalau DATABASE_URL=
# ada di .env tapi dikosongin, os.getenv bakal balikin string kosong "" (bukan
# None), dan default di os.getenv cuma kepake kalau key-nya BENERAN gak ada
# sama sekali. "or" ini yang bikin string kosong ikut ke-fallback juga.

# connect_args ini cuma dibutuhkan SQLite, diabaikan kalau pakai Postgres beneran
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# pool_pre_ping=True: SQLAlchemy ngecek dulu koneksi masih hidup sebelum
# dipakai, dan otomatis bikin koneksi baru kalau ternyata udah mati --
# penting buat Postgres serverless kayak Neon yang suka nutup/suspend
# koneksi yang nganggur, biar gak muncul error
# "psycopg2.OperationalError: could not receive data from server".
# pool_recycle=300: paksa bikin ulang koneksi tiap 5 menit biar gak sempat
# jadi stale duluan sebelum pre_ping sempat ngecek (diabaikan buat SQLite).
engine_kwargs = {"pool_pre_ping": True}
if not DATABASE_URL.startswith("sqlite"):
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(DATABASE_URL, connect_args=connect_args, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Semua model tabel (lihat db_models.py) turunan dari ini."""


def get_db():
    """Dependency FastAPI: kasih 1 session per request, otomatis ditutup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Bikin semua tabel kalau belum ada. Dipanggil sekali saat startup.

    Catatan: ini cara simpel buat hackathon (belum pakai Alembic/migration
    tool). Kalau nanti struktur tabel berubah drastis setelah ada data
    penting, perlu approach migration yang lebih hati-hati."""
    import app.models.db_models  # noqa: F401  (registrasi model ke Base.metadata)

    Base.metadata.create_all(bind=engine)