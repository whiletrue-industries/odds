import chromadb
import httpx
from pathlib import Path
import os

from ...config import config
from ...datatypes import Embedding, Dataset

DIRNAME = Path(__file__).parent.parent.parent.parent / '.chromadb'
os.makedirs(DIRNAME, exist_ok=True)

class ChromaDBIndexer:

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
    
    async def findDatasets(self, embedding: Embedding, num=10) -> list[str]:
        ret = self.collection.query(
            query_embeddings=[embedding.tolist()],
            n_results=num,
        )
        return ret.get('ids')[0] if ret and ret.get('ids') else []
