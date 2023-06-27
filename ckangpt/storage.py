import os
import json
import datetime
import platform
import subprocess

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


def get_boto_s3_client_wasabi():
    import boto3
    return boto3.client(
        's3',
        endpoint_url=config.STORAGE_WASABI_ENDPOINT,
        aws_access_key_id=config.STORAGE_WASABI_ACCESS_KEY,
        aws_secret_access_key=config.STORAGE_WASABI_SECRET_KEY,
    )


def save(item, *itempathparts):
    if config.ENABLE_DEBUG:
        print(f'Saving item to {config.STORAGE_PROVIDER}: {itempathparts}')
    validate_itempathparts(itempathparts)
    if config.STORAGE_PROVIDER == 'wasabi':
        s3 = get_boto_s3_client_wasabi()
        s3.put_object(Bucket=config.STORAGE_WASABI_BUCKET, Key='/'.join(itempathparts), Body=json.dumps(get_item_for_save(item), indent=2, ensure_ascii=False))
    elif config.STORAGE_PROVIDER == 'azure':
        import azure.storage.blob
        blob_service_client = azure.storage.blob.BlobServiceClient.from_connection_string(config.STORAGE_AZURE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(config.STORAGE_AZURE_CONTAINER)
        container_client.upload_blob('/'.join(itempathparts), json.dumps(get_item_for_save(item), indent=2, ensure_ascii=False), overwrite=True)
    else:
        raise NotImplementedError(f'Unknown storage provider: {config.STORAGE_PROVIDER}')


def save_file(file_path, *itempathparts):
    if config.ENABLE_DEBUG:
        print(f'Saving file to {config.STORAGE_PROVIDER}: {itempathparts}')
    validate_itempathparts(itempathparts)
    if config.STORAGE_PROVIDER == 'wasabi':
        s3 = get_boto_s3_client_wasabi()
        s3.upload_file(file_path, config.STORAGE_WASABI_BUCKET, '/'.join(itempathparts))
    elif config.STORAGE_PROVIDER == 'azure':
        import azure.storage.blob
        blob_service_client = azure.storage.blob.BlobServiceClient.from_connection_string(config.STORAGE_AZURE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(config.STORAGE_AZURE_CONTAINER)
        with open(file_path, 'rb') as f:
            container_client.upload_blob('/'.join(itempathparts), f)
    else:
        raise NotImplementedError(f'Unknown storage provider: {config.STORAGE_PROVIDER}')


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
        print(f'Loading item from {"disk" if load_from_disk else config.STORAGE_PROVIDER}: {itempathparts}')
    validate_itempathparts(itempathparts)
    if load_from_disk:
        file_path = os.path.join(config.STORAGE_DIR, *itempathparts)
        with open(file_path, 'r') as f:
            return get_item_from_load(json.load(f), with_metadata=with_metadata)
    elif config.STORAGE_PROVIDER == 'wasabi':
        s3 = get_boto_s3_client_wasabi()
        try:
            response = s3.get_object(Bucket=config.STORAGE_WASABI_BUCKET, Key='/'.join(itempathparts))
        except s3.exceptions.NoSuchKey:
            return (None, None) if with_metadata else None
        return get_item_from_load(json.loads(response['Body'].read().decode('utf-8')), with_metadata=with_metadata)
    elif config.STORAGE_PROVIDER == 'azure':
        import azure.storage.blob
        blob_service_client = azure.storage.blob.BlobServiceClient.from_connection_string(config.STORAGE_AZURE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(config.STORAGE_AZURE_CONTAINER)
        try:
            blob_client = container_client.get_blob_client('/'.join(itempathparts))
            response = blob_client.download_blob()
        except azure.core.exceptions.ResourceNotFoundError:
            return (None, None) if with_metadata else None
        return get_item_from_load(json.loads(response.readall().decode('utf-8')), with_metadata=with_metadata)
    else:
        raise NotImplementedError(f'Unknown storage provider: {config.STORAGE_PROVIDER}')


def load_file(file_path, *itempathparts):
    if config.ENABLE_DEBUG:
        print(f'Loading file from {config.STORAGE_PROVIDER}: {itempathparts}')
    validate_itempathparts(itempathparts)
    if config.STORAGE_PROVIDER == 'wasabi':
        s3 = get_boto_s3_client_wasabi()
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        s3.download_file(config.STORAGE_WASABI_BUCKET, '/'.join(itempathparts), file_path)
    elif config.STORAGE_PROVIDER == 'azure':
        import azure.storage.blob
        blob_service_client = azure.storage.blob.BlobServiceClient.from_connection_string(config.STORAGE_AZURE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(config.STORAGE_AZURE_CONTAINER)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            blob_client = container_client.get_blob_client('/'.join(itempathparts))
            data = blob_client.download_blob()
            data.readinto(f)
    else:
        raise NotImplementedError(f'Unknown storage provider: {config.STORAGE_PROVIDER}')


def list_(prefix='', recursive=False):
    prefix = prefix or ''
    delimiter = '' if recursive else '/'
    if config.STORAGE_PROVIDER == 'wasabi':
        s3 = get_boto_s3_client_wasabi()
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=config.STORAGE_WASABI_BUCKET, Prefix=prefix, Delimiter=delimiter):
            for item in page.get('CommonPrefixes', []):
                yield item['Prefix']
            for item in page.get('Contents', []):
                yield item['Key']
    elif config.STORAGE_PROVIDER == 'azure':
        import azure.storage.blob
        blob_service_client = azure.storage.blob.BlobServiceClient.from_connection_string(config.STORAGE_AZURE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(config.STORAGE_AZURE_CONTAINER)
        for item in container_client.walk_blobs(name_starts_with=prefix):
            yield item.name
    else:
        raise NotImplementedError(f'Unknown storage provider: {config.STORAGE_PROVIDER}')
