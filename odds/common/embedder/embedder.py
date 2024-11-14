from typing import Optional
from ...common.datatypes import Embedding


class Embedder:

    async def embed(self, text: str) -> Optional[Embedding]:
        pass

    def vector_size(self) -> int:
        pass

    def print_total_usage(self) -> None:
        pass