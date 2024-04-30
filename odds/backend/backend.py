import asyncio

from .processor import dataset_processor
from .scanner.scanner_factory import ScannerFactory
from ..common.catalog_repo import catalog_repo
from ..common.datatypes import DataCatalog, Dataset
from ..common.config import config
from ..common.store import store
from ..common.filters import CatalogFilter, CatalogFilterById, \
    DatasetFilter, DatasetFilterById, DatasetFilterNew, DatasetFilterForce, DatasetFilterIncomplete
from ..common.db import db


class ODDSBackend:
    
    catalogs: list[DataCatalog]

    def __init__(self):
        self.scanner_factory = ScannerFactory()
        self.catalogs = catalog_repo.load_catalogs()

    async def scan(self, catalogFilter: CatalogFilter, datasetFilterCls, *datasetFilterArgs) -> None:
        dataset_processor.set_concurrency(config.dataset_processor_concurrency_limit or 3)
        for catalog_idx, catalog in enumerate(self.catalogs):
            if await catalogFilter.include(catalog):
                await db.storeDataCatalog(catalog)
                scanner = self.scanner_factory.create_scanner(catalog)
                if scanner:
                    dataset_idx = 0
                    async for dataset in scanner.scan():
                        ctx = f'{catalog.id}[{catalog_idx}]/{dataset.id}[{dataset_idx}]'
                        existing = await store.getDataset(dataset.storeId())
                        if existing:
                            existing.merge(dataset)
                            dataset = existing
                        await db.storeDataset(dataset, ctx)
                        datasetFilter = datasetFilterCls(catalog, dataset, *datasetFilterArgs)
                        if await datasetFilter.consider():
                            dataset_processor.queue(dataset, catalog, datasetFilter, ctx)
                        else:
                            if config.debug:
                                print(f'{ctx}:SKIP DATASET')
                        dataset_idx += 1
            else:
                if config.debug:
                    print(f'{catalog.id}[{i}]:SKIP CATALOG')
        await dataset_processor.wait()

    def scan_required(self) -> None:
        asyncio.run(self.scan(CatalogFilter(), DatasetFilterIncomplete))

    def scan_all(self) -> None:
        asyncio.run(self.scan(CatalogFilter(), DatasetFilterForce))

    def scan_new(self) -> None:
        asyncio.run(self.scan(CatalogFilter(), DatasetFilterNew))

    def scan_specific(self, catalogId: str = None, datasetId: str = None) -> None:
        if catalogId:
            catalogFilter = CatalogFilterById(catalogId)
        else:
            catalogFilter = CatalogFilter()
        args = []
        if datasetId:
            datasetFilter = DatasetFilterById
        else:
            datasetFilter = DatasetFilter
        asyncio.run(self.scan(catalogFilter, datasetFilter, args))