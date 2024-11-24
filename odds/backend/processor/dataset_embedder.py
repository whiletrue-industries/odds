
import asyncio
from ...common.datatypes import Dataset, Embedding
from ...common.embedder import embedder
from ...common.store import store
from ...common.config import config
from ...common.realtime_status import realtime_status as rts


class DatasetEmbedder:

    CHUNK_SIZE = 256
    OVERLAP_SIZE = 64

    def chunks(self, content: str) -> list[str]:
        return [content[i:i + self.CHUNK_SIZE] for i in range(0, len(content), self.CHUNK_SIZE - self.OVERLAP_SIZE)]

    async def embed(self, dataset: Dataset, ctx: str) -> None:
        rts.set(ctx, f'EMBEDDING {dataset.better_title}')
        embedding: Embedding = await embedder.embed(dataset.better_title)
        for resource in dataset.resources:
            if resource.content:
                chunks = self.chunks(resource.content)
                embeddings = await asyncio.gather(*[embedder.embed(chunk) for chunk in chunks])
                embeddings = [dict(embeddings=embedding.tolist()) for embedding in embeddings if embedding is not None]
                resource.chunks = embeddings
        dataset.status_embedding = embedding is not None
        if dataset.status_embedding:
            await store.storeEmbedding(dataset, embedding, ctx)
        dataset.versions['embedder'] = config.feature_versions.embedder
        if config.debug:
            rts.set(ctx, f'EMBEDDED {dataset.better_title}')
