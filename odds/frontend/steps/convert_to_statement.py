import json
from typing import Any

from .frontend_query import FrontendQueryRunner, FrontendQuery

INSTRUCTION = '''
Generate a statement based on the provided data, which would help determine the following data point: "{datapoint}".
Your response should be a single self-contained complete statement referencing the data point above, and the data provided below.
If no statement can be created, return a statement which says that the datapoint cannot be determined from the data provided.

Example 1:
   datapoint: "The number of people living in LA"
   data: {{"Population": 1000000}}
   statement: "The number of people living in LA is 1,000,000."

Example 2:
   datapoint: "The number of people living in LA"
   data: {{"Duration": 1000000}}
   statement: "The number of people living in LA could not be determined from the data provided."

Data:
{data}

Relevant context regarding the data: {explanation}
'''


class ConvertToStatement(FrontendQuery):

    def __init__(self, datapoint: str, data: list[dict], data_explanation: str = None):
        super().__init__()
        self.datapoint = datapoint
        self.data = '<no data provided>' if not data else json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2)
        self.data_explanation = data_explanation

    def prompt(self) -> list[tuple[str, str]]:
        return [
            ('system', 'You are an experienced data analyst and logician.'),
            ('user', INSTRUCTION.format(datapoint=self.datapoint, explanation=self.data_explanation, data=self.data))
        ]

    def handle_result(self, result: str) -> Any:
        return result
    
    def expects_json(self) -> bool:
        return False


convert_to_statement = FrontendQueryRunner(ConvertToStatement)

