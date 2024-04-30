from typing import Any
from ..datatypes import Dataset, DataCatalog


class LLMQuery():

    def __init__(self, dataset: Dataset, catalog: DataCatalog):
        self.dataset = dataset
        self.catalog = catalog

    def model(self) -> str:
        pass

    def temperature(self) -> float:
        return 0

    def prompt(self) -> list[tuple[str, str]]:
        pass

    def handle_result(self, result: dict) -> Any:
        pass

    def expects_json(self) -> bool:
        return True
    
    def max_tokens(self) -> int:
        return 2048


class CustomLLMQuery(LLMQuery):

    def __init__(self, prompt, temperature=0.5, model='cheap', expects_json=True):
        super().__init__(None, None)
        self._prompt = prompt
        self._temperature = temperature
        self._model = model
        self._expects_json = expects_json

    def model(self) -> str:
        return self._model

    def prompt(self) -> list[tuple[str, str]]:
        return self._prompt
    
    def temperature(self) -> float:
        return self._temperature
    
    def handle_result(self, result: str) -> Any:
        pass

    def expects_json(self) -> bool:
        return self._expects_json