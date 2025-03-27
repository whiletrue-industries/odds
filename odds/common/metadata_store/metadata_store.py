import dataclasses
from typing import List
from ..datatypes import Dataset, Embedding


@dataclasses.dataclass
class DatasetResult:
    datasets: List[Dataset]
    total: int
    pages: int
    page: int


class MetadataStore:

    async def storeDataset(self, dataset: Dataset, ctx: str) -> None:
        print('STORING DATASET', dataset.catalogId, dataset.id, dataset.title)

    async def getDataset(self, datasetId: str) -> Dataset:
        return None
        
    async def hasDataset(self, datasetId: str) -> bool:
        return False
    
    async def setEmbedding(self, dataset: Dataset, embedding: Embedding):
        dataset.embedding = embedding

    async def getEmbedding(self, dataset: Dataset) -> Embedding:
        if dataset and hasattr(dataset, 'embedding'):
            return dataset.embedding
        return None
    
    async def getDatasets(self, catalogId: str, page=1, sort=None, query=None, filters=None) -> DatasetResult:
        return DatasetResult([], 0, 0, page)
        
    # async def findDatasets(self, embedding: Embedding) -> list[Dataset]:
    #     return []
