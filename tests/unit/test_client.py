import pytest
import os
from mcp_ai_worker.client import SubLLMClient

def test_detect_backend_explicit_provider():
    # Case 1: Explicitly provided as argument
    assert SubLLMClient.detect_backend("any-model", specific_provider="gemini") == "gemini"
    assert SubLLMClient.detect_backend("any-model", specific_provider="ollama") == "ollama"
    assert SubLLMClient.detect_backend("any-model", specific_provider="genspark") == "genspark"

def test_detect_backend_env_provider():
    # Backup current env
    old_provider = os.getenv("AI_PROVIDER")
    
    try:
        os.environ["AI_PROVIDER"] = "gemini"
        assert SubLLMClient.detect_backend("any-model") == "gemini"
        
        os.environ["AI_PROVIDER"] = "ollama"
        assert SubLLMClient.detect_backend("any-model") == "ollama"
        
        os.environ["AI_PROVIDER"] = "genspark"
        assert SubLLMClient.detect_backend("any-model") == "genspark"
    finally:
        if old_provider:
            os.environ["AI_PROVIDER"] = old_provider
        else:
            del os.environ["AI_PROVIDER"]

def test_detect_backend_heuristic():
    # AI_PROVIDER is unset
    old_provider = os.getenv("AI_PROVIDER")
    if old_provider:
        del os.environ["AI_PROVIDER"]

    try:
        # Model ID contains keywords
        assert SubLLMClient.detect_backend("gemini-1.5-flash") == "gemini"
        assert SubLLMClient.detect_backend("genspark-search") == "genspark"
        assert SubLLMClient.detect_backend("ollama-llama3") == "ollama"
        
        # Fallback to ollama
        assert SubLLMClient.detect_backend("unknown-model") == "ollama"
    finally:
        if old_provider:
            os.environ["AI_PROVIDER"] = old_provider
