from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import sys
import os

# Local imports work when script is run from inside the 'backend' folder
from schemas import User, LoginRequest, SignupRequest, AnalysisRequest, InstitutionReport
from api_logic import APILogic

app = FastAPI(title="Insightful Campus API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, this should be restricted
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to Insightful Campus API"}

# Auth Endpoints
@app.post("/api/auth/login", response_model=User)
async def login(req: LoginRequest):
    return APILogic.login(req)

@app.post("/api/auth/signup", response_model=User)
async def signup(req: SignupRequest):
    return APILogic.signup(req)

# Institutions Endpoints
@app.get("/api/institutions", response_model=List[InstitutionReport])
async def get_institutions():
    return APILogic.get_institutions()

@app.get("/api/institutions/{id}", response_model=InstitutionReport)
async def get_institution(id: str):
    inst = APILogic.get_institution(id)
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    return inst

@app.post("/api/analysis/new", response_model=InstitutionReport)
async def create_analysis(req: AnalysisRequest):
    return APILogic.create_analysis(req)

@app.patch("/api/institutions/{id}", response_model=InstitutionReport)
async def update_institution(id: str, data: dict):
    inst = APILogic.update_institution(id, data)
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    return inst

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
