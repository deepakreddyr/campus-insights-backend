from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import sys
import os
import json

# Local imports work when script is run from inside the 'backend' folder
from schemas import User, LoginRequest, SignupRequest, AnalysisRequest, InstitutionReport, AuthResponse
from api_logic import APILogic
from database import supabase
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, File, UploadFile
from typing import Dict

app = FastAPI(title="Insightful Campus API")

# CORS removed (allowed all origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

auth_scheme = HTTPBearer()

async def get_current_user(token: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    try:
        # Verify the token with Supabase
        user_res = supabase.auth.get_user(token.credentials)
        if not user_res.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user_res.user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Welcome to Insightful Campus API"}

# AI Analysis Endpoints
@app.post("/api/analysis/{id}/campus")
async def analyze_campus(
    id: str, 
    files: List[UploadFile] = File(...), 
    user: User = Depends(get_current_user)
):
    image_contents = []
    for file in files:
        image_contents.append(await file.read())
    return APILogic.analyze_campus(id, image_contents)

@app.post("/api/analysis/{id}/documents")
async def analyze_documents(
    id: str, 
    files: List[UploadFile] = File(...), 
    user: User = Depends(get_current_user)
):
    doc_contents = []
    for file in files:
        doc_contents.append(await file.read())
    return APILogic.analyze_documents(id, doc_contents)

@app.post("/api/analysis/{id}/performance")
async def analyze_performance(
    id: str, 
    data: dict, 
    user: User = Depends(get_current_user)
):
    # performance data is usually JSON
    return APILogic.analyze_performance(id, json.dumps(data))


# Auth Endpoints
@app.post("/api/auth/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    return APILogic.login(req)

@app.post("/api/auth/signup", response_model=AuthResponse)
async def signup(req: SignupRequest):
    return APILogic.signup(req)

# Institutions Endpoints
@app.get("/api/institutions", response_model=List[InstitutionReport])
async def get_institutions(user: User = Depends(get_current_user)):
    return APILogic.get_institutions()

@app.get("/api/institutions/{id}", response_model=InstitutionReport)
async def get_institution(id: str, user: User = Depends(get_current_user)):
    inst = APILogic.get_institution(id)
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    return inst

@app.post("/api/analysis/new", response_model=InstitutionReport)
async def create_analysis(req: AnalysisRequest, user: User = Depends(get_current_user)):
    return APILogic.create_analysis(req)

@app.patch("/api/institutions/{id}", response_model=InstitutionReport)
async def update_institution(id: str, data: dict, user: User = Depends(get_current_user)):
    inst = APILogic.update_institution(id, data)
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    return inst

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
