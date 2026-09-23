import os
from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from app.config import settings


def get_llm(temperature: float = 0.1, provider: Optional[str] = None) -> BaseChatModel:
    """
    Provider-agnostic factory for instantiating the LLM.
    Defaults to Google Gemini, with seamless runtime fallback to OpenAI, Anthropic, or Ollama.
    """
    active_provider = (provider or settings.llm_provider).lower()

    if active_provider == "gemini":
        api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Please configure it in your .env file or environment variables."
            )
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=api_key,
            temperature=temperature,
            convert_system_message_to_human=True,
        )

    elif active_provider == "openai":
        api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Please configure it in your .env file or environment variables."
            )
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=api_key,
            temperature=temperature,
        )

    elif active_provider == "anthropic":
        api_key = settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. Please configure it in your .env file or environment variables."
            )
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=settings.anthropic_model,
            api_key=api_key,
            temperature=temperature,
        )

    elif active_provider == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=temperature,
        )

    else:
        raise ValueError(
            f"Unsupported LLM provider '{active_provider}'. Supported: 'gemini', 'openai', 'anthropic', 'ollama'."
        )
