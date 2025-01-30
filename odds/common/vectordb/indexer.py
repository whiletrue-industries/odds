from ..datatypes import Embedding, Dataset


class Indexer:

    async def index(self, dataset: Dataset, embedding: Embedding) -> None:
        pass
    
    async def findDatasets(self, embedding: Embedding, query, num=10, catalog_ids: list[str] | None = None) -> list[Dataset]:
        return []