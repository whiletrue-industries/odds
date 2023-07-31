import openai

from . import get_vector_db_query
from ckangpt import vectordb, config


def main(query, from_user_prompt=False, num_results=config.DEFAULT_NUM_RESULTS):
    vdb = vectordb.get_vector_db_instance()
    usage = None
    if from_user_prompt:
        usage, query = get_vector_db_query.main(query)

    def iterator():
        collection = vdb.get_datasets_collection()
        words = [w.strip() for w in query['words']]
        ckan_instance = {
            'UK': 'https://data.gov.uk',
            'IL': 'https://data.gov.il',
            'ON': 'https://data.ontario.ca',
        }.get(query['country']) if query.get('country') else None
        where = {}
        if ckan_instance:
            where['ckan_instance'] = ckan_instance
        embeddings = openai.Embedding.create(input=', '.join(words), engine="text-embedding-ada-002")['data'][0]['embedding']
        yield from collection.iterate_query_items(embeddings, num_results=num_results, where=where)

    return usage, iterator()
