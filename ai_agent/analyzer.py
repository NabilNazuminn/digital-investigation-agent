# Ini file analyzer (Intinya LLM Analysis)

import logging
import time
from google import genai
from google.genai import types

from .config import GeminiConfig, load_config
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .json_parser import validate_and_parse
from .models import InvestigationReport, UnifiedContext

logger = logging.getLogger(__name__)


class LLMAnalyzer:
    def __init__(self, config: GeminiConfig | None = None):
        self.config = config or load_config()
        # Timeout default httpx/google-genai kadang terlalu pendek buat koneksi
        # yang kurang stabil, bikin permintaan gampang ke-timeout padahal
        # cuma butuh nunggu dikit lebih lama. 60 detik biar lebih toleran.
        self.client = genai.Client(
            api_key=self.config.api_key,
            http_options=types.HttpOptions(timeout=60_000),  # dalam milidetik
        )

    def analyze(self, unified_context: UnifiedContext | dict) -> InvestigationReport: # type: ignore
        if isinstance(unified_context, UnifiedContext):
            context_dict = unified_context.model_dump()
        else:
            context_dict = unified_context

        user_prompt = build_user_prompt(context_dict)

        logger.info("Mengirim request ke Gemini API...")
        
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.config.model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=self.config.temperature,
                        top_p=self.config.top_p,
                        max_output_tokens=self.config.max_output_tokens,
                        response_mime_type="application/json",
                    )
                )
                
                if response.text is None:
                    raise RuntimeError("Gemini mengembalikan respons kosong (None).")

                # Kalau sampai sini, berarti SUKSES. Langsung proses dan returnnyaaaaaa.
                raw_text = response.text

                logger.info("Mendapat response dari Gemini")
                logger.debug(f"Raw response (first 300 chars): {raw_text[:300]}")

                report = validate_and_parse(raw_text)
                logger.info(
                    f"Analysis complete: risk_score={report.risk_score}, "
                    f"risk_level={report.risk_level}, "
                    f"red_flags_count={len(report.red_flags)}"
                )
                return report 

            except Exception as e:
                error_str = str(e)

                # Kondisi yang layak dicoba ulang:
                # - Server Gemini lagi sibuk (503) atau kelamaan mroses di
                #   sisi mereka sendiri (504 DEADLINE_EXCEEDED) -- ini bukan
                #   masalah di kita, request-nya nyampe, tapi Google-nya yang
                #   nyerah duluan. Wajar dicoba ulang.
                # - Masalah jaringan sementara di sisi kita (connection
                #   timeout/reset) -- request-nya gak sempat nyampe sama
                #   sekali ke server.
                is_server_busy = any(marker in error_str for marker in ("503", "504", "DEADLINE_EXCEEDED"))
                is_network_hiccup = any(
                    marker in error_str
                    for marker in (
                        "10060",  # Windows: connection timed out
                        "Timeout",
                        "TimeoutError",
                        "ConnectError",
                        "Connection aborted",
                        "Connection reset",
                        "Max retries exceeded",
                    )
                )

                if (is_server_busy or is_network_hiccup) and attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    reason = "Server Gemini sibuk/lambat (503/504)" if is_server_busy else "Koneksi jaringan bermasalah"
                    logger.warning(
                        f"{reason}. Coba lagi dalam {wait_time} detik... "
                        f"({attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    # Kalau bukan kondisi di atas, atau sudah 3x gagal, berhenti dan raise error
                    logger.error(f"Gagal menganalisis: {e}")
                    if is_network_hiccup:
                        raise RuntimeError(
                            "Gagal terhubung ke server Gemini API setelah beberapa kali "
                            "percobaan. Periksa koneksi internet Anda (termasuk firewall/"
                            "antivirus yang mungkin memblokir koneksi ke generativelanguage."
                            f"googleapis.com). Detail teknis: {e}"
                        ) from e
                    raise RuntimeError(f"LLM analysis gagal: {e}") from e