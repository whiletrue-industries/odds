import os


def get_bool_env(name, default):
    return {"1": True, "0": False}.get(os.environ.get(name), default)


ROOT_DIR = os.environ.get('ROOT_DIR') or os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(ROOT_DIR, ".data")
CHROMADB_DIR = os.environ.get("CHROMADB_DIR") or os.path.join(DATA_DIR, "chromadb")
CHROMADB_COMPRESSED_FILE = os.environ.get("CHROMADB_COMPRESSED_FILE") or os.path.join(DATA_DIR, "chromadb.tar.gz")
CHROMADB_DATASETS_COLLECTION_NAME = os.environ.get("CHROMADB_DATASETS_COLLECTION_NAME") or "datasets3"
CHROMADB_COMPRESSED_FILE_URL = os.environ.get("CHROMADB_COMPRESSED_FILE_URL") or "https://storage.googleapis.com/ckangpt.whiletrue.industries/dumps/chromadb.tar.gz"
USE_CLICKHOUSE = get_bool_env('USE_CLICKHOUSE', False)
USE_CHROMA_SERVER = get_bool_env('USE_CHROMA_SERVER', True)
CHROMA_SERVER_URL = os.environ.get('CHROMA_SERVER_URL') or "https://ckangpt:pvzm1Z2pbQHQVDSz8C@ckangpt-chroma.uumpa.xyz/api/v1"
DEFAULT_NUM_RESULTS = int(os.environ.get('DEFAULT_NUM_RESULTS') or '5')

USE_PINECONE = get_bool_env('USE_PINECONE', False)
PINECONE_DATASETS_COLLECTION_NAME = os.environ.get('PINECONE_DATASETS_COLLECTION_NAME') or "ckangpt"
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.environ.get('PINECONE_ENVIRONMENT') or "us-west1-gcp"
