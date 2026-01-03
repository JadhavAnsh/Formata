# FastAPI entry point
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.guards.auth import verify_api_key

# For mounting Dash
from fastapi.staticfiles import StaticFiles
import dash
from dash import Dash
from dash import html, dcc
import plotly.express as px

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
app.include_router(ingest.router, dependencies=[Depends(verify_api_key)])
app.include_router(process.router, dependencies=[Depends(verify_api_key)])
app.include_router(status.router, dependencies=[Depends(verify_api_key)])
app.include_router(result.router, dependencies=[Depends(verify_api_key)])
app.include_router(errors.router, dependencies=[Depends(verify_api_key)])
app.include_router(convert.router, dependencies=[Depends(verify_api_key)])
app.include_router(jobs.router, dependencies=[Depends(verify_api_key)])
app.include_router(profile.router, dependencies=[Depends(verify_api_key)])
