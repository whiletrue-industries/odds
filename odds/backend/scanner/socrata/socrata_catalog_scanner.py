from typing import AsyncIterator
import httpx

from ....common.config import config
from ....common.datatypes import Dataset, DataCatalog
from ....common.datatypes_socrata import SocrataResource
from ....common.retry import Retry
from ....common.realtime_status import realtime_status as rts
from ..catalog_scanner import CatalogScanner

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0'
}

class SocrataCatalogScanner(CatalogScanner):

    def __init__(self, catalog: DataCatalog, ctx: str):
        self.catalog = catalog
        self.ctx = ctx

    def done(self, num_rows):
        if config.limit_catalog_datasets and num_rows >= config.limit_catalog_datasets:
            return True
        return False

    async def scan(self) -> AsyncIterator[Dataset]:
        num_rows = 0
        async with httpx.AsyncClient() as client:
            headers.update(self.catalog.http_headers)
            domain = self.catalog.url.split('//')[1].split('/')[0]
            while True:
                if config.debug:
                    rts.set(self.ctx, f"Getting offset {num_rows} of datasets from {self.catalog.url}")
                try:
                    r = await Retry()(client, 'get',
                        f"{self.catalog.url}/api/catalog/v1", params={"domains": domain, "offset": num_rows},
                        headers=headers,
                        timeout=240
                    )
                    r.raise_for_status()
                    r = r.json()
                except Exception as e:
                    rts.set(self.ctx, f"Error getting offset {num_rows} of datasets from {self.catalog.url}: {e!r}", 'error')
                    raise
                rows = r['results']
                if len(rows) == 0:
                    break
                for row in rows:
                    num_rows += 1
                    resource = row['resource']
                    if resource['type'] != 'dataset':
                        continue

                    resources = [
                        SocrataResource(
                            f"{self.catalog.url}/resource/{resource['id']}.csv",
                            'csv',
                            title=resource['name'],
                        )
                    ]
                    # print(resource)
                    dataset = Dataset(
                        self.catalog.id, resource['id'], resource['name'],
                        description=resource['description'],
                        publisher=resource['attribution'],
                        resources=resources
                    )
                    yield dataset
                    if self.done(num_rows):
                        break
                if self.done(num_rows):
                    break
