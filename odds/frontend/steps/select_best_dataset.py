from typing import Any

from ...common.datatypes import DataCatalog, Dataset
from ...common.store import store

from .frontend_query import FrontendQueryRunner, FrontendQuery

INSTRUCTION = '''
Please rate the following datasets based on the likelihood that they contain this information: "{datapoint}".
Rate each dataset on a scale of 1 to 10, where 10 means the dataset is very likely to contain the information *in full*. Make sure you consider the requested time period, geographic area, and other relevant factors.
For each dataset, provide its id verbatim, a brief reason explaining why its relevant and covers the scope of the requested datapoint and its relevance score.
It is important that irrelevant or partial datasets are not included in the response.
Return the most relevant datasets only. If no dataset is relevant, return an empty list.
Response should be an array of objects, in a validated json format.

Example response:
[
    {{
        "id": "dataset id",
        "reason": "why this dataset is relevant",
        "score": <relevance score, 1-10>
    }},
    ...
]


Datasets:
{datasets}
''' 


class SelectBestDataset(FrontendQuery):

    def __init__(self, datapoint: str, datasets: list[Dataset], catalogs: list[DataCatalog]):
        super().__init__()
        self.datapoint = datapoint
        self.datasets = datasets
        self.catalogs = catalogs

    def prompt(self) -> list[tuple[str, str]]:
        datasets = '\n---------\n'.join([
            f'{d.storeId()}:\n  {d.title}\n  {d.description.replace("\n", "\n  ")}\n  by {d.publisher})\n   in the catalog "{c.title}"'
            for d,c in zip(self.datasets, self.catalogs)
        ])
        return [
            ('system', 'You are a dataset retrieval system.'),
            ('user', INSTRUCTION.format(datapoint=self.datapoint, datasets=datasets))
        ]

    def handle_result(self, result: list[str]) -> Any:
        result = sorted(result, key=lambda x: int(x['score']), reverse=True)
        if result:
            dataset_id = result[0]['id']
            return dataset_id
        return None

select_best_dataset = FrontendQueryRunner(SelectBestDataset)

