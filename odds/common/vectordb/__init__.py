from .indexer import Indexer
from ..select import select
from ..embedder import embedder
from .chromadb.chromadb_indexer import ChromaDBIndexer
from .es.es_indexer import ESIndexer

indexer: Indexer = select('Indexer', locals())(embedder.vector_size())