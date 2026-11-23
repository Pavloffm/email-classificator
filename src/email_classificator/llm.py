from abc import ABC, abstractmethod


class LLM_Provider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate text or raise an exception on failure."""
        ...

class OllamaLLM(LLM_Provider):
    def __init__(self, model: str):
        self.model = model
        # Create the Ollama client here, once.

    def generate(self, prompt: str) -> str:
        # Call Ollama and return only the generated text.
        raise NotImplementedError("Ollama integration goes here")