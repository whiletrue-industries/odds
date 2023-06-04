import os
import openai


openai.api_key = os.environ.get('OPENAI_API_KEY')


def get_bool_env(name, default):
    return {"1": True, "0": False}.get(os.environ.get(name), default)


ROOT_DIR = os.environ.get('ROOT_DIR') or os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(ROOT_DIR, ".data")
CHROMADB_DIR = os.environ.get("CHROMADB_DIR") or os.path.join(DATA_DIR, "chromadb")
CHROMADB_COMPRESSED_FILE = os.environ.get("CHROMADB_COMPRESSED_FILE") or os.path.join(DATA_DIR, "chromadb.tar.gz")
CHROMADB_DATASETS_COLLECTION_NAME = os.environ.get("CHROMADB_DATASETS_COLLECTION_NAME") or "datasets3"
CHROMADB_COMPRESSED_FILE_URL = os.environ.get("CHROMADB_COMPRESSED_FILE_URL") or "https://storage.googleapis.com/ckangpt.whiletrue.industries/dumps/chromadb.tar.gz"

USE_GPT4 = get_bool_env('USE_GPT4', False)
ENABLE_CACHE = get_bool_env('ENABLE_CACHE', True)
ENABLE_DEBUG = get_bool_env('ENABLE_DEBUG', False)
DEFAULT_NUM_RESULTS = int(os.environ.get('DEFAULT_NUM_RESULTS') or '5')

USE_CLICKHOUSE = get_bool_env('USE_CLICKHOUSE', False)
USE_CHROMA_SERVER = get_bool_env('USE_CHROMA_SERVER', True)
CHROMA_SERVER_URL = os.environ.get('CHROMA_SERVER_URL') or "https://ckangpt:pvzm1Z2pbQHQVDSz8C@ckangpt-chroma.uumpa.xyz/api/v1"

USE_PINECONE = get_bool_env('USE_PINECONE', False)
PINECONE_DATASETS_COLLECTION_NAME = os.environ.get('PINECONE_DATASETS_COLLECTION_NAME') or "ckangpt"
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.environ.get('PINECONE_ENVIRONMENT') or "us-west1-gcp"

CI = os.environ.get('CI') == 'true'
STORAGE_DIR = os.environ.get("STORAGE_DIR") or os.path.join(DATA_DIR, "storage")
STORAGE_WASABI_BUCKET = os.environ.get('STORAGE_S3_BUCKET') or "ckangpt"
STORAGE_WASABI_ACCESS_KEY = os.environ.get('STORAGE_WASABI_ACCESS_KEY') or 'QWWBR9L8IWN62PJIKHOW'
STORAGE_WASABI_SECRET_KEY = os.environ.get('STORAGE_WASABI_SECRET_KEY') or 'GWXMI8SiCbNzhUIItBPqe86002pKBOPRud0zQelG'
STORAGE_WASABI_ENDPOINT = os.environ.get('STORAGE_WASABI_ENDPOINT') or 'https://s3.eu-west-2.wasabisys.com'

CKAN_INSTANCE_DOMAINS = [
    'data.gov.uk',
    'data.gov.il'
]


def model_name():
    if USE_GPT4:
        return 'gpt-4'
    else:
        return 'gpt-3.5-turbo'


def common():
    # model_name, cache, debug = config.common()
    return model_name(), ENABLE_CACHE, ENABLE_DEBUG
