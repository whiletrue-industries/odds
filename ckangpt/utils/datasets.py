from ckangpt import vectordb


def list_datasets(*, client=None):
    vdb = vectordb.get_vector_db_instance()
    collection = vdb.get_or_create_datasets_collection()
    yield from collection.iterate_item_ids()


def get_dataset(dataset_id, *, client=None):
    vdb = vectordb.get_vector_db_instance()
    collection = vdb.get_or_create_datasets_collection()
    print('getting', dataset_id)
    return collection.get_item_document(dataset_id)
