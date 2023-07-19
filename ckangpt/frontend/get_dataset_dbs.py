import os
import shutil
import base64
import tempfile
import traceback
from collections import defaultdict

import dataflows as DF
import sqlite3

from ckangpt import storage, config


TABULAR_RESOURCE_FORMATS = ['csv']


def process(db_file_path, url, **load_kwargs):
    stats = defaultdict(int)

    def update_stats(row):
        stats['rows'] += 1

    DF.Flow(
        DF.load(url, name='data', **load_kwargs,
                on_error=DF.load.ERRORS_IGNORE),
        # DF.printer(),
        update_stats,
        DF.dump_to_sql(
            {'data': {'resource-name': 'data'}},
            f'sqlite:///{db_file_path}',
        )
    ).process()
    return stats


def get_url_path_parts(url):
    url_path = base64.b64encode(url.encode('utf8')).decode('utf8').replace('/', '_')
    url_path_parts = [url_path[6:9], url_path[9:12], url_path]
    return ['data_sqlite_dbs', *url_path_parts]


def populate_data_db(url, extra_metadata, target_db_file_path=None):
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file_path = os.path.join(tmpdir, '1.db')
        try:
            stats = process(db_file_path, url)
        except:
            traceback.print_exc()
            print("Failed to load data with schema, falling back to infer and cast to strings")
            db_file_path = os.path.join(tmpdir, '2.db')
            stats = process(db_file_path, url, infer_strategy=DF.load.INFER_STRINGS, cast_strategy=DF.load.CAST_TO_STRINGS)
        conn = sqlite3.connect(db_file_path)
        c = conn.cursor()
        c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='data'")
        ddl_sql = c.fetchone()[0]
        url_path_parts = get_url_path_parts(url)
        storage.save_file(db_file_path, *url_path_parts, 'data.sqlite3')
        metadata = {'url': url, 'stats': dict(stats), 'ddl_sql': ddl_sql, **extra_metadata}
        storage.save(metadata, *url_path_parts, 'metadata.json')
        if target_db_file_path:
            shutil.copyfile(db_file_path, target_db_file_path)
    return metadata


def get_data_db(url, extra_metadata, target_db_file_path):
    url_path_parts = get_url_path_parts(url)
    metadata = storage.load(*url_path_parts, 'metadata.json')
    if metadata:
        storage.load_file(target_db_file_path, *url_path_parts, 'data.sqlite3')
        return metadata
    else:
        print("data db not in storage, populating")
        return populate_data_db(url, extra_metadata, target_db_file_path)


def main(dataset_domain, dataset_id, target_path=None):
    if not target_path:
        target_path = os.path.join(config.DATA_DIR, 'data_sqlite_dbs', dataset_domain, dataset_id)
        print(f'Saving dataset dbs to {target_path}')
    os.makedirs(target_path, exist_ok=True)
    dataset = storage.load('datasets', dataset_domain, dataset_id)
    for i, resource in enumerate(dataset.get('resources', [])):
        if (resource.get('format') or '').lower() in map(str.lower, TABULAR_RESOURCE_FORMATS):
            assert resource.get('url')
            resource['__db_metadata'] = get_data_db(resource['url'], {
                'dataset_domain': dataset_domain,
                'dataset_id': dataset_id,
                'resource_name': resource.get('name'),
                'resource_id': resource.get('id'),
            }, os.path.join(target_path, f'resource_{i}.sqlite3'))
    return dataset
