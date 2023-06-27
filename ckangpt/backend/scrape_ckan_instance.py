import fnmatch

import requests

from ckangpt import storage, config


def get_ckan_instance_requests_kwargs(domain):
    if domain.lower() == 'data.gov.il':
        return {
            'headers': {
                'User-Agent': 'datagov-external-client'
            }
        }
    else:
        return {}


def get_instance_datasets(domain, limit=None):
    page = 1
    num_rows = 0
    while True:
        if config.ENABLE_DEBUG:
            print(f"Getting page {page} of datasets from {domain}")
        r = requests.get(
            f"https://{domain}/api/3/action/package_search", params={"rows": 1000, "start": (page - 1) * 1000},
            **get_ckan_instance_requests_kwargs(domain),
            timeout=240
        )
        assert r.status_code == 200, f"Error getting page {page} of datasets from {domain}: {r.status_code}"
        rows = r.json()['result']['results']
        for row in rows:
            yield row
            num_rows += 1
            if limit and num_rows >= limit:
                break
        if len(rows) < 1000 or (limit and num_rows >= limit):
            break
        page += 1


def main_glob(domains_glob, limit=None, save_to_disk=False, save_to_storage=False, force=False, dataset_glob=None):
    print(f'Scraping datasets from domains matching {domains_glob}')
    for domain in config.CKAN_INSTANCE_DOMAINS:
        if fnmatch.fnmatchcase(domain.lower(), domains_glob.lower()):
            main(domain, limit=limit, save_to_disk=save_to_disk, save_to_storage=save_to_storage, force=force, dataset_glob=dataset_glob)


def main(domain, limit=None, save_to_disk=False, save_to_storage=False, glob=False, force=False, dataset_glob=None):
    if glob:
        return main_glob(domain, limit=limit, save_to_disk=save_to_disk, save_to_storage=save_to_storage, force=force, dataset_glob=dataset_glob)
    else:
        print(f"Scraping {limit or 'all'} datasets from {domain}")
        if dataset_glob:
            print(f"Filtering datasets by {dataset_glob}")
        if save_to_disk:
            print("Saving to local disk")
        if save_to_storage:
            print("Saving to remote storage")
            assert force or config.CI, "Save to storage should only run from CI, use --force to override"
        assert save_to_disk or save_to_storage, "Must set either --save-to-disk to save to local disk for local developement or --save-to-storage to save to remote storage"
        i = 0
        for dataset in get_instance_datasets(domain, limit=limit):
            if dataset_glob and not fnmatch.fnmatchcase(dataset['name'], dataset_glob):
                continue
            print(f'Scraping dataset {dataset["name"]} from {domain}')
            storage_item_path_parts = 'datasets', domain, dataset['name']
            if save_to_disk:
                storage.save_to_disk(dataset, *storage_item_path_parts)
            if save_to_storage:
                storage.save(dataset, *storage_item_path_parts)
            i += 1
        print(f'Saved {i} datasets from {domain}')
