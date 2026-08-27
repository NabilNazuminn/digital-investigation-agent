"""
Client untuk manggil AI Agent asli (dibuat rekan tim, lihat folder /ai_agent).

File ini GANTI dari ai_agent_interface.py versi stub sebelumnya, karena
sekarang kontrak aslinya sudah diketahui pasti dari kode yang dikirim
team leader (bukan tebakan lagi).

Kontrak asli:
    Input : ai_agent.models.UnifiedContext (lihat evidence_aggregator.py buat bikinnya)
    Output: dict siap kirim ke frontend (sudah termasuk risk_score, risk_level,
            red_flags, reasoning, recommendation, dll -- lihat ai_agent/models.py
            class InvestigationReport untuk bentuk lengkapnya)

Tetap ada mode STUB supaya lo bisa develop & testing tanpa perlu
GEMINI_API_KEY asli dulu (misal pas demo ke tim atau belum dapat kuota API).
"""

from __future__ import annotations

import os

from ai_agent.models import UnifiedContext


def run_investigation(context: UnifiedContext) -> dict:
    """Panggil AI Agent (asli atau stub, tergantung env USE_AI_AGENT_STUB).

    Sengaja dibaca DI SINI (bukan di level modul) supaya nilainya selalu
    terbaru sesuai .env saat request masuk, bukan ke-cache saat modul ini
    pertama kali di-import (itu penyebab bug env var "kepake telat")."""
    use_stub = os.getenv("USE_AI_AGENT_STUB", "true").lower() == "true"

    if use_stub:
        return _stub_investigate(context)

    from ai_agent import investigate  # import di sini biar gak wajib ada API key kalau lagi pakai stub

    raw_result = investigate(context)
    # Bentuk asli dari ai_agent.investigate() itu DIBUNGKUS:
    # {"investigation_report": {risk_score, risk_level, ...}, "metadata": {...}}
    # -- bukan rata (flat) kayak yang stub kita hasilkan. "Buka bungkusnya" di
    # sini, satu-satunya tempat, biar kode lain (endpoint, history_repository)
    # gak perlu tau soal pembungkusan ini sama sekali.
    report = raw_result["investigation_report"]
    report["metadata"] = raw_result.get("metadata")
    return report


def _stub_investigate(context: UnifiedContext) -> dict:
    """Dummy hasil, bentuknya SAMA PERSIS dengan output ai_agent asli (lihat
    InvestigationReport di ai_agent/models.py), supaya kode endpoint/frontend
    yang mengonsumsi hasil ini tidak perlu berubah saat nanti ganti ke API asli."""
    red_flags = []
    text = " ".join(context.conversation_texts).lower()

    if any(word in text for word in ["segera", "sekarang juga", "buruan", "jangan sampai"]):
        red_flags.append(
            {
                "type": "urgency_or_threat",
                "description": "[STUB] Terdeteksi bahasa mendesak pada chat.",
                "severity": "medium",
                "evidence_reference": "conversation_texts",
            }
        )

    suspicious_domains = [
        url for url, result in context.url_check_results.items()
        if result.get("status") == "suspicious"
    ]
    for url in suspicious_domains:
        red_flags.append(
            {
                "type": "suspicious_domain",
                "description": f"[STUB] Domain {url} ditandai mencurigakan.",
                "severity": "high",
                "evidence_reference": "url_check_results",
            }
        )

    score = min(100, len(red_flags) * 40)
    level = "HIGH" if score >= 70 else "MEDIUM" if score >= 40 else "LOW"

    return {
        "risk_score": score,
        "risk_level": level,
        "evidence_summary": "[STUB] Ringkasan dummy, bukan hasil AI Agent asli.",
        "red_flags": red_flags,
        "reasoning": "[STUB] Ini hasil dummy dari placeholder, ganti USE_AI_AGENT_STUB=false untuk pakai API asli.",
        "recommendation": ["Ini rekomendasi dummy dari mode stub."],
        "confidence": "low",
        "missing_evidence": [],
        "metadata": None,  # AI Agent asli juga punya field ini, stub disamakan biar konsisten
    }
