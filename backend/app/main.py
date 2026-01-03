# FastAPI entry point
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.guards.auth import verify_api_key




app = FastAPI(title="Formata API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from app.api import ingest, process, status, result, errors, convert, jobs, profile

# Base endpoint (NO authentication required)
@app.get("/")
def read_root():
    return {"message": "Formata API is running"}


# Health check endpoint (NO authentication required)
@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Register protected routes with API key guard
app.include_router(ingest, dependencies=[Depends(verify_api_key)])
app.include_router(process, dependencies=[Depends(verify_api_key)])
app.include_router(status, dependencies=[Depends(verify_api_key)])
app.include_router(result, dependencies=[Depends(verify_api_key)])
app.include_router(errors, dependencies=[Depends(verify_api_key)])
app.include_router(convert, dependencies=[Depends(verify_api_key)])
app.include_router(jobs, dependencies=[Depends(verify_api_key)])
app.include_router(profile, dependencies=[Depends(verify_api_key)])
