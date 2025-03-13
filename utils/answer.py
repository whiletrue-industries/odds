import asyncio
from odds.api.answer import answer_question

async def run():
    async for msg in answer_question(question='What is the most common tree?', deployment_id='camden'):
        print(msg)

asyncio.run(run())