from ..datatypes import Dataset, Embedding

class MetadataStore:

    async def storeDataset(self, dataset: Dataset, ctx: str) -> None:
        print('STORING DATASET', dataset.catalogId, dataset.id, dataset.title)

    async def getDataset(self, datasetId: str) -> Dataset:
        return None
        
    async def hasDataset(self, datasetId: str) -> bool:
        return False
    
    async def findDatasets(self, embedding: Embedding) -> list[Dataset]:
        return []
