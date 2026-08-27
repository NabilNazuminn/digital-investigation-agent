# ini file Risk Assessor (Layer Validasi Tambahan)

import logging
from .models import InvestigationReport, UnifiedContext, RiskLevel, Confidence  # ← import langsung

logger = logging.getLogger(__name__)


def _recalculate_level(score: int) -> RiskLevel:
    """Helper: hitung risk_level dari score."""
    if score >= 70:
        return RiskLevel.HIGH
    elif score >= 40:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.LOW


def validate_risk_assessment(
    report: InvestigationReport,
    context: UnifiedContext | dict
) -> InvestigationReport:
    """
    Layer validasi tambahan di luar LLM.
    Memastikan risk score masuk akal terhadap evidence yang tersedia.
    Ini bukan mengganti skor LLM, tapi menangkap kasus-kasus anomali.
    """
    if isinstance(context, UnifiedContext):
        ctx = context
    else:
        ctx = UnifiedContext(**context)

    # Hitung apakah ada external check results
    has_external_data = any([
        ctx.url_check_results and ctx.url_check_results.get("status") != "not_available",
        ctx.phone_check_results and any(
            v != "not_available" for v in ctx.phone_check_results.values()
        ) if isinstance(ctx.phone_check_results, dict) else False,
        ctx.account_check_results and any(
            v != "not_available" for v in ctx.account_check_results.values()
        ) if isinstance(ctx.account_check_results, dict) else False,
        ctx.email_check_results and any(
            v != "not_available" for v in ctx.email_check_results.values()
        ) if isinstance(ctx.email_check_results, dict) else False,
    ])

    # Jika tidak ada external data sama sekali dan evidence minim,
    # cap skor ke maksimal 50 dan turunkan confidence
    total_evidence = (
        len(ctx.conversation_texts)
        + len(ctx.extracted_urls)
        + len(ctx.extracted_phone_numbers)
        + len(ctx.extracted_account_numbers)
        + len(ctx.extracted_emails)
        + (1 if ctx.ocr_text and ctx.ocr_text != "not_available" else 0)
    )

    is_evidence_thin = (total_evidence <= 1) and not has_external_data

    if is_evidence_thin and report.risk_score > 50:
        logger.warning(
            f"Evidence terlalu tipis (count={total_evidence}, no external data) "
            f"tapi skor {report.risk_score}. Menurunkan ke 50."
        )
        report.risk_score = 50
        report.risk_level = _recalculate_level(report.risk_score)

    if is_evidence_thin and report.confidence == Confidence.HIGH:
        logger.warning("Menurunkan confidence karena evidence tipis")
        report.confidence = Confidence.LOW

    # Jika red_flags kosong tapi skor tinggi → anomali
    if not report.red_flags and report.risk_score >= 60:
        logger.warning(
            f"Skor tinggi ({report.risk_score}) tapi tidak ada red flags. "
            f"Menurunkan skor ke 45."
        )
        report.risk_score = 45
        report.risk_level = _recalculate_level(report.risk_score)

    return report