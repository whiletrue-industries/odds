import pandas as pd
import json
import csv
from io import StringIO

from typing import Any, Dict

from textwrap import dedent

from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.callbacks import get_openai_callback

from ckangpt.utils.datasets import get_dataset

import dataflows as DF

import pandas


class DatasetPrompt(PromptTemplate):

    dataset: Dict[str, Any]
    """The dataset to describe"""

    def format(self, **kwargs):
        dataset = self.dataset
        resources = [
            {
                'name': resource.get('name', '').strip(),
                'sample': resource['sample'],
                'fields': [
                    {
                        'name': field['name'],
                        'details': field['field details'],
                        'missing_values_ratio': field['missing_values_ratio']
                    }
                    for field in resource['fields']
                ]
            }
            for resource in dataset.get('resources', [])
        ]

        res = filter(None, [
            f"Title: {dataset['title'].strip()}",
            f"Notes: {dataset['notes'].strip()[:200]}" if dataset.get(
                'notes') else None,
            f"Organization: {dataset['organization']['title'].strip()}" if dataset.get(
                'organization', {}).get('title') else None,
            f"Organization description: {dataset['organization']['description'].strip()}" if dataset.get(
                'organization', {}).get('description') else None,
            f"Dataset files and sample data in CSV format with field details, missing values ratio, and distribution:\n" +
            '\n\n'.join(f'{i+1}) {resource}' for i,
                        resource in enumerate(resources)) if resources else None,
        ])

        kwargs['text'] = '\n'.join(res)
        return super().format(**kwargs)


def fetch_dataset_data(dataset):
    resources = []
    for resource in dataset.get('resources').values():
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
                        df[col] = pd.to_datetime(
                            df[col], errors='ignore')
                    except ValueError:
                        df[col] = pd.to_numeric(df[col], errors='ignore')

                # Add field details, missing_values, and distribution for each column
                for field in resource['fields']:
                    col_name = field['name']
                    col_type = field['type']

                    if col_type in ['float64', 'int64']:
                        min_value = df[col_name].min()
                        max_value = df[col_name].max()
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
                        top_values = list(df[col_name].value_counts().nlargest(
                            10).to_dict().keys())
                        field['field details'] = f"Top values: {top_values}"

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


def main(dataset_id, gpt4=False):
    if gpt4:
        print('WARNING! Using GPT-4 - this will be slow and expensive!')
    dataset = json.loads(get_dataset(dataset_id))
    fetch_dataset_data(dataset)
    chain = LLMChain(
        llm=ChatOpenAI(
            model_name='gpt-4' if gpt4 else 'gpt-3.5-turbo', request_timeout=240),
        prompt=DatasetPrompt(input_variables=['text'], template_format='jinja2', template=dedent("""
            Act as an experienced researcher. Following are details on a dataset containing public data. Provide a summary of this dataset in JSON format, including a title, description, and keywords. The JSON should look like this:
            {
                "purpose": "<What is the purpose of this dataset? A single sentence, concise and descriptive, using simple terms and avoiding jargon.>",
                "description": "<A good description of this dataset in a single paragraph, using simple terms and avoiding jargon.>",
                "keywords": "<a semicolon-separated list of keywords that describe this dataset.>",
                "data general": "<What sort of data might we find in this dataset?>",
                "data fields": "<a list with statistics of each field or variable in the data set: type of variable, the range of data points values, the distribution of data points, a ratio of missing values.>"
                "example questions": "<a list of different example research questions this data set can answer>"
            }
            ----------------
            {{text}}
        """), dataset=dataset),
        verbose=True
    )
    with get_openai_callback() as cb:
        res = chain.run(dataset_id)
        print(cb)
    return (res)
