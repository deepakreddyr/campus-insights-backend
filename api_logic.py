import datetime
import uuid
from typing import List, Optional
from schemas import (
    User, LoginRequest, SignupRequest, AnalysisRequest, 
    InstitutionReport, CampusAnalysis, DocumentAnalysis, PerformanceAnalysis
)
from database import supabase

class APILogic:
    @staticmethod
    def login(req: LoginRequest) -> User:
        # For professional auth, you should use supabase.auth.sign_in_with_password
        # For now, we'll keep it simple and just return a user if it exists in our 'users' table
        response = supabase.table("users").select("*").eq("email", req.email).execute()
        if not response.data:
            # Fallback or create mock for now if table is empty
            return User(id=str(uuid.uuid4()), email=req.email, name=req.email.split("@")[0], role="admin")
        
        user_data = response.data[0]
        return User(**user_data)

    @staticmethod
    def signup(req: SignupRequest) -> User:
        user_id = str(uuid.uuid4())
        new_user = {
            "id": user_id,
            "email": req.email,
            "name": req.name,
            "role": "user"
        }
        supabase.table("users").insert(new_user).execute()
        return User(**new_user)

    @staticmethod
    def get_institutions() -> List[InstitutionReport]:
        response = supabase.table("analysis_reports").select("*, institutions(*)").execute()
        reports = []
        for item in response.data:
            inst = item.pop("institutions")
            report = {
                **item,
                "name": inst["name"],
                "location": inst["location"],
                "dateAnalyzed": item["date_analyzed"]
            }
            reports.append(InstitutionReport(**report))
        return reports

    @staticmethod
    def get_institution(id: str) -> Optional[InstitutionReport]:
        response = supabase.table("analysis_reports").select("*, institutions(*)").eq("id", id).single().execute()
        if not response.data:
            return None
        
        item = response.data
        inst = item.pop("institutions")
        report_data = {
            **item,
            "name": inst["name"],
            "location": inst["location"],
            "dateAnalyzed": item["date_analyzed"]
        }
        
        # Fetch nested data if needed
        campus = supabase.table("campus_analysis").select("*").eq("report_id", id).execute()
        if campus.data:
            report_data["campusAnalysis"] = campus.data[0]
            
        docs = supabase.table("document_analysis").select("*").eq("report_id", id).execute()
        if docs.data:
            report_data["documentAnalysis"] = docs.data[0]
            
        perf = supabase.table("performance_analysis").select("*, subject_performance(*), class_wise_performance(*)").eq("report_id", id).execute()
        if perf.data:
            p_item = perf.data[0]
            p_item["subject_performance"] = p_item.pop("subject_performance")
            p_item["class_wise_analysis"] = [
                {"class": c["class_name"], "average": c["average_score"]} 
                for c in p_item.pop("class_wise_performance")
            ]
            report_data["performanceAnalysis"] = p_item
            
        return InstitutionReport(**report_data)

    @staticmethod
    def create_analysis(req: AnalysisRequest) -> InstitutionReport:
        # 1. Create Institution
        inst_res = supabase.table("institutions").insert({
            "name": req.name,
            "location": req.location
        }).execute()
        inst_id = inst_res.data[0]["id"]
        
        # 2. Create Report
        report_res = supabase.table("analysis_reports").insert({
            "institution_id": inst_id,
            "status": "processing",
            "date_analyzed": datetime.datetime.now().isoformat()
        }).execute()
        
        report_item = report_res.data[0]
        return InstitutionReport(
            id=report_item["id"],
            name=req.name,
            location=req.location,
            dateAnalyzed=report_item["date_analyzed"],
            status="processing"
        )

    @staticmethod
    def update_institution(id: str, data: dict) -> Optional[InstitutionReport]:
        # Handle complex updates for nested tables
        main_fields = ["status", "overallScore", "campusScore", "complianceScore", "academicScore"]
        update_data = {k: v for k, v in data.items() if k in main_fields}
        
        if update_data:
            # Map camelCase to snake_case if necessary, though currently schemas match
            supabase.table("analysis_reports").update(update_data).eq("id", id).execute()
            
        # Handle nested analysis data updates
        if "campusAnalysis" in data:
            c = data["campusAnalysis"]
            supabase.table("campus_analysis").upsert({
                "report_id": id,
                "infrastructure_score": c.get("infrastructure_quality_score"),
                "maintenance_issues": c.get("maintenance_issues"),
                "safety_hazards": c.get("safety_hazards"),
                "compliance_flags": c.get("compliance_flags")
            }).execute()
            
        if "documentAnalysis" in data:
            d = data["documentAnalysis"]
            supabase.table("document_analysis").upsert({
                "report_id": id,
                "authenticity_score": d.get("authenticity_score"),
                "detected_issues": d.get("detected_issues"),
                "missing_documents": d.get("missing_documents"),
                "accreditation_validation": d.get("accreditation_validation")
            }).execute()
            
        if "performanceAnalysis" in data:
            p = data["performanceAnalysis"]
            p_res = supabase.table("performance_analysis").upsert({
                "report_id": id,
                "top_courses": p.get("top_performing_courses"),
                "low_courses": p.get("low_performing_courses"),
                "recommendations": p.get("improvement_recommendations")
            }).execute()
            p_id = p_res.data[0]["id"]
            
            # Handle list updates (simple clear and re-insert for dummy logic)
            if "subject_performance" in p:
                supabase.table("subject_performance").delete().eq("performance_id", p_id).execute()
                supabase.table("subject_performance").insert([
                    {"performance_id": p_id, **s} for s in p["subject_performance"]
                ]).execute()
                
            if "class_wise_analysis" in p:
                supabase.table("class_wise_performance").delete().eq("performance_id", p_id).execute()
                supabase.table("class_wise_performance").insert([
                    {"performance_id": p_id, "class_name": c["class"], "average_score": c["average"]} 
                    for c in p["class_wise_analysis"]
                ]).execute()

        return APILogic.get_institution(id)
