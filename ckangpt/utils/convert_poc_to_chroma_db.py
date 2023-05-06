import os
import gzip
import json
import pickle
from pprint import pprint
from collections import defaultdict

from tqdm import tqdm

from ckangpt import chroma, config


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


def iterate_collection_items(limit=None):
    all_datasets = load_datasets()
    for i, url, embeddings in iterate_embeddings(limit=limit):
        if url in all_datasets:
            dataset = all_datasets[url]
            yield True, {
                'embeddings': list(embeddings),
                'document': json.dumps(dataset),
                'metadata': {
                    'name': dataset['name'],
                    'ckan_instance': dataset['ckan_instance'],
                },
                'id': url
            }
        else:
            yield False, {
                'error': f'No dataset for {url}'
            }


def iterate_collection_item_batches(batch_size=1000, limit=None):
    batch = []
    for is_valid, item in iterate_collection_items(limit=limit):
        if is_valid:
            batch.append(item)
        else:
            yield False, item
        if len(batch) >= batch_size:
            yield True, batch
            batch = []
    if len(batch) > 0:
        yield True, batch


def add_batch_to_collection(client, collection, batch, continue_from_last=False):
    all_item_ids = [item['id'] for item in batch]
    if continue_from_last:
        existing_item_ids = collection.get(ids=[item['id'] for item in batch], include=[])['ids']
    else:
        existing_item_ids = []
    new_item_ids = [item_id for item_id in all_item_ids if item_id not in existing_item_ids]
    if len(new_item_ids) > 0:
        collection.add(
            ids=[item['id'] for item in batch if item['id'] in new_item_ids],
            embeddings=[item['embeddings'] for item in batch if item['id'] in new_item_ids],
            metadatas=[item['metadata'] for item in batch if item['id'] in new_item_ids],
            documents=[item['document'] for item in batch if item['id'] in new_item_ids],
        )
        if not config.USE_CLICKHOUSE and not config.USE_CHROMA_SERVER:
            client.persist()


def main(collection_name, limit=None, force=False, continue_from_last=False, debug=False):
    if collection_name == config.CHROMADB_DATASETS_COLLECTION_NAME:
        if force:
            print("WARNING! Recreating the default collection. This will cause downtime for anyone currently using the app.")
        else:
            raise Exception('Cannot overwrite the default collection. Please create a new collection and when done change the configured collection name.')
    print(f'Populating collection name: `{collection_name}`...')
    print(f'Limit: {limit}')
    print(f'Force: {force}')
    print(f'Continue from last: {continue_from_last}')
    stats = defaultdict(int)
    client, collection = chroma.get_or_create_datasets_collection(override_collection_name=collection_name)
    if not continue_from_last:
        print('Deleting existing collection...')
        collection.delete()
    for is_valid, batch in iterate_collection_item_batches(limit=limit):
        if is_valid:
            stats['valid'] += len(batch)
            add_batch_to_collection(client, collection, batch, continue_from_last=continue_from_last)
        else:
            stats['error'] += 1
            if debug:
                print(batch['error'])
    pprint(dict(stats))
    print('OK')
