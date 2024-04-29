from typing import Any
import datetime

from .frontend_query import FrontendQueryRunner, FrontendQuery

INSTRUCTION = '''
Review the article carefully, identify and extract the 3 most crucial stand alone claims made within the text.
Each claim should be exact, objective and simple to verify for credibility using factual, numeric, data which might be found in an official published dataset.

For each claim, provide its text verbatim, a brief reason explaining why its verifiable by referencing relevant official datasets, and the name of the geographic region it refers to, if applicable.
If the claim refers to a time frame, make sure that it contains absolute dates or time periods and not relative ones (the current date is {date})
Show results as an array of objects, in a validated json format.

Example response:
[
    {{
        "quote": "When the unemployment went low by two percent during the previous quarter",
        "geo": "Canada",
        "claim": "The unemployment rate decreased by 2 percent in the last quarter.",
        "sources": "unemployment rates are published periodically by the UK's Department of Labor"
    }},
    ...
]

Article Text:
{article_text}
'''


class ExtractClaims(FrontendQuery):

    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def prompt(self) -> list[tuple[str, str]]:
        return [
            ('system', 'You are an experienced data analyst.'),
            ('user', INSTRUCTION.format(article_text=self.text, date=datetime.datetime.now().strftime('%Y-%m-%d')))
        ]

    def handle_result(self, result: list[dict]) -> Any:
        return [x['claim'] for x in result]


extract_claims = FrontendQueryRunner(ExtractClaims)