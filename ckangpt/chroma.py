import os

import chromadb
import chromadb.config
import chromadb.utils.embedding_functions
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

from . import config


def get_client():
    if config.USE_CLICKHOUSE:
        return chromadb.Client(chromadb.config.Settings(
            chroma_db_impl="clickhouse",
            persist_directory=config.CHROMADB_DIR,
            clickhouse_host="localhost",
            clickhouse_port=8123,
            anonymized_telemetry=False,
        ))
    else:
        return chromadb.Client(chromadb.config.Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=config.CHROMADB_DIR,
            anonymized_telemetry=False,
        ))


def get_or_create_datasets_collection(*, client=None):
    client = client or get_client()
    return client, client.get_or_create_collection(
        config.CHROMADB_DATASETS_COLLECTION_NAME,
        # we don't rely on the embedding_function at the moment, we generate our own embeddings
        embedding_function=chromadb.utils.embedding_functions.EmbeddingFunction
    )


def get_langchain_datasets_db():
    assert os.path.exists(os.path.join(config.CHROMADB_DIR)), \
        "ChromaDB not found, please run `ckangpt utils download-chroma-db` to download it"
    embeddings = OpenAIEmbeddings()
    return Chroma(
        config.CHROMADB_DATASETS_COLLECTION_NAME,
        embedding_function=embeddings,
        client=get_client(),
    )
