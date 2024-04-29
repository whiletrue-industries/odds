from typing import Any
import json
from dataclasses import asdict

from ...common.datatypes import Dataset
from ...common.store import store

from .frontend_query import FrontendQueryRunner, FrontendQuery

INSTRUCTION = '''
Please rate the following data files based on the likelihood that they contain this information: "{datapoint}".
Rate each data file on a scale of 1 to 10, where 10 means the dataset is very likely to contain the information.
For each data file, provide its id verbatim, a brief reason explaining why its relevant and its relevance score.
Return the most relevant data files only. Irrelevant data files should not be included in the response.
If no data file is relevant, return an empty list.
Response should be an array of objects, in a validated json format.

Example response:
[
    {{
        "id": "data file id",
        "reason": "why this data file is relevant",
        "score": <relevance score, 1-10>
    }},
    ...
]


Data files:
{resources}
''' 


class SelectBestResource(FrontendQuery):

    def __init__(self, datapoint: str, dataset: Dataset):
        super().__init__()
        self.datapoint = datapoint
        self.dataset = dataset
        self.resources = []
        for i, r in enumerate(self.dataset.resources):
            if not r.status_loaded:
                continue
            fields = [
                {k:v for k,v in asdict(f).items() if v is not None}
                for f in r.fields
            ]
            fields = [
                f'`{f.pop('name')}` ({f.pop('data_type')}): {json.dumps(f, ensure_ascii=False)}'
                for f in fields
            ]
            if len(fields) > 20:
                fields = fields[:15] + ['...'] + fields[-5:]
            id = f'file{i:02d}'
            rec = (
                id,
                r.title or 'Data',
                '\n'.join(f'    - {f}' for f in fields)
            )
            self.resources.append(rec)

    def prompt(self) -> list[tuple[str, str]]:
        resources = '\n\n'.join([
            f'{r[0]}:\n  Title: {r[1]}\n  Field Information:\n{r[2]}'
            for r in self.resources
        ])
        return [
            ('system', 'You are a data retrieval system.'),
            ('user', INSTRUCTION.format(datapoint=self.datapoint, resources=resources))
        ]

    def handle_result(self, result: list[str]) -> Any:
        result = sorted(result, key=lambda x: int(x['score']), reverse=True)
        if result:
            resource_id = result[0]['id']
            resource_title = [r[1] for r in self.resources if r[0] == resource_id]
            if len(resource_title) > 0:
                resource_title = resource_title[0]
                resource = [r for r in self.dataset.resources if r.title == resource_title]
                if len(resource) > 0:
                    return resource[0]
        return None

select_best_resource = FrontendQueryRunner(SelectBestResource)

