import httpx
from fastapi import FastAPI, HTTPException, Request

# A FastAPI app that proxies HTTP requests to the internet.
# Accepts the URL to fetch as a query parameter.
# Returns the response from the URL as a JSON response, including the status code, and body.
# Uses async HTTP requests to fetch the URL.
# Use the same http headers as in here:
#   curl 'https://www.jerusalem.muni.il/he/' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' 
# Also make sure to add http timeout of 30 seconds

app = FastAPI()

@app.get("/fetch")
async def fetch_url(request: Request, url: str):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        timeout = 30.0
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, headers=headers)
            return {
                "status_code": response.status_code,
                "body": response.text
            }
    except httpx.RequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
