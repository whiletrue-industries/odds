import os
import openai

import dotenv

dotenv.load_dotenv()

openai.api_key = os.environ.get('OPENAI_API_KEY')


def get_bool_env(name, default):
    return {"1": True, "0": False}.get(os.environ.get(name), default)


CI = os.environ.get('CI') == 'true'

ROOT_DIR = os.environ.get('ROOT_DIR') or os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(ROOT_DIR, ".data")
CHROMADB_DIR = os.environ.get("CHROMADB_DIR") or os.path.join(DATA_DIR, "chromadb")
CHROMADB_COMPRESSED_FILE = os.environ.get("CHROMADB_COMPRESSED_FILE") or os.path.join(DATA_DIR, "chromadb.tar.gz")
CHROMADB_DATASETS_COLLECTION_NAME = os.environ.get("CHROMADB_DATASETS_COLLECTION_NAME") or "datasets"
CHROMADB_COMPRESSED_FILE_URL = os.environ.get("CHROMADB_COMPRESSED_FILE_URL") or "https://storage.googleapis.com/ckangpt.whiletrue.industries/dumps/chromadb.tar.gz"

USE_GPT4 = get_bool_env('USE_GPT4', CI)  # for CI environments - always use GPT-4, otherwise default will be to not use it
ENABLE_CACHE = get_bool_env('ENABLE_CACHE', True)
ENABLE_DEBUG = get_bool_env('ENABLE_DEBUG', False)
DEFAULT_NUM_RESULTS = int(os.environ.get('DEFAULT_NUM_RESULTS') or '5')

USE_CLICKHOUSE = get_bool_env('USE_CLICKHOUSE', False)
USE_CHROMA_SERVER = get_bool_env('USE_CHROMA_SERVER', False)
CHROMA_SERVER_URL = os.environ.get('CHROMA_SERVER_URL')

USE_PINECONE = get_bool_env('USE_PINECONE', True)
# in pinecone terminology this is called an index name, pinecone collection is something else
# you need to create the index as named here ('ckangpt') in pinecone first with the following properties:
# - dimensions: 1536
# - metric: cosine
# - pod type: starter
PINECONE_DATASETS_COLLECTION_NAME = os.environ.get('PINECONE_DATASETS_COLLECTION_NAME') or "ckangpt"
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY') or "1a26625d-b388-4ebd-9fdc-0283ba594f96"
PINECONE_ENVIRONMENT = os.environ.get('PINECONE_ENVIRONMENT') or "asia-southeast1-gcp-free"

STORAGE_DIR = os.environ.get("STORAGE_DIR") or os.path.join(DATA_DIR, "storage")
STORAGE_PROVIDER = 'azure'  # 'wasabi'
STORAGE_WASABI_BUCKET = os.environ.get('STORAGE_S3_BUCKET')  # or "ckangpt"
STORAGE_WASABI_ACCESS_KEY = os.environ.get('STORAGE_WASABI_ACCESS_KEY')  # or 'QWWBR9L8IWN62PJIKHOW'
STORAGE_WASABI_SECRET_KEY = os.environ.get('STORAGE_WASABI_SECRET_KEY')  # or 'GWXMI8SiCbNzhUIItBPqe86002pKBOPRud0zQelG'
STORAGE_WASABI_ENDPOINT = os.environ.get('STORAGE_WASABI_ENDPOINT')  # or 'https://s3.eu-west-2.wasabisys.com'
STORAGE_AZURE_CONTAINER = os.environ.get('STORAGE_AZURE_CONTAINER') or 'ckangpt'
STORAGE_AZURE_BLOB_URL = os.environ.get('STORAGE_AZURE_BLOB_URL') or 'https://ckangpt.blob.core.windows.net'
STORAGE_AZURE_CONNECTION_STRING = os.environ.get('STORAGE_AZURE_CONNECTION_STRING') or 'DefaultEndpointsProtocol=https;AccountName=ckangpt;AccountKey=QgxBjRtojtdeq0CafSa+PoOSXeQJNX9yU8kayLGdyjfQI/jNjWeyooqQxGdRHi1ufmF2CVMHErl6+AStDRBk7Q==;EndpointSuffix=core.windows.net'

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
