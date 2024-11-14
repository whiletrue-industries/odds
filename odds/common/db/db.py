from ..datatypes import Dataset, DataCatalog
from ...common.realtime_status import realtime_status as rts

class DBStorage:

    async def storeDataset(self, dataset: Dataset, ctx: str) -> None:
        rts.set(ctx, f'STORE DATASET {dataset.title}')

    async def storeDataCatalog(self, catalog: DataCatalog, ctx: str) -> None:
        rts.set(ctx, f'STORE DATA CATALOG {catalog.id}')

    async def getDataset(self, datasetId: str) -> Dataset:
        return None

    async def hasDataset(self, datasetId: str) -> bool:
        return False