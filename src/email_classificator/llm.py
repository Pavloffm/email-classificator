from abc import ABC, abstractmethod

from langchain_ollama import OllamaLLM as LangChainOllamaLLM


class LLM_Provider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate text or raise an exception on failure."""
        ...


class OllamaLLM(LLM_Provider):
    def __init__(self, model: str):
        self.client = LangChainOllamaLLM(
            model=model,
            temperature=0.2,
        )

    def generate(self, prompt: str) -> str:
        return self.client.invoke(prompt)
