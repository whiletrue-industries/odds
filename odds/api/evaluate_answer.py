
from typing import Any
from ..common.llm.llm_query import LLMQuery
from ..common.llm import llm_runner


PROMPT = '''The following are a question posed to an information retrieval system and the answer it returned. Evaluate the quality of the answer.
Use the following criteria in your evaluation:
- The answer must address the question fully and accurately.
- The answer must provide the information requested, and not some related (but not requested) information, or simply unrelated information.
- The answer must contain information sourced from the information system, and not contain information that is based on general knowledge or speculation.
- The answer must contain reference links to the sources of the information provided.

Your response must be provided as a well formatted JSON object with the following fields. Don't add any preambles or postscripts to the JSON object:
{{
    "score": 0-10,  // A score from 0 to 10 indicating the quality of the answer, 10 being the best
    "success": true/false,  // A boolean indicating whether the question was answered correctly based on the criteria above
    "evaluation": "<resoning>"  // A string providing a justification for the score given
}}
----
Question: {0}

Answer:
{1}
'''

class EvaluateQuery(LLMQuery):

    def __init__(self, question, answer):
        super().__init__(None, None)
        self.question = question
        self.answer = answer

    def model(self) -> str:
        return 'expensive'

    def temperature(self) -> float:
        return 0

    def prompt(self) -> list[tuple[str, str]]:
        return  [
            ('system', 'You are an experienced information retrieval specialist.'),
            ('user', PROMPT.format(self.question, self.answer))
        ]

    def handle_result(self, result: dict | str) -> Any:
        self.score = result.get('score') or 0
        self.success = result.get('success') or False
        self.evaluation = result.get('evaluation') or ''

    def expects_json(self) -> bool:
        return True

    def max_tokens(self) -> int:
        return 2048



async def evaluate(question, answer):
    query = EvaluateQuery(question, answer)
    await llm_runner.run(query, ['evaluate', question])
    return dict(
        score=query.score,
        success=query.success,
        evaluation=query.evaluation
    )
