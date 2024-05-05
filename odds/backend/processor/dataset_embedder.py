
from ...common.datatypes import Dataset, Embedding
from ...common.embedder import embedder
from ...common.store import store
from ...common.config import config
from ...common.realtime_status import realtime_status as rts


class DatasetEmbedder:

    async def embed(self, dataset: Dataset, ctx: str) -> None:
        rts.set(ctx, f'EMBEDDING {dataset.better_title}')
        embedding: Embedding = await embedder.embed(dataset.better_title)
        dataset.status_embedding = embedding is not None
        if dataset.status_embedding:
            await store.storeEmbedding(dataset, embedding, ctx)
        dataset.versions['embedder'] = config.feature_versions.embedder
        if config.debug:
            rts.set(ctx, f'EMBEDDED {dataset.better_title}')
