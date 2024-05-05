
from ...common.datatypes import Dataset, Embedding
from ...common.vectordb import indexer
from ...common.store import store
from ...common.config import config
from ...common.realtime_status import realtime_status as rts


class DatasetIndexer:

    async def index(self, dataset: Dataset, ctx: str) -> None:
        rts.set(ctx, f'INDEXING {dataset.better_title}')
        embedding: Embedding = dataset.getEmbedding() or await store.getEmbedding(dataset)
        if embedding is None:
            rts.set(ctx, f'NO EMBEDDING {dataset.better_title}')
            return
        dataset.setEmbedding(embedding)
        await indexer.index(dataset, embedding)
        dataset.status_indexing = True
        dataset.versions['indexer'] = config.feature_versions.indexer
        if config.debug:
            rts.set(ctx, f'INDEXED {dataset.better_title}')
