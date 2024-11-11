from ..datatypes import Dataset, Embedding, Resource

class Store:

    async def storeDB(self, resource: Resource, dataset: Dataset, dbFile, ctx: str) -> bool:
        print('STORING DB', dbFile)
        return False

    async def storeEmbedding(self, dataset: Dataset, embedding: Embedding, ctx: str) -> None:
        print('STORING EMBEDDING', dataset)
    
    async def getDB(self, resource: Resource, dataset: Dataset) -> str:
        return None

    async def getEmbedding(self, dataset: Dataset) -> Embedding:
        return None
