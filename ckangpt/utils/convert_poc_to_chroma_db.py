import os
import gzip
import json
import pickle

from ckangpt import chroma, config


def main(limit=None):
    all_datasets = {}
    with gzip.GzipFile(os.path.join(config.ROOT_DIR, 'poc', 'datasets.json.gz'), 'r') as zipped:
        for dataset in json.load(zipped):
            all_datasets[(dataset['ckan_instance'] + '/' + dataset['name'])] = dataset
    with open(os.path.join(config.ROOT_DIR, 'poc', 'embeddings.pickle'), 'rb') as f:
        all_embeddings = pickle.load(f)
    client, collection = chroma.get_or_create_datasets_collection()
    collection.delete()
    for i, (url, embeddings) in enumerate(all_embeddings):
        if limit and i > int(limit):
            break
        print(f'Adding {url}')
        dataset = all_datasets[url]
        collection.add(
            embeddings=list(embeddings),
            documents=json.dumps(dataset),
            metadatas={
                'name': dataset['name'],
                'ckan_instance': dataset['ckan_instance'],
            },
            ids=url,
        )
    client.persist()
    print('OK')
