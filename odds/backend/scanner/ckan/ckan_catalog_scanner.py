from typing import AsyncIterator
import httpx
import json

from ....common.config import config
from ....common.datatypes import Dataset, Resource, DataCatalog
from ....common.retry import Retry
from ....common.realtime_status import realtime_status as rts
from ..catalog_scanner import CatalogScanner
from urllib.parse import quote


class CKANCatalogScanner(CatalogScanner):

    def __init__(self, catalog: DataCatalog, ctx: str):
        self.catalog = catalog
        self.ctx = ctx

    def done(self, num_rows):
        if config.limit_catalog_datasets and num_rows >= config.limit_catalog_datasets:
            return True
        return False

    async def scan(self) -> AsyncIterator[Dataset]:
        page = 1
        num_rows = 0
        async with httpx.AsyncClient() as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0'
            }
            headers.update(self.catalog.http_headers)
            while True:
                if config.debug:
                    rts.set(self.ctx, f"Getting page {page} of datasets from {self.catalog.url}")
                try:
                    if self.catalog.fetcher_proxy:
                        url = f"{self.catalog.url}/api/3/action/package_search?rows=100&start={(page - 1) * 100}"
                        url = f"{self.catalog.fetcher_proxy}/fetch"
                        params = dict(raw=1, url=url)
                    else:
                        url = f"{self.catalog.url}/api/3/action/package_search"
                        params = dict(rows=100, start=(page - 1) * 100)
                    r = await Retry()(client, 'get',
                        url, params=params,
                        headers=headers,
                        timeout=240
                    )
                    r.raise_for_status()
                    r = r.json()
                except Exception as e:
                    rts.set(self.ctx, f"Error getting page {page} of datasets from {self.catalog.url}: {e!r}", 'error')
                    raise
                rows = r['result']['results']
                if len(rows) == 0:
                    break
                for row in rows:
                    resources = []
                    for resource in row['resources']:
                        resource_url = resource['url'].replace('datacity.jerusalem.muni.il', 'jerusalem.datacity.org.il')
                        if self.catalog.fetcher_proxy:
                            resource_url = quote(resource_url)
                            resource_url = f"{self.catalog.fetcher_proxy}/fetch?raw=1&url={resource_url}"
                        resources.append(
                            Resource(
                                resource_url,
                                resource['format'],
                                title=resource['name'],
                            )
                        )
                    dataset = Dataset(
                        self.catalog.id, row['name'], row['title'], 
                        description=row.get('notes') or '',
                        publisher=row.get('organization', {}).get('title'),
                        publisher_description=row.get('organization', {}).get('description'),
                        resources=resources
                    )
                    yield dataset
                    num_rows += 1
                    if self.done(num_rows):
                        break
                if self.done(num_rows):
                    break
                page += 1