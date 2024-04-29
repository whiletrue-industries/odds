from ..datatypes import Embedding, Dataset


class Indexer:

    async def index(self, dataset: Dataset, embedding: Embedding) -> None:
        pass
    
    async def findDatasets(self, embedding: Embedding, num=10) -> list[str]:
        return []