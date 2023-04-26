import os
import tarfile

import requests

from ckangpt import config


def main():
    url = config.CHROMADB_COMPRESSED_FILE_URL
    compressed_filename = config.CHROMADB_COMPRESSED_FILE
    target_dir = config.CHROMADB_DIR
    assert not os.path.exists(compressed_filename), \
        f"ChromaDB compressed file already exists at `{compressed_filename}`, delete it to continue"
    assert not os.path.exists(target_dir), \
        f"ChromaDB directory already exists at `{target_dir}`, delete it to continue"
    print(f"Downloading {url} to {compressed_filename}")
    os.makedirs(os.path.dirname(compressed_filename), exist_ok=True)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(compressed_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f'Extracting {compressed_filename} to {target_dir}')
    with tarfile.open(compressed_filename, "r:gz") as tar:
        tar.extractall(os.path.dirname(target_dir))
    print("OK")
