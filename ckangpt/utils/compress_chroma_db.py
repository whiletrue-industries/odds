import os
import tarfile

from ckangpt import config


def main():
    print(f"Compressing {config.CHROMADB_DIR} to {config.CHROMADB_COMPRESSED_FILE}")
    with tarfile.open(config.CHROMADB_COMPRESSED_FILE, "w:gz") as tar:
        tar.add(config.CHROMADB_DIR, arcname=os.path.basename(config.CHROMADB_DIR))
    print("OK")
