import os
import time
import requests
import subprocess
from typing import Optional
from loguru import logger
from google import genai

class SubLLMClient:
    @staticmethod
    def get_gemini_client():
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set in .env")
        return genai.Client(api_key=api_key)

    @staticmethod
    def detect_backend(model_id: str, specific_provider: Optional[str] = None) -> str:
        """Determines the backend based on explicit configuration or fallback heuristic."""
        if specific_provider:
            return specific_provider.lower()

        global_provider = os.getenv("AI_PROVIDER", "").lower()
        if global_provider in ["gemini", "ollama", "genspark"]:
            return global_provider

        # Fallback heuristic if not explicitly set
        low_id = model_id.lower()
        if "gemini" in low_id:
            return "gemini"
        if "genspark" in low_id or low_id in ["search", "crawl"]:
            return "genspark"
        return "ollama"

    @staticmethod
    def call_any(
        model_id: str, prompt: str, role_name: str = "task", provider: Optional[str] = None
    ) -> str:
        """Call the appropriate backend based on configuration or model_id."""
        backend = SubLLMClient.detect_backend(model_id, provider)
        if backend == "gemini":
            return SubLLMClient.call_gemini(model_id, prompt, role_name)
        elif backend == "genspark":
            return SubLLMClient.call_genspark(model_id, prompt, role_name)
        else:
            return SubLLMClient.call_ollama(model_id, prompt, role_name)

    @staticmethod
    def call_gemini(model_name: str, prompt: str, role_name: str = "task") -> str:
        client = SubLLMClient.get_gemini_client()

        # Dynamic context check
        try:
            model_info = client.models.get(model=model_name)
            max_tokens = model_info.input_token_limit

            token_count_resp = client.models.count_tokens(model=model_name, contents=prompt)
            current_tokens = token_count_resp.total_tokens

            logger.info(
                f"Gemini [{role_name}] ({model_name}) Tokens: {current_tokens}/{max_tokens}"
            )

            if current_tokens > max_tokens:
                raise ValueError(
                    f"Prompt exceeds Gemini context limit: {current_tokens} > {max_tokens}"
                )
        except Exception as e:
            logger.warning(f"Could not verify Gemini context limit for {model_name}: {e}")

        logger.info(f"Calling Gemini ({model_name}) for {role_name}...")
        try:
            start_time = time.perf_counter()
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.1 if role_name != "drafting" else 0.2,
                ),
            )
            elapsed = time.perf_counter() - start_time
            logger.info(f"Gemini [{role_name}] completed in {elapsed:.2f}s")
            return response.text.strip()
        except Exception:
            logger.exception(f"Gemini [{role_name}] call failed")
            raise

    @staticmethod
    def call_ollama(model_name: str, prompt: str, role_name: str = "task") -> str:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        # Dynamic context check for Ollama
        try:
            show_resp = requests.post(f"{base_url}/api/show", json={"name": model_name}, timeout=5)
            if show_resp.status_code == 200:
                context_limit = 4096  # Conservative default
                estimated_tokens = len(prompt) // 4
                logger.info(
                    f"Ollama [{role_name}] ({model_name}) "
                    f"Est. Tokens: ~{estimated_tokens}/{context_limit}"
                )
                if estimated_tokens > context_limit:
                    logger.warning(
                        f"Prompt might exceed Ollama limit: "
                        f"~{estimated_tokens} > {context_limit}"
                    )
        except Exception as e:
            logger.warning(f"Could not verify Ollama context limit for {model_name}: {e}")

        logger.info(f"Calling Ollama ({model_name}) for {role_name}...")
        try:
            start_time = time.perf_counter()
            response = requests.post(
                f"{base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1 if role_name != "drafting" else 0.2},
                },
                timeout=90,
            )
            response.raise_for_status()
            elapsed = time.perf_counter() - start_time
            logger.info(f"Ollama [{role_name}] completed in {elapsed:.2f}s")
            return response.json().get("response", "").strip()
        except Exception:
            logger.exception(f"Ollama [{role_name}] call failed")
            raise

    @staticmethod
    def call_genspark(model_name: str, prompt: str, role_name: str = "task") -> str:
        """Call Genspark CLI (gsk) to get an answer."""
        gsk_cmd = (
            model_name
            if model_name in ["search", "crawl", "img", "video"]
            else os.getenv("GENSPARK_MODEL_TYPE", "search")
        )
        logger.info(f"Calling Genspark ({gsk_cmd}) for {role_name}...")

        command = ["gsk", gsk_cmd, prompt, "--output", "text"]

        try:
            start_time = time.perf_counter()
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            elapsed = time.perf_counter() - start_time
            logger.info(f"Genspark [{role_name}] completed in {elapsed:.2f}s")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.exception(f"Genspark [{role_name}] call failed: {e.stderr}")
            raise
