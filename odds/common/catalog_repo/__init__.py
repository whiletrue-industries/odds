from ...common.select import select
from .config_catalog_repo import ConfigCatalogRepo
from .catalog_repo import CatalogRepo


catalog_repo: CatalogRepo = select('CatalogRepo', locals())()