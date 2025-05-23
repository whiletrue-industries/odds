import json
import numpy as np

from ...common.datatypes_socrata import SocrataResource
from ...common.datatypes_website import WebsiteResource

from ...common.datatypes import Dataset, Resource, Field


def dataset_factory(data: dict) -> Dataset:
    resources = data.pop('resources', [])
    for resource in resources:
        fields = []
        for f in resource['fields']:
            f.update(json.loads(f.pop('props', None) or '{}'))
            f = dict(
                (k, v) for k, v in f.items() if k in Field.__dataclass_fields__
            )
            fields.append(Field(**f))
        resource['fields'] = fields
    data['resources'] = [resource_factory(**r) for r in resources]
    embedding = None
    if 'embeddings' in data:
        embedding = data.pop('embeddings')
    id = data.pop('id')
    catalogId = data.pop('catalogId')
    title= data.pop('title')
    dataset = Dataset(catalogId, id, title, **data)
    dataset.status_embedding = bool(embedding)
    if embedding:
        dataset.embedding = np.array(embedding, dtype=np.float32)
    return dataset


def resource_factory(**data):
    if data.get('kind') == 'socrata':
        return SocrataResource(**data)
    elif data.get('kind') == 'website':
        return WebsiteResource(**data)
    return Resource(**data)