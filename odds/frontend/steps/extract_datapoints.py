from typing import Any

from .frontend_query import FrontendQueryRunner, FrontendQuery

INSTRUCTION = '''
Generate a list of no more than 3 singular data points (i.e. which could be represented by a single number), which when provided will allow verifying or refuting the following claim: "{claim}".
Only consider data points that would normally be found in officially published datasets.
Good descriptions of data points start with "The number of...", "The amount of...", "The date of...", "The name of..." or similar.
If no such data points can be found, return an empty list.
Return the list as an array of strings, in a validated json format.
'''


class ExtractDatapoints(FrontendQuery):

    def __init__(self, claim: str):
        super().__init__()
        self.claim = claim

    def prompt(self) -> list[tuple[str, str]]:
        return [
            ('system', 'You are an experienced data analyst and researcher.'),
            ('user', INSTRUCTION.format(claim=self.claim))
        ]

    def handle_result(self, result: list[str]) -> Any:
        return result


extract_datapoints = FrontendQueryRunner(ExtractDatapoints)

