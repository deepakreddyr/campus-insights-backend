from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class CampusAnalysis(BaseModel):
    infrastructure_quality_score: int
    maintenance_issues: List[str]
    safety_hazards: List[str]
    compliance_flags: List[str]

class DocumentAnalysis(BaseModel):
    authenticity_score: int
    detected_issues: List[str]
    missing_documents: List[str]
    accreditation_validation: str

class SubjectPerformance(BaseModel):
    subject: str
    score: int

class ClassWiseAnalysis(BaseModel):
    class_name: str = Field(alias="class")
    average: int

    class Config:
        populate_by_name = True

class PerformanceAnalysis(BaseModel):
    top_performing_courses: List[str]
    low_performing_courses: List[str]
    subject_performance: List[SubjectPerformance]
    improvement_recommendations: List[str]
    class_wise_analysis: List[ClassWiseAnalysis]

class InstitutionReport(BaseModel):
    id: str
    name: str
    location: str
    dateAnalyzed: str
    status: str
    overallScore: Optional[int] = None
    campusScore: Optional[int] = None
    complianceScore: Optional[int] = None
    academicScore: Optional[int] = None
    campusAnalysis: Optional[CampusAnalysis] = None
    documentAnalysis: Optional[DocumentAnalysis] = None
    performanceAnalysis: Optional[PerformanceAnalysis] = None

class User(BaseModel):
    id: str
    email: str
    name: str
    role: str

class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    email: str
    password: str
    name: str

class AnalysisRequest(BaseModel):
    name: str
    location: str
    type: str # 'full' | 'fast'
    files: List[str] = []
