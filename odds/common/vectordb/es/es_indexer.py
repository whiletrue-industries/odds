from ...metadata_store.dataset_factory import dataset_factory
from ...datatypes import Embedding, Dataset
from ...metadata_store.es.es_client import ESClient
from ...metadata_store.es.es_metadata_store import ES_INDEX
from ..indexer import Indexer

import json

class ESIndexer(Indexer):

    def __init__(self, vector_size) -> None:
        pass

    async def index(self, dataset: Dataset, embedding: Embedding) -> None:
        # update the embedding field in the document in the ES index:
        pass
    
    async def findDatasets(self, embedding: Embedding, query, num=10, catalog_ids: list[str] | None=None) -> list[str]:
        async with ESClient() as es:
            # search for the nearest neighbors of the given embedding in the ES
            # index and return the ids of the datasets:
            text_match=dict(
                multi_match=dict(
                    query=query,
                    fields=["title", "description", "summary", "better_title", "better_description", "publisher", "publisher_description", "link", "resource.content"],
                    boost=0.2,
                    type='cross_fields',
                    operator='or',
                ),
            )
            knn=dict(
                knn=dict(
                    field="embeddings",
                    query_vector=embedding.tolist(),
                    k=10,
                    num_candidates=50,
                    boost=0.8
                )
            )
            chunks=dict(
                knn=dict(
                    field="resources.chunks.embeddings",
                    query_vector=embedding.tolist(),
                    k=10,
                    num_candidates=50,
                    boost=0.5
                )
            )

            query=dict(
                bool=dict(
                    should=[text_match, knn, chunks],
                    minimum_should_match=1,
                )
            )

            if catalog_ids is not None:
                query['bool']['filter'] = [
                    dict(terms=dict(catalogId=catalog_ids))
                ]

            results = await es.search(index=ES_INDEX, query=query, size=num)
            datasets = [hit['_source'] for hit in results['hits']['hits']]
            return [dataset_factory(dataset) for dataset in datasets]
