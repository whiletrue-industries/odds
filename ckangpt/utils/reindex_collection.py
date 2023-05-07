from ckangpt import config, vectordb


def main(collection_name, force):
    vdb = vectordb.get_vector_db_instance()
    if collection_name == vdb.get_default_collection_name():
        if force:
            print("WARNING! Reindexing the default collection. This will cause downtime for anyone currently using the app.")
        else:
            raise Exception('Cannot reindex the default collection. Please reindex a new collection and when done change the configured collection name.')
    print(f'Reindexing collection name: `{collection_name}`...')
    collection = vdb.get_or_create_datasets_collection(override_collection_name=collection_name)
    collection.reindex()
    print('OK')
