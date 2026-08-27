# Ini file Agent Orchestrator (Entry Point)

import logging
from typing import Union

from .models import InvestigationReport, UnifiedContext
from .analyzer import LLMAnalyzer
from .risk_assessor import validate_risk_assessment
from .report_generator import generate_final_output, to_json_string
from .config import GeminiConfig

logger = logging.getLogger(__name__)


class DigitalInvestigationAgent:

    def __init__(self, config: GeminiConfig | None = None):
        self.analyzer = LLMAnalyzer(config)

    def investigate(
        self,
        unified_context: Union[UnifiedContext, dict],
        validate_risk: bool = True,
    ) -> dict:

        logger.info("=" * 60)
        logger.info("Digital Investigation Agent — START")
        logger.info("=" * 60)

        # Step 1: LLM Analysis
        report = self.analyzer.analyze(unified_context)

        # Step 2: Risk Validation (layer tambahan)
        if validate_risk:
            report = validate_risk_assessment(report, unified_context)

        # Step 3: Format Output
        final_output = generate_final_output(report)

        logger.info(
            f"Investigation COMPLETE — "
            f"Score: {report.risk_score}, "
            f"Level: {report.risk_level}, "
            f"Flags: {len(report.red_flags)}, "
            f"Confidence: {report.confidence}"
        )
        logger.info("=" * 60)

        return final_output

    def investigate_to_model(
        self,
        unified_context: Union[UnifiedContext, dict],
        validate_risk: bool = True,
    ) -> InvestigationReport:

        report = self.analyzer.analyze(unified_context)
        if validate_risk:
            report = validate_risk_assessment(report, unified_context)
        return report


# ── Convenience function untuk panggil cepat ──

_default_agent: DigitalInvestigationAgent | None = None


def investigate(unified_context: Union[UnifiedContext, dict]) -> dict:
    """
    Quick-use function. Backend cukup:
        from ai_agent import investigate
        result = investigate(context_dict)
    """
    global _default_agent
    if _default_agent is None:
        _default_agent = DigitalInvestigationAgent()
    return _default_agent.investigate(unified_context)