import dataclasses

from kvfile import KVFile

from ..fs.fs_store import FSStore
from ...datatypes import Dataset

class KVFileStore(FSStore):

    def __init__(self) -> None:
        super().__init__()
        self.kvfile = KVFile(FSStore.DIR / 'db')

    async def storeDataset(self, dataset: Dataset) -> None:
        id = dataset.storeId()
        self.kvfile.set(id, dataclasses.asdict(dataset))
        print(f'STORING DATASET {dataset.catalogId} {dataset.id} {dataset.title}')

    async def getDataset(self, datasetId: str) -> Dataset:
        data = self.kvfile.get(datasetId)
        if data:
            return Dataset(**data)
        return None
    
    async def hasDataset(self, datasetId: str) -> bool:
        return self.kvfile.get(datasetId) is not None
    
    # async def findDatasets(self, embedding: Embedding) -> list[Dataset]:
    #     return []
