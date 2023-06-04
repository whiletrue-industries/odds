import os
import json
import datetime
import platform
import subprocess

import boto3

from . import config


def validate_itempathparts(itempathparts):
    for part in itempathparts:
        assert '/' not in part and '\\' not in part, f"item path parts cannot contain directory separators"


def get_ckangpt_metadata():
    try:
        git_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
    except:
        git_commit = 'unknown'
    try:
        git_status = len(subprocess.check_output(['git', 'status', '-s']).decode().strip().splitlines())
    except:
        git_status = 'unknown'
    return {
        'g4': config.USE_GPT4,
        'dt': datetime.datetime.utcnow().isoformat(),
        'p': platform.platform(),
        'n': platform.node(),
        'v': platform.python_version(),
        'g': f'{git_commit} {git_status}',
        **({'ci': True} if config.CI else {})
    }


def is_updated_item_meteadata(old_metadata):
    new_metadata = get_ckangpt_metadata()
    for k, v in old_metadata.items():
        if k not in ['dt', 'p', 'n', 'v'] and new_metadata[k] != v:
            return True
    return False


def get_item_for_save(item):
    assert 'ckgptm' not in item, 'Item already has ckgptm key'
    return {
        'ckgptm': get_ckangpt_metadata(),
        'd': item
    }


def save_to_disk(item, *itempathparts):
    if config.ENABLE_DEBUG:
        print(f'Saving item to disk: {itempathparts}')
    validate_itempathparts(itempathparts)
    file_path = os.path.join(config.STORAGE_DIR, *itempathparts)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(get_item_for_save(item), f, indent=2, ensure_ascii=False)


def get_boto_s3_client():
    return boto3.client(
        's3',
        endpoint_url=config.STORAGE_WASABI_ENDPOINT,
        aws_access_key_id=config.STORAGE_WASABI_ACCESS_KEY,
        aws_secret_access_key=config.STORAGE_WASABI_SECRET_KEY,
    )


def save(item, *itempathparts):
    if config.ENABLE_DEBUG:
        print(f'Saving item to S3: {itempathparts}')
    validate_itempathparts(itempathparts)
    s3 = get_boto_s3_client()
    s3.put_object(Bucket=config.STORAGE_WASABI_BUCKET, Key='/'.join(itempathparts), Body=json.dumps(get_item_for_save(item), indent=2, ensure_ascii=False))


def get_item_from_load(item, with_metadata=False):
    metadata = {}
    if 'ckgptm' in item:
        metadata = item['ckgptm']
        item = item['d']
    if with_metadata:
        return item, metadata
    else:
        return item


def load(*itempathparts, load_from_disk=False, with_metadata=False):
    if config.ENABLE_DEBUG:
        print(f'Loading item from {"disk" if load_from_disk else "Wasabi"}: {itempathparts}')
    validate_itempathparts(itempathparts)
    if load_from_disk:
        file_path = os.path.join(config.STORAGE_DIR, *itempathparts)
        with open(file_path, 'r') as f:
            return get_item_from_load(json.load(f), with_metadata=with_metadata)
    else:
        s3 = get_boto_s3_client()
        try:
            response = s3.get_object(Bucket=config.STORAGE_WASABI_BUCKET, Key='/'.join(itempathparts))
        except s3.exceptions.NoSuchKey:
            return (None, None) if with_metadata else None
        return get_item_from_load(json.loads(response['Body'].read().decode('utf-8')), with_metadata=with_metadata)


def list_(prefix='', recursive=False):
    prefix = prefix or ''
    delimiter = '' if recursive else '/'
    s3 = get_boto_s3_client()
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=config.STORAGE_WASABI_BUCKET, Prefix=prefix, Delimiter=delimiter):
        for item in page.get('CommonPrefixes', []):
            yield item['Prefix']
        for item in page.get('Contents', []):
            yield item['Key']
