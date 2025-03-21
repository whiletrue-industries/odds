import json
import dataclasses
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Any, Optional
from sse_starlette.sse import EventSourceResponse

from .answer import answer_question
from .common_endpoints import search_datasets, fetch_dataset, fetch_resource, query_db
from ..common.deployment_repo import deployment_repo
from .admin import router as admin_router

app = FastAPI(openapi_url=None)
app.include_router(admin_router)

# Enable CORS:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to the specific origins you want to allow
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
}

@app.get("/datasets")
async def search_datasets_handler(query: str, deployment_id: str) -> List[Dict[str, Any]]:
    deployment = await deployment_repo.get_deployment(deployment_id)
    return await search_datasets(query, deployment.catalogIds)

@app.get("/dataset/{id}")
async def fetch_dataset_handler(id: str) -> Optional[Dict[str, Any]]:
    return await fetch_dataset(id)

@app.get("/resource/{id}")
async def fetch_resource_handler(id: str) -> Optional[Dict[str, Any]]:
    return await fetch_resource(id)

@app.get("/query/{resource_id}")
async def query_db_handler(resource_id: str, sql: str) -> Optional[Dict[str, Any]]:
    return await query_db(resource_id, sql)

def check_answer(deployment_id, q, id):
    if not deployment_id:
        raise HTTPException(status_code=400, detail="deployment_id must be provided")        
    if not (q or id):
        raise HTTPException(status_code=400, detail="Either 'q' or 'id' must be provided")

@app.get("/answer")
async def answer_handler(q: Optional[str] = None, id: Optional[str] = None, deployment_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    check_answer(deployment_id, q, id)
    ret = None
    async for msg in answer_question(question=q, question_id=id, deployment_id=deployment_id):
        if msg['type'] == 'answer':
            ret = msg['value']
        if msg['type'] == 'not-found':
            raise HTTPException(status_code=404, detail="Question not found")
    return ret

@app.get("/answer-streaming")
async def answer_streaming_handler(q: Optional[str] = None, id: Optional[str] = None, deployment_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    check_answer(deployment_id, q, id)
    async def gen():
        async for msg in answer_question(question=q, question_id=id, deployment_id=deployment_id):
            yield dict(data=json.dumps(msg, ensure_ascii=False))
    return EventSourceResponse(gen(), headers=CORS_HEADERS)

@app.get("/deployment/{deployment_id}")
async def fetch_deployment(deployment_id: str) -> Optional[Dict[str, Any]]:
    dep = await deployment_repo.get_deployment(deployment_id)
    if not dep:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return dataclasses.asdict(dep)

# Run the server with:
# uvicorn server:app --reload
