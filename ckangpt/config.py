import os


ROOT_DIR = os.environ.get('ROOT_DIR') or os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(ROOT_DIR, ".data")
CHROMADB_DIR = os.environ.get("CHROMADB_DIR") or os.path.join(DATA_DIR, "chromadb")
CHROMADB_COMPRESSED_FILE = os.environ.get("CHROMADB_COMPRESSED_FILE") or os.path.join(DATA_DIR, "chromadb.tar.gz")
CHROMADB_DATASETS_COLLECTION_NAME = os.environ.get("CHROMADB_DATASETS_COLLECTION_NAME") or "datasets"
CHROMADB_COMPRESSED_FILE_URL = os.environ.get("CHROMADB_COMPRESSED_FILE_URL") or "https://www.dropbox.com/s/71kvm7amgq8ufzb/chromadb.tar.gz?dl=1"
