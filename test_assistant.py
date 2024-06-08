import json
from collections import Counter
import openai
from openai import OpenAI
from odds.common.config import config
from odds.common.vectordb import indexer
from odds.common.store import store
from odds.common.embedder import embedder
from odds.common.catalog_repo import catalog_repo
from odds.common.llm.cost_collector import CostCollector
from odds.common.llm.openai.openai_llm_runner import OpenAILLMRunner
import sqlite3

import asyncio
import time

ASSISTANT_NAME = 'Open data fact checker'
ASSISTANT_INSTRUCTIONS = """
You are a fact checker for a news organization.
Your main focus is to verify the accuracy of claims made in news articles, by using _only_ public data from governmental open data portals.

You have these tools you might use:
- search_datasets: Search for relevant datasets using semantic search
- fetch_dataset: Retrieve full information about a dataset (based on the dataset's id), including its metadata and the names and ids of the resources it contains.
- fetch_resource: Retrieve full information about a resource (based on the resource's id), including its metadata and its DB schema (so you can query it)
- query_resource_database: Query a resource using an SQL query (you need to fetch the DB schema first in order to do a query)

Your goal is to provide an assessment of the accuracy of each relevant claim in the text, based on the data you find.
You should also provide a confidence score for your assessment.

You avoid asking for any additional data, and you avoid using any data that is not publicly available.
All your responses should be based on the data you find in the open data portals, and include references to the datasets you used.
"""

TOOLS = [
    dict(
        type='function',
        function=dict(
            name='search_datasets',
            description='Find the metadata of relevant datasets using semantic search',
            parameters=dict(
                type='object',
                properties=dict(
                    query=dict(
                        type='string',
                        description='The query string to use to search for datasets. Multiple query terms are allowed, separated by a comma.'
                    ),
                ),
                required=['query']
            )
        )
    ),
    dict(
        type='function',
        function=dict(
            name='fetch_dataset',
            description='Get the full metadata for a single dataset, including the list of its resources',
            parameters=dict(
                type='object',
                properties=dict(
                    dataset_id=dict(
                        type='string',
                        description='The dataset ID to fetch.'
                    ),
                ),
                required=['dataset_id']
            )
        )
    ),
    dict(
        type='function',
        function=dict(
            name='fetch_resource',
            description='Get the full metadata for a single resource in a single dataset ',
            parameters=dict(
                type='object',
                properties=dict(
                    dataset_id=dict(
                        type='string',
                        description='The dataset id containing this resource'
                    ),
                    resource_id=dict(
                        type='string',
                        description='The resource ID to fetch.'
                    ),
                ),
                required=['dataset_id', 'resource_id']
            )
        )
    ),
    dict(
        type='function',
        function=dict(
            name='query_resource_database',
            description='Perform an SQL query on a resource',
            parameters=dict(
                type='object',
                properties=dict(
                    resource_id=dict(
                        type='string',
                        description='The resource ID to query.'
                    ),
                    query=dict(
                        type='string',
                        description='SQLite compatible query to perform on the resource'
                    ),
                ),
                required=['id', 'query']
            )
        )
    ),    
]

async def search_datasets(query: str):
    print('SEARCH DATASETS:', query)
    query_terms = query.split(',')
    query_terms = [term.strip() for term in query_terms]
    query_terms = [term for term in query_terms if term]
    print('QUERY TERMS:', query_terms)
    embeddings = await asyncio.gather(*[embedder.embed(name) for name in query_terms])
    dataset_ids = await asyncio.gather(*[indexer.findDatasets(embedding) for embedding in embeddings])
    dataset_ids = [x for y in dataset_ids for x in y]
    dataset_ids = [x[0] for x in Counter(dataset_ids).most_common(10)]
    print('DATASET IDS:', dataset_ids)
    datasets = await asyncio.gather(*[store.getDataset(id) for id in dataset_ids])
    catalogs = [catalog_repo.get_catalog(dataset.catalogId) for dataset in datasets]
    response = [
        dict(
            id=dataset.storeId(),
            title=dataset.better_title or dataset.title,
            description=dataset.better_description or dataset.description,
            publisher=dataset.publisher,
            catalog=catalog.title,
        )
        for dataset, catalog in zip(datasets, catalogs)
    ]
    print('RESPONSE:', response)
    return response

async def fetch_dataset(id):
    print('FETCH DATASET:', id)
    dataset = await store.getDataset(id)
    response = None
    if dataset:
        response = dict(
            title=dataset.better_title or dataset.title,
            description=dataset.better_description or dataset.description,
            publisher=dataset.publisher,
            publisher_description=dataset.publisher_description,
            resources=[
                dict(
                    id=id + f'##{i}',
                    name=resource.title,
                    num_rows=resource.row_count,
                )
                for i, resource in enumerate(dataset.resources)
            ],            
        )
    print('RESPONSE:', response)
    return response

async def fetch_sesource(id):
    print('FETCH RESOURCE:', id)
    datasetId, resourceIdx = id.split('##')
    resourceIdx = int(resourceIdx)
    dataset = await store.getDataset(datasetId)
    response = None
    if dataset:
        resource = dataset.resources[resourceIdx]
        if resource:
            response = dict(
                name=resource.title,
                fields=[
                    dict(
                        name=field.name,
                        type=field.data_type,
                        max=field.max_value,
                        min=field.min_value,
                        sample_values=field.sample_values,
                    )
                    for field in resource.fields
                ],
                db_schema=resource.db_schema
            )
        print('RESPONSE:', response)
    return response

async def query_db(resource_id, query):
    print('QUERY DB:', resource_id, query)
    datasetId, resourceIdx = resource_id.split('##')
    resourceIdx = int(resourceIdx)
    dataset = await store.getDataset(datasetId)
    if dataset:
        resource = dataset.resources[resourceIdx]
        if resource:
            dbFile = await store.getDB(resource, dataset)
            if dbFile is None:
                print('FAILED TO FIND DB', dbFile)
                return None
            try:
                con = sqlite3.connect(dbFile)
                cur = con.cursor()
                cur.execute(query)
                # Fetch data as a list of dicts:
                data = cur.fetchall()
                headers = [x[0] for x in cur.description]
                data = [dict(zip(headers, row)) for row in data]
                print('GOT DATA', data)
                return dict(success=True, data=data)
            except Exception as e:
                print('FAILED TO QUERY DB', dbFile, repr(e))
                return dict(success=False, error=str(e))
    return None

async def loop(client, thread, run, usage):
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
                    output = await search_datasets(query)
                elif function_name == 'fetch_dataset':
                    id = arguments['dataset_id']
                    output = await fetch_dataset(id)
                elif function_name == 'fetch_resource':
                    id = arguments['resource_id']
                    output = await fetch_sesource(id)
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
                    run = client.beta.threads.runs.submit_tool_outputs_and_poll(
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

def main():
    client = OpenAI(
        api_key=config.credentials.openai.key,
        organization=config.credentials.openai.org,
        project=config.credentials.openai.proj,
    )
    
    assistant = client.beta.assistants.create(
        name=ASSISTANT_NAME,
        instructions=ASSISTANT_INSTRUCTIONS,
        model="gpt-4o",
        tools=TOOLS,
        temperature=0,
    )

    thread = client.beta.threads.create()

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role='user',
        content='Please verify the claims in this article:\n\n' + open('article2.txt').read(),
    )

    usage = CostCollector('assistant', OpenAILLMRunner.COSTS)

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
        temperature=0,
    )
    if run.usage:
        usage.update_cost('expensive', 'prompt', run.usage.prompt_tokens)
        usage.update_cost('expensive', 'completion', run.usage.completion_tokens)

    success = False
    try:
        success = asyncio.run(loop(client, thread, run, usage))
    finally:
        print('SUCCESS:', success)
        messages = client.beta.threads.messages.list(
            thread_id=thread.id, order='asc'
        )
        for message in messages:
            print(f'{message.role}:')
            for block in message.content:
                if block.type == 'text':
                    print(block.text.value)
                else:
                    print(block.type)
                    print(block)
        print('CLEANUP')
        # try:
        #     time.sleep(600)
        # except KeyboardInterrupt:
        #     pass
        client.beta.threads.delete(thread.id)
        client.beta.assistants.delete(assistant.id)
        usage.print_total_usage()

if __name__ == '__main__':
    main()

    