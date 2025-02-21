from typing import AsyncIterator
import httpx

from ....common.config import config
from ....common.datatypes import Dataset, DataCatalog, Resource
from ....common.retry import Retry
from ....common.realtime_status import realtime_status as rts
from ..catalog_scanner import CatalogScanner

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0'
}

class ArcGISCatalogScanner(CatalogScanner):

    def __init__(self, catalog: DataCatalog, ctx: str):
        self.catalog = catalog
        self.ctx = ctx

    def done(self, num_rows):
        if config.limit_catalog_datasets and num_rows >= config.limit_catalog_datasets:
            return True
        return False

    async def scan_aux(self, collection, filetype) -> AsyncIterator[Dataset]:
        num_rows = 0
        startindex = 1
        used_ids = set()
        async with httpx.AsyncClient() as client:
            headers.update(self.catalog.http_headers)
            while True:
                if config.debug:
                    rts.set(self.ctx, f"Getting offset {startindex-1} of datasets from {self.catalog.url}")
                try:
                    r = await Retry()(client, 'get',
                        f"{self.catalog.url}/api/search/v1/collections/{collection}/items", params={"startindex": startindex, "filter": f"type='{filetype}'"},
                        headers=headers,
                        timeout=60
                    )
                    r.raise_for_status()
                    r = r.json()
                except Exception as e:
                    rts.set(self.ctx, f"Error getting offset {startindex-1} of datasets from {self.catalog.url}: {e!r}", 'error')
                    raise
                rows = r['features']
                if len(rows) == 0:
                    break
                # print(f'XXXXX got {len(rows)} rows')
                for row in rows:
                    startindex += 1
                    id = row['id']
                    properties = row['properties']
                    if properties['type'] != filetype:
                        continue
                    if id in used_ids:
                        print(f"Skipping duplicate resource {id}")
                        continue
                    data_url = f'https://www.arcgis.com/sharing/rest/content/items/{id}/data'
                    title = row['properties']['title']
                    description = row['properties']['description']
                    filename = properties['name']
                    file_format = filename.split('.')[-1].lower()
                    publisher = properties['source']
                    link = f'{self.catalog.url}/datasets/{id}/about'

                    used_ids.add(id)
                    num_rows += 1

                    resources = [
                        Resource(
                            f'{data_url}#{filename}',
                            file_format,
                            title=filename,
                        )
                    ]
                    # print(resource)
                    dataset = Dataset(
                        self.catalog.id, id, title,
                        description=description,
                        publisher=publisher,
                        resources=resources,
                        link=link
                    )
                    yield dataset
                    if self.done(num_rows):
                        break

    async def scan(self) -> AsyncIterator[Dataset]:
        async for dataset in self.scan_aux('dataset', 'CSV'):
            yield dataset
        async for dataset in self.scan_aux('document', 'Microsoft Excel'):
            yield dataset