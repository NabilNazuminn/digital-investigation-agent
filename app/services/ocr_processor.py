"""
OCR Processor (box 3 di diagram arsitektur).

Tugasnya: baca teks yang ada di dalam gambar screenshot (misal isi chat WhatsApp
yang di-screenshot, bukan di-paste sebagai teks). Hasilnya (ocr_text) nanti
digabung sama chat_text di Information Extractor (box 4) buat dicari
URL/rekening/telepon/email-nya.

Pakai Gemini Vision (bukan Tesseract) sesuai pilihan di diagram arsitektur tim
--  lebih gampang setup (gak perlu install program OCR terpisah di sistem,
cukup modal API key yang sama dengan AI Agent), dan lebih akurat baca teks
dari screenshot chat yang kadang miring/blur/ada emoji.
"""

from __future__ import annotations

import base64
import binascii
import logging
import os

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Model ringan & cepat, cukup untuk baca teks -- gak perlu model "berpikir" mahal untuk OCR
OCR_MODEL_NAME = os.getenv("GEMINI_OCR_MODEL", "gemini-2.0-flash")

OCR_PROMPT = (
    "Ekstrak SEMUA teks yang terlihat pada gambar ini apa adanya (verbatim), "
    "termasuk nama pengirim, isi pesan, nomor, link, dan timestamp kalau ada. "
    "Jangan tambahkan komentar, penjelasan, atau opini apapun -- kembalikan "
    "teksnya saja persis seperti yang tertulis di gambar."
)

MIME_TYPE_BY_PREFIX = {
    "data:image/png": "image/png",
    "data:image/jpg": "image/jpeg",
    "data:image/jpeg": "image/jpeg",
}


class OCRError(Exception):
    """Dilempar kalau OCR gagal total (misal API key salah, atau gambar rusak)."""


def _decode_screenshot(screenshot_base64: str) -> tuple[bytes, str]:
    prefix, encoded_data = screenshot_base64.split(",", 1)
    mime_type = MIME_TYPE_BY_PREFIX.get(prefix, "image/png")
    try:
        raw_bytes = base64.b64decode(encoded_data, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise OCRError("Data gambar rusak, tidak bisa didecode.") from exc
    return raw_bytes, mime_type


def extract_text_from_screenshot(screenshot_base64: str) -> str:
    """Panggil Gemini Vision untuk baca teks dari screenshot.
    Raise OCRError kalau gagal -- endpoint yang manggil ini yang memutuskan
    mau retry, minta upload ulang, atau lanjut tanpa OCR (lihat investigate.py)."""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise OCRError("GEMINI_API_KEY tidak ditemukan di environment.")

    raw_bytes, mime_type = _decode_screenshot(screenshot_base64)

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=OCR_MODEL_NAME,
            contents=[
                types.Part.from_bytes(data=raw_bytes, mime_type=mime_type),
                OCR_PROMPT,
            ],
        )
    except Exception as exc:  # noqa: BLE001 -- sengaja luas, semua kegagalan API dibungkus jadi OCRError
        logger.error("OCR gagal: %s", exc)
        raise OCRError(f"Gagal memproses gambar lewat Gemini Vision: {exc}") from exc

    if not response.text:
        raise OCRError("Gemini Vision mengembalikan hasil kosong.")

    return response.text.strip()
