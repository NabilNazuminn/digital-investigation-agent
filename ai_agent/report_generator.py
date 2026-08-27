# Ini file Report Generator (Final Output Formatter)

import json
import logging
from datetime import datetime, timezone

from .models import InvestigationReport  

logger = logging.getLogger(__name__)


def generate_final_output(report: InvestigationReport) -> dict:
    """
    Mengubah InvestigationReport ke dict siap kirim ke backend.
    """
    output = {
        "investigation_report": {
            "risk_score": report.risk_score,
            "risk_level": report.risk_level.value,  # .value untuk konversi enum → stringnya
            "evidence_summary": report.evidence_summary,
            "red_flags": [
                {
                    "type": rf.type,
                    "description": rf.description,
                    "severity": rf.severity,
                    "evidence_reference": rf.evidence_reference,
                }
                for rf in report.red_flags
            ],
            "reasoning": report.reasoning,
            "recommendation": report.recommendation,
            "confidence": report.confidence.value,  # .value untuk konversi enum → string
            "missing_evidence": report.missing_evidence,
        },
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "red_flags_count": len(report.red_flags),
            "high_severity_flags": sum(
                1 for rf in report.red_flags if rf.severity == "high"
            ),
        }
    }

    return output


def to_json_string(report: InvestigationReport, pretty: bool = True) -> str:
    """Helper: langsung ke JSON string."""
    output = generate_final_output(report)
    return json.dumps(output, ensure_ascii=False, indent=2 if pretty else None)