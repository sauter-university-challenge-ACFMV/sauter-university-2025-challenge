import os
from fastapi import FastAPI
import uvicorn

app = FastAPI()


@app.get("/")
async def root() -> dict:
    return {"message": "Hello World"}


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
