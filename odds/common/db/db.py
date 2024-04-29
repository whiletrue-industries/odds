from ..datatypes import Dataset, DataCatalog

class DBStorage:

    async def storeDataset(self, dataset: Dataset) -> None:
        print('SAVING DATASET', dataset.catalogId, dataset.id, dataset.title)

    async def storeDataCatalog(self, catalog: DataCatalog) -> None:
        print('SAVING DATA CATALOG', catalog.id)

    async def getDataset(self, datasetId: str) -> Dataset:
        return None

    async def hasDataset(self, datasetId: str) -> bool:
        return False