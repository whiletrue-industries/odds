from ..datatypes import Dataset, DataCatalog

class DBStorage:

    async def storeDataset(self, dataset: Dataset, ctx: str) -> None:
        print(f'{ctx}:SAVING DATASET', dataset.title)

    async def storeDataCatalog(self, catalog: DataCatalog, ctx: str) -> None:
        print(f'{ctx}:SAVING DATA CATALOG', catalog.id)

    async def getDataset(self, datasetId: str) -> Dataset:
        return None

    async def hasDataset(self, datasetId: str) -> bool:
        return False