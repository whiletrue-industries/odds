
from ...common.datatypes import Dataset, Embedding
from ...common.embedder import embedder
from ...common.store import store
from ...common.config import config


class DatasetEmbedder:

    async def embed(self, dataset: Dataset) -> None:
        print('EMBEDDING', dataset.id, dataset.better_title)
        embedding: Embedding = await embedder.embed(dataset.better_title)
        dataset.status_embedding = embedding is not None
        if dataset.status_embedding:
            await store.storeEmbedding(dataset, embedding)
        dataset.versions['embedder'] = config.feature_versions.embedder
        if config.debug:
            print('EMBEDDED', dataset.id, dataset.better_title)
