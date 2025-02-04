from typing import AsyncIterator
import httpx

from ....common.config import config
from ....common.datatypes import Dataset, Resource, DataCatalog
from ....common.retry import Retry
from ....common.realtime_status import realtime_status as rts
from ..catalog_scanner import CatalogScanner
from ...settings import ALLOWED_FORMATS


class WorldBankCatalogScanner(CatalogScanner):

    def __init__(self, catalog: DataCatalog, ctx: str):
        self.catalog = catalog
        self.ctx = ctx

    def done(self, num_rows):
        if config.limit_catalog_datasets and num_rows >= config.limit_catalog_datasets:
            return True
        return False

    async def scan(self) -> AsyncIterator[Dataset]:
        skip = 0
        async with httpx.AsyncClient() as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0'
            }
            headers.update(self.catalog.http_headers)
            dataset_ids = []
            while True:
                try:
                    r = await Retry()(client, 'get',
                        f"https://datacatalogapi.worldbank.org/ddhxext/DatasetList", params={"$top": 100, "$skip": skip},
                        headers=headers,
                        timeout=240
                    )
                    r.raise_for_status()
                    r = r.json()
                except Exception as e:
                    rts.set(self.ctx, f"Error getting skip {skip} of datasets from worldbank api: {e!r}", 'error')
                    raise
                data = r.get('data', [])
                if config.debug:
                    rts.set(self.ctx, f"Getting skip {skip} of datasets from worldbank api, got {len(data)} datasets", 'info')
                dataset_ids.extend(data)
                if len(data) == 0 or self.done(len(dataset_ids)):
                    break
                skip += len(data)
            for dataset_id in dataset_ids:
                dataset_unique_id = dataset_id['dataset_unique_id']
                try:
                    r = await Retry()(client, 'get',
                        f"https://datacatalogapi.worldbank.org/ddhxext/DatasetView", params={"dataset_unique_id": dataset_unique_id},
                        headers=headers,
                        timeout=240
                    )
                    r.raise_for_status()
                    r = r.json()
                    dataset = r
                except Exception as e:
                    rts.set(self.ctx, f"Error getting dataset {dataset_unique_id} from worldbank api: {e!r}", 'error')
                    raise

                resources = [
                    Resource(
                        resource['url'],
                        resource['url'].split('?')[0].split('.')[-1],
                        title=','.join(filter(None, [resource.get('name'), resource.get('description')])),
                    )
                    for resource in dataset['Resources']
                    if resource.get('url')
                ]
                resources = list(r for r in resources if r.file_format in ALLOWED_FORMATS)
                if len(resources) == 0:
                    continue
                identification = dataset.get('identification', {})
                dataset = Dataset(
                    self.catalog.id, 
                    dataset['dataset_unique_id'], dataset['name'], 
                    description='\n'.join(filter(None, [identification.get('title'), identification.get('subtitle'), identification.get('description')])),
                    publisher=identification.get('citation'),
                    publisher_description='',
                    resources=resources
                )
                yield dataset
