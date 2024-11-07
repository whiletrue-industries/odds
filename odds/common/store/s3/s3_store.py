from contextlib import asynccontextmanager
import hashlib
import numpy as np
from io import BytesIO

import aioboto3

from ...config import config, CACHE_DIR
from ..store import Store
from ...datatypes import Dataset, Embedding, Resource
from ...realtime_status import realtime_status as rts


class S3Store(Store):

    def __init__(self) -> None:
        self.session = aioboto3.Session()
        self.cachedir = CACHE_DIR / 's3-temp'
        self.cachedir.mkdir(exist_ok=True, parents=True)

    @asynccontextmanager
    async def bucket(self):
        async with self.session.resource(
            's3',
            aws_access_key_id=config.credentials.s3_store.access_key_id,
            aws_secret_access_key=config.credentials.s3_store.secret_access_key,
            region_name=config.credentials.s3_store.region,
            endpoint_url=config.credentials.s3_store.endpoint_url,
        ) as s3:
            yield await s3.Bucket(config.credentials.s3_store.bucket)

    async def storeDB(self, resource: Resource, dataset: Dataset, dbFile, ctx: str) -> None:
        async with self.bucket() as bucket:
            id = '{}/{}'.format(dataset.storeId(), resource.url)
            key = self.get_key('db', id, 'sqlite')
            rts.set(ctx, f'STORING RES-DB {resource.title} -> {key}')
            obj = await bucket.Object(key)
            await obj.upload_file(dbFile)

    async def storeEmbedding(self, dataset: Dataset, embedding: Embedding, ctx: str) -> None:
        async with self.bucket() as bucket:
            id = dataset.storeId()
            key = self.get_key('embedding', id, 'npy')
            rts.set(ctx, f'STORING EMBEDDING -> {key}')
            filename = BytesIO()
            np.save(filename, embedding)
            filename.seek(0)
            obj = await bucket.Object(key)
            await obj.upload_fileobj(filename)

    async def getDB(self, resource: Resource, dataset: Dataset) -> str:
        async with self.bucket() as bucket:
            id = '{}/{}'.format(dataset.storeId(), resource.url)
            key = self.get_key('db', id, 'sqlite')
            print('GETTING DB', dataset.catalogId, dataset.id, resource.title, key)
            try:
                obj = await bucket.Object(key)
                await obj.load()
                # download the file into a temporary file:
                key = key.replace('/', '_')
                outfile = self.cachedir / f'{key}.sqlite'
                if not outfile.exists():
                    await obj.download_file(str(outfile))
                return str(outfile)
            except Exception as e:
                pass
        return None
    
    async def getEmbedding(self, dataset: Dataset) -> Embedding:
        async with self.bucket() as bucket:
            id = dataset.storeId()
            key = self.get_key('embedding', id, 'npy')
            try:
                obj = await bucket.Object(key)
                await obj.load()
                content = await obj.get()
                content = await content['Body'].read()
                filename = BytesIO(content)
                return np.load(filename)
            except:
                pass
            return None

    def get_key(self, kind, id, suffix):
        hash = hashlib.md5(id.encode()).hexdigest()[:16]
        return f'{kind}/{hash[:2]}/{hash[2:4]}/{hash}.{suffix}'
