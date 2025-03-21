import json
import dataclasses

from elasticsearch import Elasticsearch

from ....common.datatypes import Embedding
from ..dataset_factory import dataset_factory

from ..metadata_store import MetadataStore
from ...datatypes import Dataset
from ...realtime_status import realtime_status as rts
from ...embedder import embedder

from .es_client import ESClient

ES_INDEX = 'datasets'
MAPPING = {
    'properties': {
        'catalogId': {'type': 'keyword'},
        'id': {'type': 'keyword'},
        'title': {'type': 'text'},
        'description': {'type': 'text'},
        'publisher': {'type': 'text'},
        'publisher_description': {'type': 'text'},
        'link': {'type': 'keyword'},
        'resources': {
            'type': 'nested',
            'properties': {
                'url': {'type': 'keyword'},
                'file_format': {'type': 'keyword'},
                'title': {'type': 'text'},
                'fields': {
                    'type': 'nested',
                    'properties': {
                        'name': {'type': 'keyword'},
                        'title': {'type': 'text'},
                        'description': {'type': 'text'},
                        'data_type': {'type': 'keyword'},
                        # Don't index these:
                        'props': {'type': 'text'},
                    }
                },
                'row_count': {'type': 'integer'},
                'db_schema': {'type': 'keyword', 'index': False},
                'status_selected': {'type': 'boolean'},
                'status_loaded': {'type': 'boolean'},
                'loading_error': {'type': 'text'},
                'kind': {'type': 'keyword'},
                'content': {'type': 'text'},
                'chunks': {
                    'type': 'nested', 
                    'properties': {
                        'embeddings': {
                            'type': 'dense_vector',
                            'dims': embedder.vector_size(),
                            'index': True,
                            'similarity': 'cosine'
                        }
                    }
                }
            }
        },
        'better_title': {'type': 'text'},
        'better_description': {'type': 'text'},
        'summary': {'type': 'text'},
        'status_embedding': {'type': 'boolean'},
        'status_indexing': {'type': 'boolean'},
        'versions': {'type': 'object', 'enabled': False},
        'embeddings': {
            'type': 'dense_vector',
            'dims': embedder.vector_size(),
            'index': True,
            'similarity': 'cosine'
        }
    }
}

class ESMetadataStore(MetadataStore):

    def __init__(self):
        self.initialized = False

    async def single_time_init(self, client: Elasticsearch):
        if self.initialized:
            return
        self.initialized = True
        assert await client.ping()
        if not await client.indices.exists(index=ES_INDEX):
            await client.indices.create(index=ES_INDEX, body={
                'mappings': MAPPING
            })
        else:
            # Update mapping
            await client.indices.put_mapping(index=ES_INDEX, **MAPPING)

    async def storeDataset(self, dataset: Dataset, ctx: str) -> None:
        async with ESClient() as client:
            await self.single_time_init(client)
            id = dataset.storeId()
            rts.set(ctx, f'STORING DATASET {dataset.title} -> {id}')
            body = dataclasses.asdict(dataset)
            for resource in body['resources']:
                for field in resource['fields']:
                    props = dict()
                    for k in list(field.keys()):
                        if k not in ['name', 'data_type']:
                            props[k] = field.pop(k)
                    field['props'] = json.dumps(props, ensure_ascii=False)
            try:
                ret = await client.update(index='datasets', id=id, doc=body, doc_as_upsert=True)
            except Exception as e:
                rts.set(ctx, f'ERROR STORING DATASET {dataset.title} -> {id}: {e!r}', 'error')
                json.dump(body, open(f'/srv/.caches/error_{id}.json', 'w'))
        
    async def getDataset(self, datasetId: str) -> Dataset:
        async with ESClient() as client:
            await self.single_time_init(client)
            exists = await client.exists(index=ES_INDEX, id=datasetId)
            if exists:
                data = await client.get(index=ES_INDEX, id=datasetId)
                data = data.get('_source')
                if not data:
                    return None
                data = dict(data)
                try:
                    return dataset_factory(data)
                except Exception as e:
                    print('ERROR PARSING DATASET', datasetId, e)
                    return None
            return None
    
    async def hasDataset(self, datasetId: str) -> bool:
        async with ESClient() as client:
            await self.single_time_init(client)
            print('FETCHING DATASET', datasetId)
            return await client.exists(index=ES_INDEX, id=datasetId)

    # async def findDatasets(self, embedding: Embedding) -> list[Dataset]:
    #     return []

    async def setEmbedding(self, dataset: Dataset, embedding: Embedding):
        if hasattr(dataset, 'embedding') and (dataset.embedding is embedding):
            return
        async with ESClient() as client:
            await self.single_time_init(client)
            doc = dict(embeddings=embedding.tolist())
            ret = await client.update(
                index=ES_INDEX,
                id=dataset.storeId(),
                doc=doc,
                doc_as_upsert=True
            )
            dataset.embedding = embedding

    async def getEmbedding(self, dataset: Dataset) -> Embedding:
        return await super().getEmbedding(dataset)
