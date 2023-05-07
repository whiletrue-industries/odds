# ckangpt

## Local Development

### Install

```
python3.8 -m venv venv
. venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### Configure

Copy `.env.sample` to `.env` and set your OPENAI_API_KEY

### Frontend Usage

Make a query to the frontend using GPT-4

```
ckangpt frontend find-datasets --gpt4 "Can you find any research on biotoxins in mussels in the UK?"
```

### Backend Usage

Describe a dataset using GPT-4

```
ckangpt backend describe-dataset --gpt4 https://data.gov.uk/other-species-conditions-data
```

### Populate database

This is an advanced feature, you probably don't need to do this, unless you know what you're doing.

To prevent downtime, you should use a new unique collection name to populate the database, then switch the collection name when ready.

```
ckangpt utils convert-poc-to-vector-db "<UNIQUE_COLLECTION_NAME>"
# if there are errors, you can try to continue on the same dataset
ckangpt utils convert-poc-to-vector-db "<UNIQUE_COLLECTION_NAME>" --continue 
```

When done, you can test the collection by setting `CHROMADB_DATASETS_COLLECTION_NAME=datasets2` in the .env

When ready, you can rename the default config for `CHROMADB_DATASETS_COLLECTION_NAME` to the new dataset name and commit.
