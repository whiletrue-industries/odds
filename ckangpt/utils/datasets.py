import fnmatch

from ckangpt import config, storage


def list_datasets(dataset_domain, dataset_name, load_from_disk=False, limit=None):
    print(f'Listing datasets matching glob pattern {dataset_domain}/{dataset_name}')
    matching_domains = set()
    for item in storage.list_(prefix='dataset_descriptions/'):
        domain = item.split('/')[1]
        if fnmatch.fnmatchcase(domain.lower(), dataset_domain.lower()):
            matching_domains.add(domain)
    i = 0
    for domain in matching_domains:
        for item in storage.list_(prefix=f'dataset_descriptions/{domain}/'):
            parts = item.split('/')
            name = parts[2]
            if fnmatch.fnmatchcase(name.lower(), dataset_name.lower()):
                yield domain, name, storage.load(*parts, load_from_disk=load_from_disk)
                i += 1
                if limit and i >= limit:
                    return


def get_dataset(dataset_id, *, client=None):
    vdb = vectordb.get_vector_db_instance()
    collection = vdb.get_datasets_collection()
    print('getting', dataset_id)
    return collection.get_item_document(dataset_id)
