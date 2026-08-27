"""
File Storage -- simpan screenshot yang diupload user ke disk lokal.

Untuk hackathon ini disimpan di folder lokal (cukup buat demo). Kalau nanti
butuh production beneran (misal deploy ke Render, disk-nya bisa kehapus
tiap deploy ulang), baru pertimbangkan cloud storage (S3-compatible, dll)
-- tapi itu bukan prioritas 3 minggu ini.
"""

from __future__ import annotations

import base64
import binascii
import uuid
from pathlib import Path

STORAGE_DIR = Path("storage/screenshots")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

EXTENSION_BY_PREFIX = {
    "data:image/png": "png",
    "data:image/jpg": "jpg",
    "data:image/jpeg": "jpg",
}


def save_screenshot(screenshot_base64: str) -> str:
    """Simpan screenshot base64 ke disk, return path filenya (relative).

    Asumsi: `screenshot_base64` sudah lolos validasi di validation.py
    (format & ukuran sudah dicek di sana)."""
    prefix, encoded_data = screenshot_base64.split(",", 1)
    extension = EXTENSION_BY_PREFIX.get(prefix, "bin")

    filename = f"{uuid.uuid4()}.{extension}"
    filepath = STORAGE_DIR / filename

    try:
        raw_bytes = base64.b64decode(encoded_data, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Gagal decode screenshot -- pastikan sudah divalidasi dulu.") from exc

    filepath.write_bytes(raw_bytes)
    return str(filepath)
