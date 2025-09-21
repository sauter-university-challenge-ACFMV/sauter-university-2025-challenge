import os
from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from datetime import date

from routers import ons_router

app = FastAPI(
    title="ONS Data Fetcher API",
    description="An API to fetch and filter PARQUET file resources from the ONS open data portal.",
    version="1.0.0"
)

app.include_router(ons_router.router)

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
