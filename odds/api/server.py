from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Any, Optional

from .answer import answer_question
from .common_endpoints import search_datasets, fetch_dataset, fetch_resource, query_db

### A FastAPI server that serves the odds API
# Exposes the following methods:
# - search_datasets(query: str) -> List[Dict[str, str]]
# - fetch_dataset(id: str) -> Optional[Dict[str, str]]
# - fetch_resource(id: str) -> Optional[Dict[str, str]]
# - query_db(resource_id: str, query: str) -> Optional[Dict[str, Any]]

app = FastAPI()

# Enable CORS:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to the specific origins you want to allow
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/datasets")
async def search_datasets_handler(query: str) -> List[Dict[str, Any]]:
    return await search_datasets(query, None)

@app.get("/dataset/{id}")
async def fetch_dataset_handler(id: str) -> Optional[Dict[str, Any]]:
    return await fetch_dataset(id)

@app.get("/resource/{id}")
async def fetch_resource_handler(id: str) -> Optional[Dict[str, Any]]:
    return await fetch_resource(id)

@app.get("/query/{resource_id}")
async def query_db_handler(resource_id: str, sql: str) -> Optional[Dict[str, Any]]:
    return await query_db(resource_id, sql)

@app.get("/answer")
async def answer_handler(q: Optional[str] = None, id: Optional[str] = None, catalog_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if not q and not id:
        raise HTTPException(status_code=400, detail="Either 'q' or 'id' must be provided")
    ret = await answer_question(question=q, question_id=id, catalog_id=catalog_id)
    if not ret:
        raise HTTPException(status_code=404, detail="Question not found")
    return ret

# Serve static files from the 'ui' directory on the '/' endpoint
app.mount("/", StaticFiles(directory="ui", html=True), name="static")

# Run the server with:
# uvicorn server:app --reload
