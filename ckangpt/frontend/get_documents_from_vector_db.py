import openai

from . import get_vector_db_query
from ckangpt import chroma


def main(query, from_user_prompt=False, gpt4=False, num_results=20):
    if from_user_prompt:
        query = get_vector_db_query.main(query, gpt4)
    collection = chroma.get_datasets_collection()
    words = [w.strip() for w in query['words']]
    words += {
        'UK': ['United Kingdom', 'England', 'Britain', 'data.gov.uk', 'uk'],
        'IL': ['Israel', 'ישראל', 'data.gov.il', 'il']
    }.get(query.get('country'), [])
    embeddings = [e['embedding'] for e in openai.Embedding.create(input=[', '.join(words)], engine="text-embedding-ada-002")['data']]
    results = collection.query(
        query_embeddings=embeddings,
        n_results=num_results,
        include=["metadatas", "documents"],
    )
    all_documents = {}
    for word, ids, documents, metadatas in zip(words, results['ids'], results['documents'], results['metadatas']):
        for id, document, metadata in zip(ids, documents, metadatas):
            if id not in all_documents:
                all_documents[id] = {
                    'id': id,
                    'metadata': metadata,
                    'document': document,
                    'words': set(),
                }
            all_documents[id]['words'].add(word)
    return list(all_documents.values())
