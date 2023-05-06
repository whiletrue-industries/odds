import chromadb
import chromadb.config
import chromadb.api.fastapi
import chromadb.telemetry.posthog
import chromadb.utils.embedding_functions

from . import config


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


def get_or_create_datasets_collection(*, client=None, override_collection_name=None):
    import openai  # we need to import openai here because it needs to initizlie the api key after we load dotenv
    client = client or get_client()
    return client, client.get_or_create_collection(
        override_collection_name or config.CHROMADB_DATASETS_COLLECTION_NAME,
        embedding_function=chromadb.utils.embedding_functions.OpenAIEmbeddingFunction(api_key=openai.api_key)
    )


def get_datasets_collection(*args, **kwargs):
    _, collection = get_or_create_datasets_collection(*args, **kwargs)
    return collection
