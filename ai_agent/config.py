# ini file nya dia buat konfigurasi Gemini API ya 

import os
from dataclasses import dataclass

@dataclass
class GeminiConfig:
    api_key: str
    model_name: str = "gemini-3.5-flash"
    temperature: float = 0.2
    top_p: float = 0.8
    max_output_tokens: int = 4096

def load_config() -> GeminiConfig:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY tidak ditemukan. "
            "Set environment variable: set GEMINI_API_KEY='your-key'"
        )

    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    temp = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))

    return GeminiConfig(api_key=api_key, model_name=model, temperature=temp)