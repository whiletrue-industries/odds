from pathlib import Path
import os
import hashlib
import json
import numpy as np
import dataclasses

from ..store import Store
from ...config import CACHE_DIR
from ...datatypes import Dataset, Embedding, Resource, Field
from ....common.realtime_status import realtime_status as rts

DIR = CACHE_DIR / '.fsstore'

class FSStore(Store):

    async def storeDataset(self, dataset: Dataset, ctx: str) -> None:
        id = dataset.storeId()
        filename = self.get_filename('dataset', id, 'json')
        rts.set(ctx, f'STORING DATASET {dataset.title} -> {filename}')
        with open(filename, 'w') as file:
            json.dump(dataclasses.asdict(dataset), file, indent=2, ensure_ascii=False)

    async def storeDB(self, resource: Resource, dataset: Dataset, dbFile, ctx: str) -> None:
        id = '{}/{}'.format(dataset.storeId(), resource.url)
        filename = self.get_filename('db', id, 'sqlite')
        rts.set(ctx, f'STORING RES-DB {resource.title} -> {filename}')
        os.rename(dbFile, filename)

    async def storeEmbedding(self, dataset: Dataset, embedding: Embedding, ctx: str) -> None:
        id = dataset.storeId()
        filename = self.get_filename('embedding', id, 'npy')
        rts.set(ctx, f'STORING EMBEDDING -> {filename}')
        np.save(filename, embedding)
        
    async def getDataset(self, datasetId: str) -> Dataset:
        filename = self.get_filename('dataset', datasetId, 'json')
        if filename.exists():
            with open(filename) as file:
                data = json.load(file)
                resources = data.pop('resources', [])
                for resource in resources:
                    resource['fields'] = [Field(**f) for f in resource['fields']]
                data['resources'] = [Resource(**r) for r in resources]
                if 'embedding' in data:
                    data['status_embedding'] = bool(data.pop('embedding'))
                dataset = Dataset(**data)
                return dataset
        return None
    
    async def hasDataset(self, datasetId: str) -> bool:
        filename = self.get_filename('dataset', datasetId, 'json')
        return filename.exists()
    
    async def getDB(self, resource: Resource, dataset: Dataset) -> str:
        id = '{}/{}'.format(dataset.storeId(), resource.url)
        filename = self.get_filename('db', id, 'sqlite')
        print('GETTING DB', dataset.catalogId, dataset.id, resource.title, filename)
        return filename
    
    async def getEmbedding(self, dataset: Dataset) -> Embedding:
        id = dataset.storeId()
        filename = self.get_filename('embedding', id, 'npy')
        if filename.exists():
            return np.load(filename)
        return None

    async def findDatasets(self, embedding: Embedding) -> list[Dataset]:
        return []
    
    def get_filename(self, kind, id, suffix):
        hash = hashlib.md5(id.encode()).hexdigest()[:16]
        dir = DIR / kind / hash[:2] / hash[2:4]
        dir.mkdir(parents=True, exist_ok=True)
        return dir / ('{}.{}'.format(hash, suffix))