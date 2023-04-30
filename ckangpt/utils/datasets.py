from ckangpt import chroma

def list_datasets(*, client=None):
    _, collection = chroma.get_or_create_datasets_collection(client=client)
    offset = 0
    while True:
        results = collection.get(offset=offset, limit=1000, include=[])
        ids = results.get('ids', [])
        for id in ids:
            yield id
        offset += len(ids)
        if len(ids) == 0:
            break


def get_dataset(dataset_id, *, client=None):
    _, collection = chroma.get_or_create_datasets_collection(client=client)
    print('getting', dataset_id)
    return collection.get([dataset_id]).get('documents', [{}])[0]
