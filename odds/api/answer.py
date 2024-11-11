import json
import yaml

from odds.common.catalog_repo import catalog_repo
from odds.common.cost_collector import CostCollector
from odds.common.embedder import embedder
from odds.common.llm.openai.openai_llm_runner import OpenAILLMRunner

from openai import AsyncOpenAI

from odds.common.vectordb import indexer
from ..common.config import config
from .common_endpoints import search_datasets, fetch_dataset, fetch_resource, query_db


async def loop(client, thread, run, usage, catalog_id):
    while True:
        print('RUN:', run.status)
        if run.status == 'completed': 
            return True
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
                return False
        else:
            print(run.status)
            return False

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


async def answer_question(question, catalog_id):
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
        success = await loop(client, thread, run, usage, catalog_id)
    except Exception as e:
        error = str(e)
    finally:
        print('SUCCESS:', success)
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

        if error:
            return dict(success=False, error=error)
        else:
            return dict(success=success, answer=answer)
