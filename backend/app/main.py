# FastAPI entry point
from fastapi import FastAPI

app = FastAPI(title="Formata API", version="1.0.0")

# Import routers
from app.api import ingest, process, status, result, errors, convert

# Register routes
app.include_router(ingest.router)
app.include_router(process.router)
app.include_router(status.router)
app.include_router(result.router)
app.include_router(errors.router)
app.include_router(convert.router)


@app.get("/")
def read_root():
    return {"message": "Formata API is running"}
