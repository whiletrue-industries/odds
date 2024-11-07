from ...common.datatypes import DataCatalog

from .catalog_scanner import CatalogScanner
from .ckan.ckan_catalog_scanner import CKANCatalogScanner
from .socrata.socrata_catalog_scanner import SocrataCatalogScanner


class ScannerFactory:

    def create_scanner(self, catalog: DataCatalog, ctx: str) -> CatalogScanner:
        if catalog.kind == 'CKAN':
            return CKANCatalogScanner(catalog, ctx)
        if catalog.kind == 'Socrata':
            return SocrataCatalogScanner(catalog, ctx)