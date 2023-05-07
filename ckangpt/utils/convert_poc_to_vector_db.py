import os
import gzip
import json
import pickle
from pprint import pprint
from collections import defaultdict

from tqdm import tqdm

from ckangpt import config
from ckangpt.vectordb import get_vector_db_instance


def load_datasets():
    all_datasets = {}
    with gzip.GzipFile(os.path.join(config.ROOT_DIR, 'poc', 'datasets.json.gz'), 'r') as zipped:
        for dataset in json.load(zipped):
            all_datasets[(dataset['ckan_instance'] + '/' + dataset['name'])] = dataset
    return all_datasets


def iterate_embeddings(limit=None):
    with open(os.path.join(config.ROOT_DIR, 'poc', 'embeddings.pickle'), 'rb') as f:
        all_embeddings = pickle.load(f)
    for i, (url, embeddings) in enumerate(tqdm(all_embeddings)):
        yield i, url, embeddings
        if limit is not None and i > limit:
            print(f'WARNING! incomplete iteration, limit reached: {limit} items')
            break


def get_dataset_metadata(dataset):
    # metadata should include only a limited number of fields and values because it is indexed in Chroma
    ckan_instance = dataset.get('ckan_instance')
    return {
        'ckan_instance': ckan_instance if ckan_instance in ['https://data.gov.uk', 'https://data.gov.il'] else ''
    }


def iterate_collection_items(item_class, limit=None):
    all_datasets = load_datasets()
    for i, url, embeddings in iterate_embeddings(limit=limit):
        if url in all_datasets:
            dataset = all_datasets[url]
            yield True, item_class(
                embeddings=list(embeddings),
                document=json.dumps(dataset),
                metadata=get_dataset_metadata(dataset),
                id=url
            )
        else:
            yield False, f'No dataset for {url}'


def iterate_collection_item_batches(item_class, batch_size=1000, limit=None):
    batch = []
    for is_valid, item in iterate_collection_items(item_class, limit=limit):
        if is_valid:
            batch.append(item)
        else:
            yield False, item
        if len(batch) >= batch_size:
            yield True, batch
            batch = []
    if len(batch) > 0:
        yield True, batch


def add_batch_to_collection(vdb, collection, items, continue_from_last=False):
    all_item_ids = [item.id for item in items]
    if continue_from_last:
        existing_item_ids = collection.get_existing_item_ids(all_item_ids)
    else:
        existing_item_ids = []
    new_item_ids = [item_id for item_id in all_item_ids if item_id not in existing_item_ids]
    if len(new_item_ids) > 0:
        collection.add([item for item in items if item.id in new_item_ids])
        vdb.persist()


def main(collection_name, limit=None, force=False, continue_from_last=False, debug=False):
    vdb = get_vector_db_instance()
    if collection_name == vdb.get_default_collection_name():
        if force:
            print("WARNING! Recreating the default collection. This will cause downtime for anyone currently using the app.")
        else:
            raise Exception('Cannot overwrite the default collection. Please create a new collection and when done change the configured collection name.')
    print(f'Populating collection name: `{collection_name}` using vector db provider {vdb.get_vector_db_provider_name()}...')
    print(f'Limit: {limit}')
    print(f'Force: {force}')
    print(f'Continue from last: {continue_from_last}')
    stats = defaultdict(int)
    if continue_from_last:
        collection = vdb.get_datasets_collection(override_collection_name=collection_name)
    elif force:
        collection = vdb.get_or_create_datasets_collection(override_collection_name=collection_name)
        print('Deleting existing collection...')
        collection.delete()
    else:
        collection = vdb.create_datasets_collection(override_collection_name=collection_name)
    print('Adding items to collection...')
    for is_valid, items in iterate_collection_item_batches(vdb.Item, limit=limit):
        if is_valid:
            stats['valid'] += len(items)
            add_batch_to_collection(vdb, collection, items, continue_from_last=continue_from_last)
        else:
            error = items
            stats['error'] += 1
            if debug:
                print(error)
    pprint(dict(stats))
    print('OK')
