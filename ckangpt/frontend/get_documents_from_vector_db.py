import openai

from ckangpt import vectordb, config


def main(query, num_results=config.DEFAULT_NUM_RESULTS):
    vdb = vectordb.get_vector_db_instance()

    def iterator():
        collection = vdb.get_datasets_collection()
        where = {}
        # ckan_instance = {
        #     'UK': 'https://data.gov.uk',
        #     'IL': 'https://data.gov.il',
        #     'ON': 'https://data.ontario.ca',
        # }.get(query['geo']) if query.get('geo') else None
        # if ckan_instance:
        #     where['ckan_instance'] = ckan_instance
        embeddings = openai.Embedding.create(input=query, engine="text-embedding-ada-002")['data'][0]['embedding']
        yield from collection.iterate_query_items(embeddings, num_results=num_results, where=where)

    return iterator()
