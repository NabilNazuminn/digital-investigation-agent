# ini file JSON Parser & Validator. LLM kadang ngeluarin JSON yang tidak bersih. Ini dia penanganannya😁.

import json
import re
import logging

from .models import InvestigationReport, RiskLevel

logger = logging.getLogger(__name__)


def extract_json_from_llm_response(raw: str) -> dict:
    """
   Dia menangani output LLM yang kadang:
    - Diwrap dalam ```json ... ```
    - Diawali/diakhiri whitespace berlebih
    - Mengandung karakter control
    - Terpotong jadi dua JSON (Extra data error di Gemini 3.x)
    """
    text = raw.strip()

    # Hapus markdown code block jika ada ya
    pattern = r"```(?:json)?\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        text = match.group(1).strip()

    # Hapus character yang bisa bikin si JSON rusak
    text = text.replace("\x00", "")

    # Hapus trailing comma sebelum } atau ]
    text = re.sub(r",\s*([}\]])", r"\1", text)

    try:
        # Coba parse normal dulu
        return json.loads(text)
    except json.JSONDecodeError:
        # Kalau gagal (misal: "Extra data"), ambil HANYA JSON pertama yang valid
        logger.warning("JSON terpotong/berlebih, mencoba mengambil objek pertama...")
        decoder = json.JSONDecoder()
        return decoder.raw_decode(text)[0]


def validate_and_parse(raw_response: str) -> InvestigationReport:
    """
    Parse raw LLM response → validate → return InvestigationReport.
    Raise ValueError jika tidak bisa diparse atau tidak valid.
    """
    try:
        data = extract_json_from_llm_response(raw_response)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}")
        logger.error(f"Raw response (first 500 chars): {raw_response[:500]}")
        raise ValueError(f"LLM output bukan JSON valid: {e}")

    try:
        report = InvestigationReport(**data)
    except Exception as e:
        logger.error(f"Pydantic validation failed: {e}")
        logger.error(f"Parsed data: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
        raise ValueError(f"Struktur output tidak sesuai schema: {e}")

    # Cross-validasi: risk_level harus konsisten dengan risk_score
    score = report.risk_score
    expected_level = (
        RiskLevel.HIGH if score >= 70 else
        RiskLevel.MEDIUM if score >= 40 else
        RiskLevel.LOW
    )
    if report.risk_level != expected_level:
        logger.warning(
            f"Risk level mismatch: score={score} but level={report.risk_level}. "
            f"Correcting to {expected_level}"
        )
        report.risk_level = expected_level

    return report