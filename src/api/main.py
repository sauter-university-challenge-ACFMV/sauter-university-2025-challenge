import os
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from datetime import date
from routers.ons_router import create_router
from dotenv import load_dotenv

# carrega o arquivo .env que está no mesmo diretório do main.py
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

app = FastAPI(
    title="ONS Data Fetcher API",
    description="An API to fetch and filter PARQUET file resources from the ONS open data portal.",
    version="1.0.0",
)

app.include_router(create_router())


class DataFilter(BaseModel):
    start_date: date | None
    end_date: date | None


@app.get("/")
async def root() -> dict:
    return {"message": "Hello World"}


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
