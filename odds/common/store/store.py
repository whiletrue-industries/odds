from ..datatypes import Dataset, Embedding, Resource

class Store:

    async def storeDataset(self, dataset: Dataset, ctx: str) -> None:
        print('STORING DATASET', dataset.catalogId, dataset.id, dataset.title)

    async def storeDB(self, resource: Resource, dataset: Dataset, dbFile, ctx: str) -> None:
        print('STORING DB', dbFile)

    async def storeEmbedding(self, dataset: Dataset, embedding: Embedding, ctx: str) -> None:
        print('STORING EMBEDDING', dataset)

    async def getDataset(self, datasetId: str) -> Dataset:
        return None
    
    async def getDB(self, resource: Resource, dataset: Dataset) -> str:
        return None

    async def getEmbedding(self, dataset: Dataset) -> Embedding:
        return None
    
    async def hasDataset(self, datasetId: str) -> bool:
        return False