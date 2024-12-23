import dataclasses
import json
import yaml

from odds.common.qa_repo import qa_repo
from odds.common.cost_collector import CostCollector
from odds.common.llm.openai.openai_llm_runner import OpenAILLMRunner

from openai import AsyncOpenAI

from ..common.config import config
from .common_endpoints import search_datasets, fetch_dataset, fetch_resource, query_db
from .evaluate_answer import evaluate


async def loop(client, thread, run, usage, catalog_id):
    while True:
        print('RUN:', run.status)
        if run.status == 'completed': 
            return True, None
        elif run.status == 'requires_action':
            tool_outputs = []
            for tool in run.required_action.submit_tool_outputs.tool_calls:
                if not tool.type == 'function':
                    continue
                print(f'TOOL - {tool.type}: {tool.function.name}({tool.function.arguments})')
                arguments = json.loads(tool.function.arguments)
                function_name = tool.function.name
                if function_name == 'search_datasets':
                    query = arguments['query']
                    output = await search_datasets(query, catalog_id)
                elif function_name == 'fetch_dataset':
                    id = arguments['dataset_id']
                    output = await fetch_dataset(id)
                elif function_name == 'fetch_resource':
                    id = arguments['resource_id']
                    output = await fetch_resource(id)
                elif function_name == 'query_resource_database':
                    id = arguments['resource_id']
                    query = arguments['query']
                    output = await query_db(id, query)
                output = json.dumps(output, ensure_ascii=False)
                tool_outputs.append(dict(
                    tool_call_id=tool.id,
                    output=output
                ))
            
            # Submit all tool outputs at once after collecting them in a list
            if tool_outputs:
                try:
                    run = await client.beta.threads.runs.submit_tool_outputs_and_poll(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs,
                    )
                    if run.usage:
                        usage.update_cost('expensive', 'prompt', run.usage.prompt_tokens)
                        usage.update_cost('expensive', 'completion', run.usage.completion_tokens)
                    print("Tool outputs submitted successfully.")
                    continue
                except Exception as e:
                    print("Failed to submit tool outputs:", e)
            else:
                return False, 'No tool outputs to submit.'
        else:
            return False, str(run.status)

assistant_id = None
async def get_assistant_id(client: AsyncOpenAI):
    global assistant_id
    if assistant_id is not None:
        return assistant_id
    assistants = await client.beta.assistants.list()
    async for assistant in assistants:
        if assistant.name == config.assistant.name:
            assistant_id = assistant.id
            return assistant_id
    assistant = await client.beta.assistants.create(
        name=config.assistant.name,
        description=config.assistant.description,
        instructions=open(config.assistant.instructions_file).read(),
        model="gpt-4o",
        tools=yaml.safe_load(open(config.assistant.tools_file)),
        temperature=0,
    )
    assistant_id = assistant.id
    return assistant_id


async def answer_question(*, question=None, catalog_id=None, question_id=None):

    ret = dict()
    qa = await qa_repo.getQuestion(question=question, id=question_id)
    if question_id and not qa:
        return None
    
    if qa is None:
        client = AsyncOpenAI(
            api_key=config.credentials.openai.key,
            organization=config.credentials.openai.org,
            project=config.credentials.openai.proj,
        )
        
        assistant_id = await get_assistant_id(client)

        thread = await client.beta.threads.create()

        await client.beta.threads.messages.create(
            thread_id=thread.id,
            role='user',
            content=question,
        )

        answer = ''

        usage = CostCollector('assistant', OpenAILLMRunner.COSTS)

        run = await client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant_id,
            temperature=0,
        )
        if run.usage:
            usage.update_cost('expensive', 'prompt', run.usage.prompt_tokens)
            usage.update_cost('expensive', 'completion', run.usage.completion_tokens)

        success = False
        error = None
        try:
            success, error = await loop(client, thread, run, usage, catalog_id)
        except Exception as e:
            error = str(e)
        finally:
            messages = await client.beta.threads.messages.list(
                thread_id=thread.id, order='asc'
            )
            answer = ''
            async for message in messages:
                if message.role == 'assistant':
                    for block in message.content:
                        if block.type == 'text':
                            answer += block.text.value
            usage.print_total_usage()

            await client.beta.threads.delete(thread.id)
            ret.update(
                dict(id=None, question=question, success=success, error=error)
            )
            if not error:
                ret['answer'] = answer


    else:
        ret.update(
            dict(id=qa.id, question=qa.question, answer=qa.answer, success=qa.success, error=None)
        )

    if not ret['error']:
        if not ret['id']:
            evaluation = await evaluate(question, answer)
            ret.update(evaluation)
            qa = await qa_repo.storeQA(question, answer, evaluation['success'], evaluation['score'])
            ret['id'] = qa.id
        ret['related'] = [dataclasses.asdict(x) for x in await qa_repo.findRelated(ret['question'], ret['id'])]
    return ret
