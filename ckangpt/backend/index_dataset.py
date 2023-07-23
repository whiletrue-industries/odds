import time
import fnmatch

import openai

from ckangpt import config, storage, vectordb
from ckangpt.vectordb.base import BaseItem


def main_glob(dataset_domain, dataset_name,
              load_from_disk=False, save_to_disk=False, save_to_storage=False,
              force_update=False, limit=None, collection_name=None):
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
        existing = set(storage.list_(prefix=f'dataset_embeddings/{domain}/'))
        print(f'Found {len(existing)} existing embeddings for {domain}')
        for idx, item in enumerate(storage.list_(prefix=f'dataset_descriptions/{domain}/')):
            name = item.split('/')[2]
            if fnmatch.fnmatchcase(name.lower(), dataset_name.lower()):
                ret = None
                if f'dataset_embeddings/{domain}/{name}' not in existing or force_update:
                    for retry in range(3):
                        try:
                            ret = main(domain, name, 
                                       load_from_disk=load_from_disk, save_to_disk=save_to_disk, save_to_storage=save_to_storage,
                                       force_update=force_update, collection=collection)
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
         load_from_disk=False, save_to_disk=False, save_to_storage=False,
         force_update=False, limit=None, collection_name=None, collection=None):
    assert not limit
    itempathparts = 'dataset_embeddings', dataset_domain, dataset_name
    item = None
    if not force_update:
        item, metadata = storage.load(*itempathparts, with_metadata=True, load_from_disk=load_from_disk)
        if item and not storage.is_updated_item_meteadata(metadata):
            if config.ENABLE_DEBUG:
                print("dataset embedding already exists in storage and does not require update")
            return None
    if not item:
        dataset_description = storage.load('dataset_descriptions', dataset_domain, dataset_name, load_from_disk=load_from_disk)
        if not dataset_description:
            if config.ENABLE_DEBUG:
                print("dataset description not found in storage, skipping")
                return
        summary = dataset_description.get('summary')
        if not summary:
            if config.ENABLE_DEBUG:
                print("dataset summary not found in description, skipping")
                return
        embedding = openai.Embedding.create(input=summary, model='text-embedding-ada-002')
        if not embedding and config.ENABLE_DEBUG:
            print("failed to generate embedding, skipping")
            return
        embedding = embedding['data'][0]['embedding']
    else:
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

    item = dict(
        embedding=embedding
    )
    if save_to_disk:
        storage.save_to_disk(item, *itempathparts)
    if save_to_storage:
        storage.save(item, *itempathparts)
    return '/'.join(itempathparts)
