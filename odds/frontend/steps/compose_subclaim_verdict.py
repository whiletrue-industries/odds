import json
from typing import Any

from .frontend_query import FrontendQueryRunner, FrontendQuery

INSTRUCTION = '''
Analyze the claim "{subclaim}" based on the following statements and return your opinion on the probability of the claim being true, and how certain you are in your assessment.
Result should be provided as a single object in a validated json format.

Example response:
{{
    "verdict": <probability of the claim being true, 0-100>,
    "certainty": <level of certainty in the assessment, 0-100>,      
    "verdict_explanation": "<short explanation of the verdict>",
    "certainty_explanation": "<short explanation of the certainty>"
}}

Statements:
{statements}
'''


class ComposeSubclaimVerdict(FrontendQuery):

    def __init__(self, subclaim: str, statements: list[str]):
        super().__init__()
        self.subclaim = subclaim
        self.statements = '\n'.join(f' - {s}' for s in statements)

    def prompt(self) -> list[tuple[str, str]]:
        return [
            ('system', 'You are an experienced data analyst and logician.'),
            ('user', INSTRUCTION.format(subclaim=self.subclaim, statements=self.statements))
        ]

    def handle_result(self, result: str) -> Any:
        return result


compose_subclaim_verdict = FrontendQueryRunner(ComposeSubclaimVerdict)

