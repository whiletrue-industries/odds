from .datatypes import DataCatalog, Dataset
from .store import store
from .config import config


class DatasetFilter:

    def __init__(self, catalog: DataCatalog, dataset: Dataset):
        self.catalog = catalog
        self.dataset = dataset
        self.analyzed = False
        self.described = False
        self.embedded = False
        self.indexed = False

    async def consider(self) -> bool:
        return True

    async def analyze(self) -> bool:
        # print('FILTER ANALYZE', dataset.id, len(dataset.resources), all([not r.status_selected for r in dataset.resources]), dataset.versions.get('resource_analyzer') != config.feature_versions.resource_analyzer)
        self.analyzed = (
            len(self.dataset.resources) and 
            all([not r.status_selected for r in self.dataset.resources])
        ) or self.dataset.versions.get('resource_analyzer') != config.feature_versions.resource_analyzer
        return self.analyzed

    async def describe(self) -> bool:
        # print('FILTER DESCRIBE', dataset.id, dataset.better_title is None, dataset.better_description is None, dataset.versions.get('meta_describer') != config.feature_versions.meta_describer)
        self.described = (
            self.analyzed or
            self.dataset.better_title is None or 
            self.dataset.better_description is None or
            self.dataset.versions.get('meta_describer') != config.feature_versions.meta_describer
        )
        return self.described

    async def embed(self) -> bool:
        # print('FILTER EMBED', dataset.id, dataset.embedding is None, dataset.versions.get('embedder') != config.feature_versions.embedder)
        self.embedded = self.dataset.better_title is not None and (
            self.described or
            self.dataset.status_embedding is None or
            self.dataset.versions.get('embedder') != config.feature_versions.embedder or
            await store.getEmbedding(self.dataset) is None
        )
        return self.embedded
    
    async def index(self) -> bool:
        self.indexed = self.embedded or not self.dataset.status_indexing or self.dataset.versions.get('indexer') != config.feature_versions.indexer
        return self.indexed


class DatasetFilterNew(DatasetFilter):

    async def consider(self) -> bool:
        return not await store.hasDataset(self.dataset.storeId())


class DatasetFilterForce(DatasetFilter):

    async def analyze(self) -> bool:
        return True


class DatasetFilterById(DatasetFilterForce):
    def __init__(self, catalog: DataCatalog, dataset: Dataset, datasetId: str):
        super().__init__(catalog, dataset)
        self.datasetId = datasetId

    async def consider(self) -> bool:
        return self.dataset.id == self.datasetId


class DatasetFilterIncomplete(DatasetFilter):

    async def consider(self) -> bool:
        dataset = await store.getDataset(self.dataset.storeId())
        if dataset is None:
            return True
        if await self.analyze():
            return True
        if await self.describe():
            return True
        if await self.embed():
            return True
        if await self.index():
            return True
        return False


class CatalogFilter:

    async def include(self, catalog: DataCatalog) -> bool:
        return True
    
class CatalogFilterById(CatalogFilter):
    def __init__(self, catalogId: str):
        self.catalogId = catalogId

    async def include(self, catalog: DataCatalog) -> bool:
        return catalog.id == self.catalogId
