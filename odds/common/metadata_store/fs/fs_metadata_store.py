import hashlib
import json
import dataclasses

from ..metadata_store import MetadataStore
from ...config import CACHE_DIR
from ...datatypes import Dataset, Resource, Field
from ...datatypes_socrata import SocrataResource
from ...realtime_status import realtime_status as rts

DIR = CACHE_DIR / '.fsstore'

class FSMetadataStore(MetadataStore):

    async def storeDataset(self, dataset: Dataset, ctx: str) -> None:
        id = dataset.storeId()
        filename = self.get_filename('dataset', id, 'json')
        rts.set(ctx, f'STORING DATASET {dataset.title} -> {filename}')
        with open(filename, 'w') as file:
            json.dump(dataclasses.asdict(dataset), file, indent=2, ensure_ascii=False)
        
    async def getDataset(self, datasetId: str) -> Dataset:
        filename = self.get_filename('dataset', datasetId, 'json')
        if filename.exists():
            with open(filename) as file:
                data = json.load(file)
                resources = data.pop('resources', [])
                for resource in resources:
                    resource['fields'] = [Field(**f) for f in resource['fields']]
                data['resources'] = [self.resource_factory(**r) for r in resources]
                if 'embedding' in data:
                    data['status_embedding'] = bool(data.pop('embedding'))
                dataset = Dataset(**data)
                return dataset
        return None
    
    async def hasDataset(self, datasetId: str) -> bool:
        filename = self.get_filename('dataset', datasetId, 'json')
        return filename.exists()

    # async def findDatasets(self, embedding: Embedding) -> list[Dataset]:
    #     return []
    
    def get_filename(self, kind, id, suffix):
        hash = hashlib.md5(id.encode()).hexdigest()[:16]
        dir = DIR / kind / hash[:2] / hash[2:4]
        dir.mkdir(parents=True, exist_ok=True)
        return dir / ('{}.{}'.format(hash, suffix))
    
    def resource_factory(self, **data):
        if data.get('kind') == 'socrata':
            return SocrataResource(**data)
        return Resource(**data)