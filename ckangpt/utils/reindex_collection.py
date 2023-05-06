from ckangpt import config, chroma


def main(collection_name, force):
    if collection_name == config.CHROMADB_DATASETS_COLLECTION_NAME:
        if force:
            print("WARNING! Reindexing the default collection. This will cause downtime for anyone currently using the app.")
        else:
            raise Exception('Cannot reindex the default collection. Please reindex a new collection and when done change the configured collection name.')
    print(f'Reindexing collection name: `{collection_name}`...')
    _, collection = chroma.get_or_create_datasets_collection(override_collection_name=collection_name)
    collection.create_index()
    print('OK')
