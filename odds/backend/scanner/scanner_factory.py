from ...common.datatypes import DataCatalog

from .catalog_scanner import CatalogScanner
from .ckan.ckan_catalog_scanner import CKANCatalogScanner
from .socrata.socrata_catalog_scanner import SocrataCatalogScanner
from .website.website_scanner import WebsiteCatalogScanner
from .worldbank.worldbank_catalog_scanner import WorldBankCatalogScanner
from .arcgis.arcgis_catalog_scanner import ArcGISCatalogScanner


class ScannerFactory:

    def create_scanner(self, catalog: DataCatalog, ctx: str) -> CatalogScanner:
        if catalog.kind == 'CKAN':
            return CKANCatalogScanner(catalog, ctx)
        if catalog.kind == 'Socrata':
            return SocrataCatalogScanner(catalog, ctx)
        if catalog.kind == 'website':
            return WebsiteCatalogScanner(catalog, ctx)
        if catalog.kind == 'worldbank':
            return WorldBankCatalogScanner(catalog, ctx)
        if catalog.kind == 'arcgis':
            return ArcGISCatalogScanner(catalog, ctx)
