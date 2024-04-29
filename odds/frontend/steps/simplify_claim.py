from typing import Any

from .frontend_query import FrontendQueryRunner, FrontendQuery

INSTRUCTION = '''
Generate a list of no more than 3 individual, separately verifiable claims, which combined are equivalent to the following compound claim: "{claim}".
If the claim is already an individual claim, return it as the only element in the list.
Return the list as an array of strings, in a validated json format.
'''


class SimplifyClaim(FrontendQuery):

    def __init__(self, claim: str):
        super().__init__()
        self.claim = claim

    def prompt(self) -> list[tuple[str, str]]:
        return [
            ('system', 'You are an experienced data analyst and logician.'),
            ('user', INSTRUCTION.format(claim=self.claim))
        ]

    def handle_result(self, result: list[str]) -> Any:
        return result


simplify_claim = FrontendQueryRunner(SimplifyClaim)

