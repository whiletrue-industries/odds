import json
import numpy as np

from ...common.datatypes_socrata import SocrataResource

from ...common.datatypes import Dataset, Resource, Field


def dataset_factory(data: dict) -> Dataset:
    resources = data.pop('resources', [])
    for resource in resources:
        fields = []
        for f in resource['fields']:
            f.update(json.loads(f.pop('properties') or '{}'))
            fields.append(Field(**f))
        resource['fields'] = fields
    data['resources'] = [resource_factory(**r) for r in resources]
    embedding = None
    if 'embeddings' in data:
        embedding = data.pop('embeddings')
    dataset = Dataset(**data)
    dataset.status_embedding = bool(embedding)
    if embedding:
        dataset.embedding = np.array(embedding, dtype=np.float32)
    return dataset


def resource_factory(**data):
    if data.get('kind') == 'socrata':
        return SocrataResource(**data)
    return Resource(**data)