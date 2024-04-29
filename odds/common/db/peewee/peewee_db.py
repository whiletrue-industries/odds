from ..db import DBStorage
from ...datatypes import DataCatalog, Dataset, Resource

from .models import Catalog as CatalogModel, Dataset as DatasetModel, Resource as ResourceModel
from .base_model import db

class PeeweeDBStorage(DBStorage):

    def __init__(self) -> None:
        db.create_tables([CatalogModel, DatasetModel, ResourceModel])

    def storeResource(self, dataset_id, resource: Resource) -> None:
        params = dict(
            file_format=resource.file_format,
            title=resource.title,
            row_count=resource.row_count,
            db_schema=resource.db_schema,
            status_selected=resource.status_selected,
            status_loaded=resource.status_loaded,
            loading_error=resource.loading_error,
            dataset=dataset_id,
        )
        ResourceModel.insert(url=resource.url, **params)\
            .on_conflict('update', update=params, conflict_target=(ResourceModel.url,))\
            .execute()


    async def storeDataset(self, dataset: Dataset) -> None:
        print('SAVING DATASET', dataset.catalogId, dataset.id, dataset.title)
        params = dict(
            catalogId=dataset.catalogId,
            title=dataset.title,
            description=dataset.description,
            publisher=dataset.publisher,
            publisher_description=dataset.publisher_description,
            status_embedding=dataset.status_embedding,
            status_indexing=dataset.status_indexing,
            better_title=dataset.better_title,
            better_description=dataset.better_description,
            versions=dataset.versions,
        )
        DatasetModel.insert(id=dataset.storeId(), **params)\
            .on_conflict('update', update=params, conflict_target=(DatasetModel.id,))\
            .execute()
        current_urls = set()
        for resource in dataset.resources:
            self.storeResource(dataset.storeId(), resource)
            current_urls.add(resource.url)
        ResourceModel.delete().where(ResourceModel.dataset == dataset.storeId()).where(ResourceModel.url.not_in(current_urls)).execute()

    async def storeDataCatalog(self, catalog: DataCatalog) -> None:
        print('SAVING DATA CATALOG', catalog.id)
        params = dict(
            kind=catalog.kind,
            url=catalog.url,
            title=catalog.title,
            description=catalog.description,
            geo=catalog.geo,
            http_headers=catalog.http_headers,
        )
        CatalogModel.insert(id=catalog.id, **params)\
            .on_conflict('update', update=params, conflict_target=(CatalogModel.id,))\
            .execute()

    async def getDataset(self, datasetId: str) -> Dataset:
        return None

    async def hasDataset(self, datasetId: str) -> bool:
        return False