import chromadb
import chromadb.config
import chromadb.api.fastapi
import chromadb.telemetry.posthog
import chromadb.utils.embedding_functions

from . import config

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


def get_client():
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


def get_collection_kwargs(override_collection_name, with_metadata=True):
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


def create_datasets_collection(*, client=None, override_collection_name=None):
    client = client or get_client()
    return client, client.create_collection(**get_collection_kwargs(override_collection_name))


def get_or_create_datasets_collection(*, client=None, override_collection_name=None):
    client = client or get_client()
    return client, client.get_or_create_collection(**get_collection_kwargs(override_collection_name))


def get_datasets_collection(*, client=None, override_collection_name=None):
    client = client or get_client()
    return client, client.get_collection(**get_collection_kwargs(override_collection_name, with_metadata=False))


def list_collections():
    client = get_client()
    return client.list_collections()


def delete_collection(name):
    client = get_client()
    client.delete_collection(name)
