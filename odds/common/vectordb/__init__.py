from .indexer import Indexer
from ..select import select
from ..embedder import embedder
from .chromadb.chromadb_indexer import ChromaDBIndexer

indexer: Indexer = select('Indexer', locals())(embedder.vector_size())