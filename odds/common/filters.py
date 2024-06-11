from .datatypes import DataCatalog, Dataset
from .store import store
from .config import config


class DatasetFilter:
    async def consider(self, dataset: Dataset) -> bool:
        return False
    
    async def analyze(self, dataset: Dataset) -> bool:
        return True
    
    async def describe(self, dataset: Dataset) -> bool:
        return True
    
    async def embed(self, dataset: Dataset) -> bool:
        return True
    
    async def index(self, dataset: Dataset) -> bool:
        return True
    

class DatasetFilterIncomplete(DatasetFilter):

    def __init__(self) -> None:
        super().__init__()

    async def consider(self, dataset: Dataset) -> bool:
        if await self.analyze(dataset):
            return True
        if await self.describe(dataset):
            return True
        if await self.embed(dataset):
            return True
        if await self.index(dataset):
            return True

    async def analyze(self, dataset: Dataset) -> bool:
        # print('FILTER ANALYZE', dataset.id, len(dataset.resources), all([not r.status_selected for r in dataset.resources]), dataset.versions.get('resource_analyzer') != config.feature_versions.resource_analyzer)
        return (
            len(dataset.resources) and 
            any([(r.status_selected and not r.status_loaded) for r in dataset.resources])
        ) or dataset.versions.get('resource_analyzer') != config.feature_versions.resource_analyzer

    async def describe(self, dataset: Dataset) -> bool:
        # print('FILTER DESCRIBE', dataset.id, dataset.better_title is None, dataset.better_description is None, dataset.versions.get('meta_describer') != config.feature_versions.meta_describer)
        return (
            dataset.better_title is None or 
            dataset.better_description is None or
            dataset.versions.get('meta_describer') != config.feature_versions.meta_describer
        )

    async def embed(self, dataset: Dataset) -> bool:
        # print('FILTER EMBED', dataset.id, dataset.embedding is None, dataset.versions.get('embedder') != config.feature_versions.embedder)
        return dataset.better_title is not None and (
            dataset.status_embedding is None or
            dataset.versions.get('embedder') != config.feature_versions.embedder or
            await store.getEmbedding(dataset) is None
        )
    
    async def index(self, dataset: Dataset) -> bool:
        return not dataset.status_indexing or dataset.versions.get('indexer') != config.feature_versions.indexer


class DatasetFilterNew(DatasetFilter):

    async def consider(self, dataset: Dataset) -> bool:
        return not await store.hasDataset(self.dataset.storeId())


class DatasetFilterForce(DatasetFilter):

    async def consider(self, dataset: Dataset) -> bool:
        return True


class DatasetFilterById(DatasetFilter):
    def __init__(self, datasetId: str):
        super().__init__()
        self.datasetId = datasetId

    async def consider(self, dataset: Dataset) -> bool:
        return dataset.id == self.datasetId


class CatalogFilter:

    async def include(self, catalog: DataCatalog) -> bool:
        return True
    
class CatalogFilterById(CatalogFilter):
    def __init__(self, catalogId: str):
        self.catalogId = catalogId

    async def include(self, catalog: DataCatalog) -> bool:
        return catalog.id == self.catalogId
