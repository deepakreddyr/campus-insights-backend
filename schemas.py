from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class CampusAnalysis(BaseModel):
    infrastructure_quality_score: int = Field(alias="infrastructure_score")
    maintenance_issues: List[str]
    safety_hazards: List[str]
    compliance_flags: List[str]

    class Config:
        populate_by_name = True

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
    top_performing_courses: List[str] = Field(alias="top_courses")
    low_performing_courses: List[str] = Field(alias="low_courses")
    subject_performance: List[SubjectPerformance]
    improvement_recommendations: List[str] = Field(alias="recommendations")
    class_wise_analysis: List[ClassWiseAnalysis]

    class Config:
        populate_by_name = True

class InstitutionReport(BaseModel):
    id: str
    name: str
    location: str
    dateAnalyzed: str = Field(alias="date_analyzed")
    status: str
    overallScore: Optional[int] = Field(None, alias="overall_score")
    campusScore: Optional[int] = Field(None, alias="campus_score")
    complianceScore: Optional[int] = Field(None, alias="compliance_score")
    academicScore: Optional[int] = Field(None, alias="academic_score")
    campusAnalysis: Optional[CampusAnalysis] = None
    documentAnalysis: Optional[DocumentAnalysis] = None
    performanceAnalysis: Optional[PerformanceAnalysis] = None

    class Config:
        populate_by_name = True

class User(BaseModel):
    id: str
    email: str
    name: str
    role: str

class AuthResponse(BaseModel):
    user: User
    access_token: str
    refresh_token: Optional[str] = None

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
