from pymilvus import MilvusClient, DataType
import httpx

from ...config import config
from ...datatypes import Embedding, Dataset


class MilvusIndexer:

    COLLECTION_NAME = 'datasets'

    def __init__(self, vector_size) -> None:
        self.client = MilvusClient(
            uri=config.endpoints.milvus.host,
            token=config.credentials.milvus.token,
        )
        if self.COLLECTION_NAME not in self.client.list_collections():
            self.client.create_collection(self.COLLECTION_NAME, vector_size)

    def create_collection(self, name, vector_size) -> None:
        # schema = MilvusClient.create_schema(
        #     auto_id=True,
        #     enable_dynamic_field=True,
        # )

        # schema.add_field(field_name='id', datatype=DataType.INT64, is_primary=True)
        # schema.add_field(field_name='embedding', datatype=DataType.FLOAT_VECTOR, dim=vector_size)
        # schema.add_field(field_name='dataset_id', datatype=DataType.STRING)

        # index_params = self.client.prepare_index_params()

        # index_params.add_index(
        #     field_name='id',
        #     index_type='STL_SORT'
        # )

        # index_params.add_index(
        #     field_name='embedding', 
        #     index_type='AUTOINDEX',
        #     metric_type='L2',
        #     params={'nlist': 128}
        # )

        self.client.create_collection(
            collection_name=name,
            dimension=vector_size,
            auto_id=True,
            metric_type='COSINE',
            # id_type='string',
            # schema=schema,
            # index_params=index_params
        )
        

    async def index(self, dataset: Dataset, embedding: Embedding) -> None:
        # async with httpx.AsyncClient() as client:
        #     params = {
        #         'collectionName': self.COLLECTION_NAME,
        #         'data': [{
        #             # 'dataset_id': dataset.storeId(),
        #             'vector': embedding.tolist()
        #         }]
        #     }
        #     headers = {
        #         'content-type': 'application/json',
        #     }
        #     r = await client.post(
        #         f'{config.endpoints.milvus.host}/v1/vector/insert',
        #         json=params,
        #         headers=headers,
        #         timeout=60
        #     )
        #     r.raise_for_status()
        #     print('RRR33', r.json(), params, len(params['data'][0]['vector']))
        ret = self.client.insert(collection_name=self.COLLECTION_NAME, data=[{'id': dataset.storeId(), 'vector': embedding.tolist()}])
        print('RRR33', ret)
    
    async def findDatasets(self, embedding: Embedding, num=10, **kw) -> list[Dataset]:
        async with httpx.AsyncClient() as client:
            params = {
                'collectionName': self.COLLECTION_NAME,
                'vector': embedding.tolist(),
            }
            r = await client.post(
                f'{config.endpoints.milvus.host}/v1/vector/search',
                json=params,
                timeout=60
            )
            r.raise_for_status()
            print('RRR', r.json())
            assert False
