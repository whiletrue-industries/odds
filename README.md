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

### Frontend usage

Download the ChromaDB

```
ckangpt utils download-chroma-db
```

Make a query to the frontend using GPT-4

```
ckangpt frontend find-dataset --gpt4 "Can you find any research on biotoxins in mussels in the UK?"
```
