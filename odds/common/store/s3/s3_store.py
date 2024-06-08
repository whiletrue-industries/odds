from contextlib import asynccontextmanager
import tempfile
import hashlib
import json
import numpy as np
import dataclasses
from io import BytesIO

import aioboto3

from ...config import config
from ..store import Store
from ...datatypes import Dataset, Embedding, Resource, Field
from ...realtime_status import realtime_status as rts


class S3Store(Store):

    def __init__(self) -> None:
        self.session = aioboto3.Session()

    @asynccontextmanager
    async def bucket(self):
        async with self.session.resource(
            's3',
            aws_access_key_id=config.credentials.s3_store.access_key_id,
            aws_secret_access_key=config.credentials.s3_store.secret_access_key,
            region_name=config.credentials.s3_store.region,
            endpoint_url=config.credentials.s3_store.endpoint_url,
        ) as s3:
            yield s3, await s3.Bucket(config.credentials.s3_store.bucket)

    async def storeDataset(self, dataset: Dataset, ctx: str) -> None:
        async with self.bucket() as (s3, bucket):
            id = dataset.storeId()
            key = self.get_key('dataset', id, 'json')
            rts.set(ctx, f'STORING DATASET {dataset.title} -> {key}')
            obj = await bucket.Object(key)
            await obj.put(Body=json.dumps(dataclasses.asdict(dataset), indent=2, ensure_ascii=False).encode('utf-8'))
            # await s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(dataclasses.asdict(dataset), indent=2, ensure_ascii=False))

    async def storeDB(self, resource: Resource, dataset: Dataset, dbFile, ctx: str) -> None:
        async with self.bucket() as (s3, bucket):
            id = '{}/{}'.format(dataset.storeId(), resource.url)
            key = self.get_key('db', id, 'sqlite')
            rts.set(ctx, f'STORING RES-DB {resource.title} -> {key}')
            obj = await bucket.Object(key)
            await obj.upload_file(dbFile)

    async def storeEmbedding(self, dataset: Dataset, embedding: Embedding, ctx: str) -> None:
        async with self.bucket() as (s3, bucket):
            id = dataset.storeId()
            key = self.get_key('embedding', id, 'npy')
            rts.set(ctx, f'STORING EMBEDDING -> {key}')
            filename = BytesIO()
            np.save(filename, embedding)
            filename.seek(0)
            obj = await bucket.Object(key)
            await obj.upload_fileobj(filename)
        
    async def getDataset(self, datasetId: str) -> Dataset:
        async with self.bucket() as (s3, bucket):
            key = self.get_key('dataset', datasetId, 'json')
            try:
                obj = await bucket.Object(key)
                await obj.load()
            except Exception as e:
                print('NOT FOUND', key, e)
                return None
            content = await obj.get()
            content = await content['Body'].read()
            data = json.loads(content.decode('utf-8'))
            resources = data.pop('resources', [])
            for resource in resources:
                resource['fields'] = [Field(**f) for f in resource['fields']]
            data['resources'] = [Resource(**r) for r in resources]
            if 'embedding' in data:
                data['status_embedding'] = bool(data.pop('embedding'))
            dataset = Dataset(**data)
            return dataset
    
    async def hasDataset(self, datasetId: str) -> bool:
        async with self.bucket() as (s3, bucket):
            key = self.get_key('dataset', datasetId, 'json')
            obj = await bucket.Object(key)
            try:
                await obj.load()
                return True
            except:
                return False
    
    async def getDB(self, resource: Resource, dataset: Dataset) -> str:
        async with self.bucket() as (s3, bucket):
            id = '{}/{}'.format(dataset.storeId(), resource.url)
            key = self.get_key('db', id, 'sqlite')
            print('GETTING DB', dataset.catalogId, dataset.id, resource.title, key)
            try:
                obj = await bucket.Object(key)
                await obj.load()
                # download the file into a temporary file:
                with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{id}.sqlite') as temp:
                    await bucket.download_file(key, temp.name)
                    return temp.name
            except:
                print('DB NOT FOUND', key)
                pass
        return None
    
    async def getEmbedding(self, dataset: Dataset) -> Embedding:
        async with self.bucket() as (s3, bucket):
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
                print('EMBEDDING NOT FOUND', key)
                pass
            return None

    async def findDatasets(self, embedding: Embedding) -> list[Dataset]:
        return []
    
    def get_key(self, kind, id, suffix):
        hash = hashlib.md5(id.encode()).hexdigest()[:16]
        return f'{kind}/{hash[:2]}/{hash[2:4]}/{hash}.{suffix}'
