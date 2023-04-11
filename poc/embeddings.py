import json
import os
import openai
import dotenv
import gzip
import pickle
import numpy as np

dotenv.load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

def dataset_text(dataset):
    return f'''A dataset called "{dataset['title']}" published by {dataset['organization']['title']} on {dataset['metadata_created'][:4]}. {(dataset.get('notes') or '')}'''[:500]

try:
    with open('embeddings.pickle', 'rb') as f:
        embeddings = pickle.load(f)
except Exception as e:
    print('Failed to load existing file', str(e))
    embeddings = []
print('Loaded {} embeddings'.format(len(embeddings)))
used = set([k for k, v in embeddings])

with gzip.GzipFile('datasets.json.gz', 'r') as zipped:
    datasets = json.load(zipped)
    print('Loaded {} datasets'.format(len(datasets)))
    for i, dataset in enumerate(datasets):
        key = f'{dataset["ckan_instance"]}/{dataset["name"]}'
        if key in used:
            continue
        text = dataset_text(dataset)
        embedding = openai.Embedding.create(input=text, model='text-embedding-ada-002')
        embedding = embedding['data'][0]['embedding']
        embeddings.append((key, np.array(embedding)))
        if i % 1000 == 0:
            print(i, key, text)
            with open('embeddings.pickle', 'wb') as f:
                pickle.dump(embeddings, f)
            with open('embeddings.pickle.bak', 'wb') as f:
                pickle.dump(embeddings, f)
        used.add(key)

with open('embeddings.pickle', 'wb') as f:
    pickle.dump(embeddings, f)
with open('embeddings.pickle.bak', 'wb') as f:
    pickle.dump(embeddings, f)
