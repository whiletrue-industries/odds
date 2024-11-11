import os
import hashlib
import numpy as np

from ..store import Store
from ...config import CACHE_DIR
from ...datatypes import Dataset, Embedding, Resource
from ....common.realtime_status import realtime_status as rts

DIR = CACHE_DIR / '.fsstore'

class FSStore(Store):

    async def storeDB(self, resource: Resource, dataset: Dataset, dbFile, ctx: str) -> bool:
        id = '{}/{}'.format(dataset.storeId(), resource.url)
        filename = self.get_filename('db', id, 'sqlite')
        rts.set(ctx, f'STORING RES-DB {resource.title} -> {filename}')
        os.rename(dbFile, filename)
        return True

    async def storeEmbedding(self, dataset: Dataset, embedding: Embedding, ctx: str) -> None:
        id = dataset.storeId()
        filename = self.get_filename('embedding', id, 'npy')
        rts.set(ctx, f'STORING EMBEDDING -> {filename}')
        np.save(filename, embedding)
        
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
    
    def get_filename(self, kind, id, suffix):
        hash = hashlib.md5(id.encode()).hexdigest()[:16]
        dir = DIR / kind / hash[:2] / hash[2:4]
        dir.mkdir(parents=True, exist_ok=True)
        return dir / ('{}.{}'.format(hash, suffix))
    