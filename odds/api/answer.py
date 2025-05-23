import dataclasses
import json
import yaml
from pathlib import Path

from odds.common.datatypes import Deployment
from odds.common.deployment_repo import deployment_repo
from odds.common.qa_repo import qa_repo
from odds.common.cost_collector import CostCollector
from odds.common.llm.openai.openai_llm_runner import OpenAILLMRunner

from openai import AsyncOpenAI
from openai.types.beta.assistant_stream_event import AssistantStreamEvent

from ..common.config import config
from .common_endpoints import search_datasets, fetch_dataset, fetch_resource, query_db
from .evaluate_answer import evaluate

ROOT = Path(__file__).parent.parent.parent

async def loop(client, thread, stream, usage, deployment):
    while True:
        event: AssistantStreamEvent = await stream.__anext__()
        # print(f'Event: {event.event}, data: {repr(event.data)[:100]}')
        if event.event == 'thread.run.completed':
            run = event.data
            if run.usage:
                usage.update_cost('expensive', 'prompt', run.usage.prompt_tokens)
                usage.update_cost('expensive', 'completion', run.usage.completion_tokens)
            yield dict(success=True, error=None)
            return
        elif event.event == 'thread.run.requires_action':
            run = event.data
            tool_outputs = []
            for tool in run.required_action.submit_tool_outputs.tool_calls:
                if not tool.type == 'function':
                    continue
                print(f'TOOL - {tool.type}: {tool.function.name}({tool.function.arguments})')
                arguments = json.loads(tool.function.arguments)
                function_name = tool.function.name
                yield dict(type='tool', value=dict(
                    name=function_name,
                    arguments=arguments
                ))
                if function_name == 'search_datasets':
                    query = arguments['query']
                    output = await search_datasets(query, deployment.catalogIds)
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
                    stream = await client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs,
                        stream=True
                    )
                    print("Tool outputs submitted successfully.")
                    continue
                except Exception as e:
                    print("Failed to submit tool outputs:", e)
            else:
                yield dict(type='error', value='No tool outputs to submit.')
                return
        elif event.event == 'thread.message.delta':
            text = ''
            for block in event.data.delta.content:
                if block.type == 'text' and block.text.value:
                    text += block.text.value
            yield dict(type='text', value=text)

assistant_ids = dict()
async def get_assistant_id(client: AsyncOpenAI, deployment: Deployment):
    assistant_id = assistant_ids.get(deployment.id)
    if assistant_id is not None:
        return assistant_id
    assistant_name = f"{config.assistant.name} ({deployment.id})"
    assistants = await client.beta.assistants.list()
    async for assistant in assistants:
        if assistant.name == assistant_name:
            assistant_ids[deployment.id] = assistant.id
            return assistant.id
    instructions = (ROOT / config.assistant.instructions_file).open().read()
    instructions = instructions\
        .replace(":org-name:", deployment.agentOrgName)\
        .replace(":catalog-descriptions:", deployment.agentCatalogDescriptions)
    assistant = await client.beta.assistants.create(
        name=assistant_name,
        description=f'{config.assistant.description} for {deployment.agentOrgName}',
        instructions=instructions,
        model="gpt-4o",
        tools=yaml.safe_load((ROOT / config.assistant.tools_file).open()),
        temperature=0,
    )
    assistant_id = assistant.id
    return assistant_id


async def answer_question(*, question=None, question_id=None, deployment_id=None):

    ret = dict()
    qa = await qa_repo.getQuestion(question=question, id=question_id, deployment_id=deployment_id)
    if question_id and not qa:
        yield dict(type='not-found')
        return
    
    if qa is None:
        yield dict(type='status', value='preparing')
        deployment = await deployment_repo.get_deployment(deployment_id)

        client = AsyncOpenAI(
            api_key=config.credentials.openai.key,
            organization=config.credentials.openai.org,
            project=config.credentials.openai.proj,
        )
        
        assistant_id = await get_assistant_id(client, deployment)

        thread = await client.beta.threads.create()

        await client.beta.threads.messages.create(
            thread_id=thread.id,
            role='user',
            content=question,
        )

        answer = ''

        usage = CostCollector('assistant', OpenAILLMRunner.COSTS)

        yield dict(type='status', value='running')
        stream = await client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id,
            temperature=0,
            stream=True
        )

        # if run.usage: TODO
        #     usage.update_cost('expensive', 'prompt', run.usage.prompt_tokens)
        #     usage.update_cost('expensive', 'completion', run.usage.completion_tokens)
        # success = False
        # error = None
        # try:
        #     success, error = await loop(client, thread, run, usage, deployment)

        success, error = False, None
        try:
            result = None
            async for msg in loop(client, thread, stream, usage, deployment):
                result = msg
                if 'type' in msg:
                    yield msg
                assert not msg.get('type') == 'error', msg.get('value')
            success, error = result['success'], result['error']
        except Exception as e:
            error = str(e)
        finally:
            yield dict(type='status', value='complete')
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
            qa = await qa_repo.storeQA(question, answer, evaluation['success'], evaluation['score'], deployment_id)
            ret['id'] = qa.id
        ret['related'] = [dataclasses.asdict(x) for x in await qa_repo.findRelated(ret['question'], ret['id'], deployment_id)]
    yield dict(type='answer', value=ret)
