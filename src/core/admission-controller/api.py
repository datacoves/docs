import logging

import httpx
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseSettings


class Settings(BaseSettings):
    WEBHOOK_URL: str = None

    class Config:
        env_file = ".env"


settings = Settings()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
app = FastAPI()
client = httpx.AsyncClient(verify=False)


@app.post("/", status_code=200)
async def main(request: Request):
    try:
        data: dict = await request.json()
        r = await client.post(settings.WEBHOOK_URL, json=data)
        response = r.json()
    except Exception as e:
        logger.error(e)
        return JSONResponse({}, status_code=status.HTTP_400_BAD_REQUEST)

    return response


@app.get("/health", status_code=200)
async def health(request: Request):
    return {"health": True}
