import asyncio

from .resource_processor import ResourceProcessor
from .meta_describer import MetaDescriber
from .dataset_embedder import DatasetEmbedder
from .dataset_indexer import DatasetIndexer
from ...common.datatypes import Dataset, DataCatalog
from ...common.store import store
from ...common.db import db
from ...common.config import config
from ...common.filters import DatasetFilter


class DatasetProcessor:

    tasks: list[asyncio.Task] = []

    def __init__(self) -> None:
        self.resource_processor = ResourceProcessor()
        self.meta_describer = MetaDescriber()
        self.embedder = DatasetEmbedder()
        self.indexer = DatasetIndexer()

    def set_concurrency(self, limit: int):
        self.resource_processor.set_concurrency_limit(limit)

    def queue(self, dataset: Dataset, catalog: DataCatalog, datasetFilter: DatasetFilter):
        print('QUEUE DATASET', catalog.id, dataset.id, dataset.title)
        self.tasks.append(asyncio.create_task(self.process(dataset, catalog, datasetFilter)))

    async def wait(self):
        await asyncio.gather(*self.tasks)

    async def process(self, dataset: Dataset, catalog: DataCatalog, datasetFilter: DatasetFilter):
        if config.debug:
            print('PROCESS DATASET', dataset.versions.get('resource_analyzer'), catalog.id, dataset.id, dataset.title)
        resources = self.prune_resources(dataset)
        if await datasetFilter.analyze():
            if len(resources) > 0:
                await asyncio.gather(
                    *[
                        self.resource_processor.process(resource, dataset, catalog)
                        for resource in resources
                    ]
                )
        else:
            if config.debug:
                print('SKIP ANALYZE', dataset.id)
        resources = [resource for resource in resources if resource.status_loaded]
        if len(resources) > 0:
            if await datasetFilter.describe():
                await self.meta_describer.describe(dataset)
            else:
                if config.debug:
                    print('SKIP DESCRIBE', dataset.id)
            if await datasetFilter.embed():
                await self.embedder.embed(dataset)
            if await datasetFilter.index():
                await self.indexer.index(dataset)
        await store.storeDataset(dataset)
        await db.storeDataset(dataset)

    def prune_resources(self, dataset: Dataset):
        resources = dataset.resources
        resources = [resource for resource in resources if ResourceProcessor.check_format(resource)]
        resource_names = {}
        for resource in resources:
            format_idx = ResourceProcessor.format_idx(resource)
            resource_names.setdefault(resource.title, format_idx)
            if resource_names[resource.title] > format_idx:
                resource_names[resource.title] = format_idx
        if config.debug:
            print('RESOURCE NAMES', dataset.title, resource_names)
        resources = [resource for resource in resources if ResourceProcessor.format_idx(resource) == resource_names[resource.title]]
        return resources