from .base import ModelProvider, Reponse
from .mock import MockProvider
from .simule import SimuleProvider
from .offline_mcp import OfflineMCPProvider

__all__ = [
    "MockProvider",
    "ModelProvider",
    "Reponse",
    "SimuleProvider",
    "OfflineMCPProvider",
    "charger",
]


def charger(nom: str, **kwargs):
    """Fabrique de provider par nom.

    Providers supportés :
      - mock        : déterministe, pour les tests
      - simule      : bruité, pour vérifier le banc hors ligne
      - anthropic   : Claude (nécessite ANTHROPIC_API_KEY)
      - openai      : compatible OpenAI (GPT, etc.)
      - ollama      : local, sans clé (http://127.0.0.1:11434)
      - grok        : alias pratique pour Grok via l'API xAI
    """
    if nom == "mock":
        return MockProvider(**kwargs)
    if nom == "simule":
        return SimuleProvider(**kwargs)
    if nom in ("offline", "mcp", "offline_mcp"):
        return OfflineMCPProvider(**kwargs)
    if nom == "anthropic":
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider(**kwargs)
    if nom == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider(**kwargs)
    if nom == "local":
        from .local_provider import LocalProvider
        return LocalProvider(**kwargs)
    if nom == "ollama":
        from .ollama_provider import OllamaProvider
        return OllamaProvider(**kwargs)
    if nom == "grok":
        from .openai_provider import OpenAIProvider
        import os

        # Valeurs par défaut adaptées à xAI
        kwargs.setdefault("modele", "grok-3")
        kwargs.setdefault("base_url", os.environ.get("OPENAI_BASE_URL", "https://api.x.ai/v1"))
        if "api_key" not in kwargs:
            kwargs["api_key"] = os.environ.get("GROK_API_KEY") or os.environ.get("OPENAI_API_KEY")
        return OpenAIProvider(**kwargs)

    raise ValueError(
        f"provider inconnu: {nom}. "
        "Choix possibles : mock, simule, local, offline, mcp, ollama, anthropic, openai, grok"
    )
