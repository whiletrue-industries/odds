
from ...common.datatypes import Dataset, Embedding
from ...common.vectordb import indexer
from ...common.store import store
from ...common.config import config


class DatasetIndexer:

    async def index(self, dataset: Dataset, ctx: str) -> None:
        print(f'{ctx}:INDEXING', dataset.better_title)
        embedding: Embedding = dataset.getEmbedding() or await store.getEmbedding(dataset)
        if embedding is None:
            print(f'{ctx}:NO EMBEDDING', dataset.better_title)
            return
        dataset.setEmbedding(embedding)
        await indexer.index(dataset, embedding)
        dataset.status_indexing = True
        dataset.versions['indexer'] = config.feature_versions.indexer
        if config.debug:
            print(f'{ctx}:INDEXED', dataset.better_title)
