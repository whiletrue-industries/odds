from ...common.config import config
from ...common.datatypes import DataCatalog
from .catalog_repo import CatalogRepo


class ConfigCatalogRepo(CatalogRepo):

    def __init__(self):
        self.catalogs = None
        self.load_catalogs()

    def load_catalogs(self) -> list[DataCatalog]:
        if self.catalogs is not None:
            return list(self.catalogs.values())
        self.catalogs = {}
        catalogs = config.catalogs
        ret = [
            DataCatalog(
                catalog['id'], catalog['kind'], catalog['url'], catalog['title'],
                description=catalog.get('description'),
                geo=catalog.get('geo'),
                http_headers=catalog.get('http_headers') or {},
                ignore_query=catalog.get('ignore_query') or False,
                fetcher_proxy=catalog.get('fetcher_proxy'),
            )
            for catalog in catalogs
        ]
        for catalog in ret:
            self.catalogs[catalog.id] = catalog
        return ret

    def get_catalog(self, catalog_id: str) -> DataCatalog:
        return self.catalogs.get(catalog_id)