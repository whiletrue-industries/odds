import json

import requests

from .config import CKAN_INSTANCES, KEEP_FIELDS


def get_instance_datasets(ckan_instance):
    page = 1
    while True:
        print(f"Getting page {page} of datasets from {ckan_instance}")
        r = requests.get(f"{ckan_instance}/api/3/action/package_search", params={"rows": 1000, "start": (page - 1) * 1000})
        if r.status_code != 200:
            print(f"Error getting page {page} of datasets from {ckan_instance}: {r.status_code}")
            break
        rows = r.json()['result']['results']
        yield from rows
        if len(rows) < 1000:
            break
        page += 1

def get_nested_field(dataset, field, prefix=''):
    if '.' not in field:
        yield f'{prefix}.{field}', dataset.get(field)
    else:
        first, rest = field.split('.', 1)
        if first in dataset:
            v = dataset[first]
            if isinstance(v, dict):
                yield from get_nested_field(v, rest, f'{prefix}.{first}')                    
            elif isinstance(v, list):
                for i, vv in enumerate(v):
                    yield from get_nested_field(vv, rest, f'{prefix}.{first}.{i}')
            else:
                print('Unexpected value', v, type(v), field, prefix)

def set_nested_field(rec, field, value):
    if '.' not in field:
        rec[field] = value
    else:
        first, rest = field.split('.', 1)        
        set_nested_field(rec.setdefault(first, dict()), rest, value)

def process_dataset(dataset):
    recs = [(k[1:], v) for field in KEEP_FIELDS for (k, v) in get_nested_field(dataset, field) if v is not None]
    ret = dict()
    for k, v in recs:
        set_nested_field(ret, k, v)
    return ret

def get_processed_datasets(ckan_instance):
    for dataset in get_instance_datasets(ckan_instance):
        yield process_dataset(dataset)

def get_all_datasets():
    for ckan_instance in CKAN_INSTANCES:
        for dataset in get_processed_datasets(ckan_instance):
            yield dict(**dataset, ckan_instance=ckan_instance)

if __name__ == "__main__":
    datasets = list(get_all_datasets())
    with open('datasets.json', 'w') as f:
        json.dump(datasets, f, ensure_ascii=False, indent=4)


