from contextlib import asynccontextmanager
import hashlib
import json
import dataclasses

import aioboto3

from ...config import config, CACHE_DIR
from ..metadata_store import MetadataStore
from ...datatypes import Dataset, Embedding, Resource, Field
from ...realtime_status import realtime_status as rts


class S3MetadataStore(MetadataStore):

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

    async def storeDataset(self, dataset: Dataset, ctx: str) -> None:
        async with self.bucket() as bucket:
            id = dataset.storeId()
            key = self.get_key('dataset', id, 'json')
            rts.set(ctx, f'STORING DATASET {dataset.title} -> {key}')
            obj = await bucket.Object(key)
            await obj.put(Body=json.dumps(dataclasses.asdict(dataset), indent=2, ensure_ascii=False).encode('utf-8'))
        
    async def getDataset(self, datasetId: str) -> Dataset:
        async with self.bucket() as bucket:
            key = self.get_key('dataset', datasetId, 'json')
            try:
                obj = await bucket.Object(key)
                await obj.load()
            except Exception as e:
                return None
            try:
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
            except Exception as e:
                print('FAILED TO LOAD', key, e)
                return None
    
    async def hasDataset(self, datasetId: str) -> bool:
        async with self.bucket() as bucket:
            key = self.get_key('dataset', datasetId, 'json')
            obj = await bucket.Object(key)
            try:
                await obj.load()
                return True
            except:
                return False

    async def findDatasets(self, embedding: Embedding) -> list[Dataset]:
        return []
    
    def get_key(self, kind, id, suffix):
        hash = hashlib.md5(id.encode()).hexdigest()[:16]
        return f'{kind}/{hash[:2]}/{hash[2:4]}/{hash}.{suffix}'
