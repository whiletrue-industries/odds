from ...common.datatypes import DataCatalog

from .catalog_scanner import CatalogScanner
from .ckan.ckan_catalog_scanner import CKANCatalogScanner


class ScannerFactory:

    def create_scanner(self, catalog: DataCatalog) -> CatalogScanner:
        if catalog.kind == 'CKAN':
            return CKANCatalogScanner(catalog)