import time
import fnmatch

import openai

from ckangpt import config, storage, vectordb
from ckangpt.vectordb.base import BaseItem


def main_glob(dataset_domain, dataset_name,
              load_from_disk=False, limit=None, collection_name=None):
    print(f'Indexing datasets matching glob pattern {dataset_domain}/{dataset_name}')

    vdb = vectordb.get_vector_db_instance()
    collection_name = collection_name or vdb.get_default_collection_name()
    collection = vdb.get_datasets_collection(override_collection_name=collection_name)

    matching_domains = set()
    for item in storage.list_(prefix='dataset_descriptions/'):
        domain = item.split('/')[1]
        if fnmatch.fnmatchcase(domain.lower(), dataset_domain.lower()):
            matching_domains.add(domain)
    indexed = 0
    for domain in matching_domains:
        for idx, item in enumerate(storage.list_(prefix=f'dataset_embeddings/{domain}/')):
            name = item.split('/')[2]
            if fnmatch.fnmatchcase(name.lower(), dataset_name.lower()):
                ret = None
                for retry in range(3):
                    try:
                        ret = main(domain, name, 
                                    load_from_disk=load_from_disk, collection=collection)
                        break
                    except Exception as e:
                        print(f'Failed to index {domain}/{name}: {e}, waiting 1 minute and retrying {retry + 1}/3')
                        time.sleep(60)

                if ret:
                    indexed += 1
                    if limit and indexed >= limit:
                        return
                    yield ret
            if idx % 100 == 99:
                print(f'Indexed {indexed} datasets so far (out of {idx + 1} datasets considered so far)') 


def main(dataset_domain, dataset_name,
         load_from_disk=False, limit=None, collection_name=None, collection=None):
    assert not limit
    itempathparts = 'dataset_embeddings', dataset_domain, dataset_name
    item = storage.load(*itempathparts, load_from_disk=load_from_disk)
    if not item:
        print(f"dataset embedding for {itempathparts} doesn't exists in storage!")
        return None
    embedding = item['embedding']

    if not collection:
        vdb = vectordb.get_vector_db_instance()
        collection_name = collection_name or vdb.get_default_collection_name()
        collection = vdb.get_datasets_collection(override_collection_name=collection_name)
    path = '/'.join(itempathparts)
    indexed_item = BaseItem(
        id=path,
        embeddings=[embedding],
        metadata=dict(dataset_domain=dataset_domain, dataset_name=dataset_name),
        document=['dataset_descriptions', dataset_domain, dataset_name]
    )
    collection.add([indexed_item])

    return '/'.join(itempathparts)
