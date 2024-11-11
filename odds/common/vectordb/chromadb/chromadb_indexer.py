import chromadb
import httpx
from pathlib import Path
import os

from ...config import config, CACHE_DIR
from ...datatypes import Embedding, Dataset
from ..indexer import Indexer
from ...metadata_store import metadata_store

DIRNAME = CACHE_DIR / '.chromadb'
os.makedirs(DIRNAME, exist_ok=True)

class ChromaDBIndexer(Indexer):

    COLLECTION_NAME = 'datasets'

    def __init__(self, vector_size) -> None:
        self.client = chromadb.PersistentClient(path=str(DIRNAME))
        self.collection = self.client.create_collection(
            name=self.COLLECTION_NAME, get_or_create=True,
            metadata={'hnsw:space': 'cosine'}
        )

    async def index(self, dataset: Dataset, embedding: Embedding) -> None:
        self.collection.upsert(
            embeddings=[embedding.tolist()],
            ids=[dataset.storeId()]
        )
    
    async def findDatasets(self, embedding: Embedding, num=10, **kw) -> list[Dataset]:
        ret = self.collection.query(
            query_embeddings=[embedding.tolist()],
            n_results=num,
        )
        ids = ret.get('ids')[0] if ret and ret.get('ids') else []
        
