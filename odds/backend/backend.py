import asyncio

from .processor import dataset_processor
from .scanner.scanner_factory import ScannerFactory
from ..common.catalog_repo import catalog_repo
from ..common.datatypes import DataCatalog, Dataset
from ..common.config import config
from ..common.metadata_store import metadata_store
from ..common.filters import CatalogFilter, CatalogFilterById, \
    DatasetFilter, DatasetFilterById, DatasetFilterNew, DatasetFilterForce, DatasetFilterIncomplete
# from ..common.db import db
from ..common.realtime_status import realtime_status as rts


class ODDSBackend:
    
    catalogs: list[DataCatalog]

    def __init__(self):
        self.scanner_factory = ScannerFactory()
        self.catalogs = catalog_repo.load_catalogs()

    async def scan(self, catalogFilter: CatalogFilter, datasetFilter: DatasetFilter, *datasetFilterArgs) -> None:
        dataset_processor.set_concurrency(config.dataset_processor_concurrency_limit or 3)
        rts.clearAll()
        scanner_ctx = ''
        for catalog_idx, catalog in enumerate(self.catalogs):
            cat_ctx = f'{catalog.id}[{catalog_idx}]'
            if await catalogFilter.include(catalog):
                # await db.storeDataCatalog(catalog, cat_ctx)
                scanner = self.scanner_factory.create_scanner(catalog, cat_ctx)
                if scanner:
                    dataset_idx = 0
                    async for dataset in scanner.scan():
                        rts.set(cat_ctx, f'GOT DATASET {dataset.id}')
                        ctx = f'{cat_ctx}/{dataset.id}[{dataset_idx}]'
                        existing = await metadata_store.getDataset(dataset.storeId())
                        if existing:
                            existing.merge(dataset)
                            dataset = existing
                        if await datasetFilter.consider(dataset):
                            rts.set(cat_ctx, f'CONSIDER DATASET {dataset.id}')
                            # await db.storeDataset(dataset, ctx)
                            dataset_processor.queue(dataset, catalog, datasetFilter, ctx)
                        else:
                            rts.set(cat_ctx, f'SKIP DATASET {dataset.id}')
                        dataset_idx += 1
            else:
                if config.debug:
                    rts.set(scanner_ctx, f'SKIP CATALOG {catalog.id}')
            rts.clear(cat_ctx)            
        rts.clear(scanner_ctx)
        await dataset_processor.wait()

    def scan_required(self) -> None:
        asyncio.run(self.scan(CatalogFilter(), DatasetFilterIncomplete()))

    def scan_all(self) -> None:
        asyncio.run(self.scan(CatalogFilter(), DatasetFilterForce()))

    def scan_new(self) -> None:
        asyncio.run(self.scan(CatalogFilter(), DatasetFilterNew()))

    def scan_specific(self, catalogId: str = None, datasetId: str = None, force=True) -> None:
        if catalogId:
            catalogFilter = CatalogFilterById(catalogId)
        else:
            catalogFilter = CatalogFilter()
        if datasetId:
            datasetFilter = DatasetFilterById(datasetId)
        else:
            if force:
                datasetFilter = DatasetFilterForce()
            else:
                datasetFilter = DatasetFilterIncomplete()
        asyncio.run(self.scan(catalogFilter, datasetFilter))