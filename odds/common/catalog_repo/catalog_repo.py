from ...common.datatypes import DataCatalog


class CatalogRepo:

    def load_catalogs(self) -> list[DataCatalog]:
        pass

    def get_catalog(self, catalog_id: str) -> DataCatalog:
        pass