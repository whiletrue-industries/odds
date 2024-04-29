from typing import Any

from .frontend_query import FrontendQueryRunner, FrontendQuery

INSTRUCTION = '''
Generate a list of possible official dataset titles which would likely contain the following data point: "{datapoint}".
If no such data points can be found, return an empty list.
Return the list as an array of strings, in a validated json format.
'''


class GuessDatasetNames(FrontendQuery):

    def __init__(self, datapoint: str):
        super().__init__()
        self.datapoint = datapoint

    def prompt(self) -> list[tuple[str, str]]:
        return [
            ('system', 'You are an experienced data analyst and researcher.'),
            ('user', INSTRUCTION.format(datapoint=self.datapoint))
        ]

    def handle_result(self, result: list[str]) -> Any:
        return result


guess_dataset_names = FrontendQueryRunner(GuessDatasetNames)

