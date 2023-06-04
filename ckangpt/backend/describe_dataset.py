import json
import yaml
import fnmatch

from typing import Any, Dict

from textwrap import dedent

import guidance

from ckangpt import config, storage

import pandas as pd
import numpy as np


DESCRIBE_DATASET = '''{{#system~}}
You are an experienced data analyst.
{{~/system}}

{{#user~}}

Following are details on a dataset containing public data. Provide a summary of this dataset in JSON format, including a concise summary and a more detailed description.
The JSON should look like this:
{
    "summary": "<What does this dataset contain? A single term, concise and descriptive, using simple terms and avoiding jargon, answering this question.>",
    "description": "<Provide a good description of this dataset in a single paragraph, using simple terms and avoiding jargon.>"
}
Include in the description and summary information regarding relevant time periods, geographic regions, and other relevant details.
Return only the json object, without any additional explanation or context.
--------------
{{#each sections}}
{{this[0]}}{{this[1]}}
{{/each}}
{{~/user}}
{{#assistant~}}
{{gen 'response' temperature=0}}
{{~/assistant}}
'''

def dataset_params(dataset):
    dataset_resources = [
        {
            'name': resource.get('name', '').strip(),
            'fields': dict(
                (field['name'], field['field details']) for field in resource['fields']
                if 'field details' in field
            )
        }
        for resource in dataset.get('resources', [])
    ]
    dataset_resources = yaml.dump(dataset_resources, indent=4, sort_keys=False, Dumper=yaml.SafeDumper)

    title = dataset['title'].strip()
    notes = dataset['notes'].strip()[:200].replace('\n', '') if dataset.get('notes') else None
    if notes == title:
        notes = None
    org = dataset['organization']['title'].strip() if dataset.get('organization', {}).get('title') else None
    org_description = dataset['organization']['description'].strip()[:200].replace('\n', '') if dataset.get('organization', {}).get('description') else None
    ret = [
        ('Title: ', title),
        ('Notes: ', notes),
        ('Publisher: ', org),
        ('Publisher Description: ', org_description),
        ('Dataset files with field details:\n', dataset_resources),
    ]
    ret = list(filter(lambda x: x[1], ret))
    return ret


def fetch_dataset_data(dataset):
    resources = []
    for resource in dataset.get('resources', []):
        if 'format' not in resource:
            continue
        if resource['format'].lower() in ['csv', 'xls', 'xlsx']:
            if 'url' not in resource:
                continue
            url = resource['url']
            try:
                print('Loading', url)
                df = pd.read_csv(url)
                resource['fields'] = [
                    {'name': col, 'type': str(df[col].dtype)} for col in df.columns]

                # Convert data types of object columns to improve data descriptions
                for col in df.select_dtypes(include=['object']):
                    try:
                        df[col] = pd.to_datetime(df[col], errors='ignore', format='auto')
                    except ValueError:
                        df[col] = pd.to_numeric(df[col], errors='ignore')

                # Add field details, missing_values, and distribution for each column
                for field in resource['fields']:
                    col_name = field['name']
                    col_type = field['type']

                    if col_type in ['float64', 'int64']:
                        min_value = df[col_name].min()
                        max_value = df[col_name].max()
                        if not np.isnan(min_value):
                            mean_value = round(df[col_name].mean(), 3)
                            median_value = round(df[col_name].median(), 3)
                            field['field details'] = f"Range: {min_value} to {max_value}, Mean: {mean_value}, Median: {median_value}"

                    elif col_type == 'datetime64[ns]':
                        min_date = df[col_name].min()
                        max_date = df[col_name].max()
                        min_date_str = min_date.strftime(
                            '%Y-%m') if not pd.isnull(min_date) else 'N/A'
                        max_date_str = max_date.strftime(
                            '%Y-%m') if not pd.isnull(max_date) else 'N/A'
                        field['field details'] = f"Date range: {min_date_str} to {max_date_str}"
                    else:
                        top_values = ', '.join([str(x).strip() for x in df[col_name].value_counts()[:3].index])
                        field['field details'] = f"e.g. {top_values}"

                    # Add missing_values ratio
                    missing_values_count = df[col_name].isna().sum()
                    missing_values_ratio = round(
                        missing_values_count / len(df), 3)
                    field['missing_values_ratio'] = missing_values_ratio

                    # Add distribution count if possible
                    try:
                        distribution = df[col_name].value_counts().to_dict()
                        field['distribution'] = distribution
                    except:
                        field['distribution'] = None

                resource['sample'] = df.sample(
                    n=3, random_state=42).to_csv(index=False)
                resources.append(resource)
            except Exception as e:
                print('Failed to load', url, e)
                resource['sample'] = url
    dataset['resources'] = resources


def main_glob(dataset_domain, dataset_name, load_from_disk=False, save_to_disk=False, save_to_storage=False, force_update=False, limit=None):
    print(f'Describing datasets matching glob pattern {dataset_domain}/{dataset_name}')
    matching_domains = set()
    for item in storage.list_(prefix='datasets/'):
        domain = item.split('/')[1]
        if fnmatch.fnmatchcase(domain.lower(), dataset_domain.lower()):
            matching_domains.add(domain)
    i = 0
    for domain in matching_domains:
        for item in storage.list_(prefix=f'datasets/{domain}/'):
            name = item.split('/')[2]
            if fnmatch.fnmatchcase(name.lower(), dataset_name.lower()):
                yield main(domain, name, load_from_disk=load_from_disk, save_to_disk=save_to_disk, save_to_storage=save_to_storage, force_update=force_update)
                i += 1
                if limit and i >= limit:
                    return


def main(dataset_domain, dataset_name, load_from_disk=False, save_to_disk=False, save_to_storage=False, force_update=False, limit=None):
    assert not limit
    itempathparts = 'dataset_descriptions', dataset_domain, dataset_name
    if save_to_storage and not force_update:
        old_dataset_description, metadata = storage.load(*itempathparts, with_metadata=True)
        print(old_dataset_description, metadata)
        if old_dataset_description and not storage.is_updated_item_meteadata(metadata):
            if config.ENABLE_DEBUG:
                print("dataset description already exists in storage and does not require update, skipping")
            return old_dataset_description
    if config.USE_GPT4:
        print('WARNING! Using GPT-4 - this will be slow and expensive!')
    dataset = storage.load('datasets', dataset_domain, dataset_name, load_from_disk=load_from_disk)
    fetch_dataset_data(dataset)

    llm = guidance.llms.OpenAI(config.model_name(), chat_mode=True, caching=config.ENABLE_CACHE)
    res = guidance.Program(
        llm=llm,
        text=DESCRIBE_DATASET,
        silent=True
    )(sections=dataset_params(dataset))

    try:
        item = json.loads(res['response'])
    except Exception as e:
        raise Exception(f'Failed to parse response json: \n{res}') from e
    if save_to_disk:
        storage.save_to_disk(item, *itempathparts)
    if save_to_storage:
        storage.save(item, *itempathparts)
    return item
