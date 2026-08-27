# dia file public API

"""
Digital Investigation Agent — AI Module
=======================================

Cara penggunaan oleh backend FastAPI:

    from ai_agent import investigate, DigitalInvestigationAgent

    # Cara 1: Quick function
    result = investigate(unified_context_dict)

    # Cara 2: Dengan instance (lebih baik untuk production)
    agent = DigitalInvestigationAgent()
    result = agent.investigate(unified_context_dict)

Unified context dict harus memiliki key:
    - conversation_texts: list[str]
    - extracted_urls: list[str]
    - extracted_phone_numbers: list[str]
    - extracted_account_numbers: list[str]
    - extracted_emails: list[str]
    - url_check_results: dict
    - phone_check_results: dict
    - account_check_results: dict
    - email_check_results: dict
    - ocr_text: str
"""

from .agent import DigitalInvestigationAgent, investigate
from .models import InvestigationReport, UnifiedContext, RiskLevel, Confidence

__all__ = [
    "DigitalInvestigationAgent",
    "investigate",
    "InvestigationReport",
    "UnifiedContext",
    "RiskLevel",
    "Confidence",
]