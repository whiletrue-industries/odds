import chromadb
import chromadb.api.fastapi
import chromadb.telemetry.posthog
import chromadb.utils.embedding_functions

from .base import BaseVectorDB, BaseCollection, BaseItem
from ckangpt import config


# https://github.com/nmslib/hnswlib/blob/master/ALGO_PARAMS.md

# r"^(l2|cosine|ip)$" = "l2",
# Squared L2	'l2'	d = sum((Ai-Bi)^2)
# Inner product	'ip'	d = 1.0 - sum(Ai*Bi)
# Cosine similarity	'cosine'	d = 1.0 - sum(Ai*Bi) / sqrt(sum(Ai*Ai) * sum(Bi*Bi))
HNSW_SPACE = "l2"

# r"^\d+$" = "100",
# the parameter has the same meaning as search_ef, but controls the index_time/index_accuracy.
# Bigger ef_construction leads to longer construction, but better index quality.
# At some point, increasing ef_construction does not improve the quality of the index.
# One way to check if the selection of ef_construction was ok is to measure a recall for M nearest
# neighbor search when ef =ef_construction: if the recall is lower than 0.9, than there is room for improvement.
HNSW_CONSTRUCTION_EF = 200

# r"^\d+$" = "10",
# the size of the dynamic list for the nearest neighbors (used during the search).
# Higher ef leads to more accurate but slower search.
# ef cannot be set lower than the number of queried nearest neighbors k.
# The value ef of can be anything between k and the size of the dataset.
HNSW_SEARCH_EF = 100

# r"^\d+$" = "16",
# M - the number of bi-directional links created for every new element during construction.
# Reasonable range for M is 2-100.
# Higher M work better on datasets with high intrinsic dimensionality and/or high recall,
# while low M work better for datasets with low intrinsic dimensionality and/or low recalls.
# The parameter also determines the algorithm's memory consumption, which is roughly M * 8-10 bytes per stored element.
# As an example for dim=4 random vectors optimal M for search is somewhere around 6,
# while for high dimensional datasets (word embeddings, good face descriptors),
# higher M are required (e.g. M=48-64) for optimal performance at high recall.
# The range M=12-48 is ok for the most of the use cases. When M is changed one has to update the other parameters.
# Nonetheless, ef and ef_construction parameters can be roughly estimated by assuming that M*ef_{construction} is a constant.
HNSW_M = 64

# r"^\d+$" = "4",
# Note that search with a filter works slow in python in multithreaded mode.
# It is recommended to set `num_threads=1` when doing a search, however this is not possible
# so need to experiment with this parameter, maybe fix Chroma to use a single thread only for search.
HNSW_NUM_THREADS = 4

# r"^\d+(\.\d+)?$" = "1.2",
# when number of elements exceeds max_elements, the index is resized by factor of resize_factor.
# new_size = max(self._index_metadata["elements"] * self._params.resize_factor, 1000)
HNSW_RESIZE_FACTOR = 1.5


class _FastAPI(chromadb.api.fastapi.FastAPI):

    def __init__(self, telemetry_client):
        self._api_url = config.CHROMA_SERVER_URL
        self._telemetry_client = telemetry_client


class ChromaItem(BaseItem):
    pass


class ChromaCollection(BaseCollection):

    def __init__(self, chroma_collection):
        self._collection = chroma_collection

    @property
    def name(self):
        return self._collection.name

    def add(self, items):
        self._collection.add(
            ids=[item.id for item in items],
            embeddings=[item.embeddings for item in items],
            metadatas=[item.metadata for item in items],
            documents=[item.document for item in items],
        )

    def delete(self):
        self._collection.delete()

    def reindex(self):
        self._collection.create_index()

    def get_existing_item_ids(self, item_ids):
        return self._collection.get(ids=item_ids, include=[])['ids']

    def get_item_document(self, item_id):
        for id, document in self.iterate_item_documents(item_ids=[item_id]):
            return document
        return None

    def iterate_item_documents(self, item_ids=None):
        assert item_ids, 'Chroma does not support iterating over all item documents'
        results = self._collection.get(ids=item_ids, include=["documents"])
        yield from zip(results["ids"], results["documents"])

    def iterate_item_ids(self, offset=0, limit=1000):
        while True:
            results = self._collection.get(offset=offset, limit=limit, include=[])
            ids = results.get('ids', [])
            for id in ids:
                yield id
            offset += len(ids)
            if len(ids) == 0:
                break

    def iterate_query_items(self, embeddings, num_results=5, where=None):
        if where:
            print("WARNING! Chroma does not support where clause")  # where causes a crash in Chroma sometimes
        results = self._collection.query(
            query_embeddings=embeddings,
            n_results=num_results,
            include=["metadatas", "documents"],
        )
        for id, document, metadata in zip(results['ids'][0], results['documents'][0], results['metadatas'][0]):
            yield ChromaItem(id, document=document, metadata=metadata)


class ChromaVectorDB(BaseVectorDB):
    Item = ChromaItem

    def __init__(self):
        self._client = self._get_client()

    @staticmethod
    def get_default_collection_name():
        return config.CHROMADB_DATASETS_COLLECTION_NAME

    @staticmethod
    def get_vector_db_provider_name():
        return "chroma"

    @staticmethod
    def _get_client():
        common_settings_kwargs = {
            "anonymized_telemetry": False,
        }
        if config.USE_CLICKHOUSE:
            assert not config.USE_CHROMA_SERVER, "Cannot use both clickhouse and chroma server"
            return chromadb.Client(chromadb.config.Settings(
                chroma_db_impl="clickhouse",
                persist_directory=config.CHROMADB_DIR,
                clickhouse_host="localhost",
                clickhouse_port=8123,
                **common_settings_kwargs
            ))
        elif config.USE_CHROMA_SERVER:
            assert config.CHROMA_SERVER_URL, "CHROMA_SERVER_URL is not set"
            telemetry_client = chromadb.telemetry.posthog.Posthog(chromadb.config.Settings(**common_settings_kwargs))
            return _FastAPI(telemetry_client)
        else:
            return chromadb.Client(chromadb.config.Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=config.CHROMADB_DIR,
                **common_settings_kwargs
            ))

    @staticmethod
    def _get_collection_kwargs(override_collection_name, with_metadata=True):
        import openai  # we need to import openai here because it needs to initizlie the api key after we load dotenv
        kwargs = {
            "name": override_collection_name or config.CHROMADB_DATASETS_COLLECTION_NAME,
            "embedding_function": chromadb.utils.embedding_functions.OpenAIEmbeddingFunction(api_key=openai.api_key),
        }
        if with_metadata:
            kwargs['metadata'] = {
                "hnsw:space": HNSW_SPACE,
                "hnsw:construction_ef": HNSW_CONSTRUCTION_EF,
                "hnsw:search_ef": HNSW_SEARCH_EF,
                "hnsw:M": HNSW_M,
                "hnsw:num_threads": HNSW_NUM_THREADS,
                "hnsw:resize_factor": HNSW_RESIZE_FACTOR,
            }
        return kwargs

    def persist(self):
        if not config.USE_CLICKHOUSE and not config.USE_CHROMA_SERVER:
            self._client.persist()

    def get_datasets_collection(self, override_collection_name=None):
        return ChromaCollection(self._client.get_collection(**self._get_collection_kwargs(override_collection_name, with_metadata=False)))

    def get_or_create_datasets_collection(self, override_collection_name=None):
        return ChromaCollection(self._client.get_or_create_collection(**self._get_collection_kwargs(override_collection_name)))

    def create_datasets_collection(self, override_collection_name=None):
        return ChromaCollection(self._client.create_collection(**self._get_collection_kwargs(override_collection_name)))

    def list_collections(self):
        for collection in self._client.list_collections():
            yield ChromaCollection(collection)

    def delete_collection(self, name):
        self._client.delete_collection(name)
