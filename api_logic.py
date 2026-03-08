import datetime
import uuid
from typing import List, Optional, Dict
from schemas import (
    User, LoginRequest, SignupRequest, AnalysisRequest, 
    InstitutionReport, CampusAnalysis, DocumentAnalysis, PerformanceAnalysis,
    AuthResponse
)
from database import supabase, supabase_admin
from openai_service import OpenAIService

class APILogic:
    @staticmethod
    def analyze_campus(report_id: str, image_contents: List[bytes]) -> Dict:
        """Analyze campus images and save to DB."""
        ai_result = OpenAIService.analyze_campus(image_contents)
        
        # Save to Supabase
        supabase_admin.table("campus_analysis").upsert({
            "report_id": report_id,
            "infrastructure_score": ai_result.get("infrastructure_score"),
            "maintenance_issues": ai_result.get("maintenance_issues"),
            "safety_hazards": ai_result.get("safety_hazards"),
            "compliance_flags": ai_result.get("compliance_flags")
        }).execute()
        
        # Update main report score
        supabase_admin.table("analysis_reports").update({
            "campus_score": ai_result.get("infrastructure_score")
        }).eq("id", report_id).execute()
        
        return ai_result

    @staticmethod
    def analyze_documents(report_id: str, doc_contents: List[bytes]) -> Dict:
        """Analyze documents using Vision and save to DB."""
        ai_result = OpenAIService.analyze_documents(doc_contents)
        
        supabase_admin.table("document_analysis").upsert({
            "report_id": report_id,
            "authenticity_score": ai_result.get("authenticity_score"),
            "detected_issues": ai_result.get("detected_issues"),
            "missing_documents": ai_result.get("missing_documents"),
            "accreditation_validation": ai_result.get("accreditation_validation")
        }).execute()
        
        # Update main report score
        supabase_admin.table("analysis_reports").update({
            "compliance_score": ai_result.get("authenticity_score")
        }).eq("id", report_id).execute()
        
        return ai_result

    @staticmethod
    def analyze_performance(report_id: str, performance_data: str) -> Dict:
        """Analyze performance data and save to DB."""
        ai_result = OpenAIService.analyze_performance(performance_data)
        
        p_res = supabase_admin.table("performance_analysis").upsert({
            "report_id": report_id,
            "top_courses": ai_result.get("top_courses"),
            "low_courses": ai_result.get("low_courses"),
            "recommendations": ai_result.get("recommendations")
        }).execute()
        p_id = p_res.data[0]["id"]
        
        if "subject_performance" in ai_result:
            supabase_admin.table("subject_performance").delete().eq("performance_id", p_id).execute()
            supabase_admin.table("subject_performance").insert([
                {"performance_id": p_id, **s} for s in ai_result["subject_performance"]
            ]).execute()
            
        if "class_wise_analysis" in ai_result:
            supabase_admin.table("class_wise_performance").delete().eq("performance_id", p_id).execute()
            supabase_admin.table("class_wise_performance").insert([
                {"performance_id": p_id, "class_name": c["class"], "average_score": c["average"]} 
                for c in ai_result["class_wise_analysis"]
            ]).execute()

        # Update main report score
        supabase_admin.table("analysis_reports").update({
            "academic_score": ai_result.get("academicScore"),
            "status": "completed"
        }).eq("id", report_id).execute()
        
        return ai_result

    @staticmethod
    def login(req: LoginRequest) -> AuthResponse:
        # Use Supabase Auth to sign in
        try:
            auth_response = supabase.auth.sign_in_with_password({
                "email": req.email,
                "password": req.password
            })
            
            if not auth_response.user:
                raise Exception("Login failed")
                
            # Fetch additional user data from public.users
            response = supabase_admin.table("users").select("*").eq("id", auth_response.user.id).execute()
            if not response.data:
                # If profile doesn't exist, return basic auth info
                user = User(
                    id=auth_response.user.id,
                    email=auth_response.user.email,
                    name=auth_response.user.email.split("@")[0],
                    role="user"
                )
            else:
                user = User(**response.data[0])

            return AuthResponse(
                user=user,
                access_token=auth_response.session.access_token,
                refresh_token=auth_response.session.refresh_token
            )
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail=str(e))

    @staticmethod
    def signup(req: SignupRequest) -> AuthResponse:
        try:
            # 1. Sign up with Supabase Auth
            auth_response = supabase.auth.sign_up({
                "email": req.email,
                "password": req.password,
            })
            
            if not auth_response.user:
                raise Exception("Signup failed")
            
            # 2. Create profile in public.users table using admin client to bypass RLS
            user_id = auth_response.user.id
            new_user = {
                "id": user_id,
                "email": req.email,
                "name": req.name,
                "role": "user"
            }
            supabase_admin.table("users").insert(new_user).execute()
            
            return AuthResponse(
                user=User(**new_user),
                access_token=auth_response.session.access_token if auth_response.session else "Check Email for confirmation",
                refresh_token=auth_response.session.refresh_token if auth_response.session else None
            )
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    def get_institutions() -> List[InstitutionReport]:
        response = supabase_admin.table("analysis_reports").select("*, institutions(*)").execute()
        reports = []
        for item in response.data:
            inst = item.pop("institutions")
            report_data = {
                **item,
                "name": inst["name"],
                "location": inst["location"],
            }
            reports.append(InstitutionReport(**report_data))
        return reports

    @staticmethod
    def get_institution(id: str) -> Optional[InstitutionReport]:
        response = supabase_admin.table("analysis_reports").select("*, institutions(*)").eq("id", id).single().execute()
        if not response.data:
            return None
        
        item = response.data
        inst = item.pop("institutions")
        report_data = {
            **item,
            "name": inst["name"],
            "location": inst["location"],
        }
        
        # Fetch nested data if needed
        campus = supabase_admin.table("campus_analysis").select("*").eq("report_id", id).execute()
        if campus.data:
            report_data["campusAnalysis"] = campus.data[0]
            
        docs = supabase_admin.table("document_analysis").select("*").eq("report_id", id).execute()
        if docs.data:
            report_data["documentAnalysis"] = docs.data[0]
            
        perf = supabase_admin.table("performance_analysis").select("*, subject_performance(*), class_wise_performance(*)").eq("report_id", id).execute()
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
        inst_res = supabase_admin.table("institutions").insert({
            "name": req.name,
            "location": req.location
        }).execute()
        inst_id = inst_res.data[0]["id"]
        
        # 2. Create Report
        report_res = supabase_admin.table("analysis_reports").insert({
            "institution_id": inst_id,
            "status": "processing",
            "date_analyzed": datetime.datetime.now().isoformat()
        }).execute()
        
        report_item = report_res.data[0]
        return InstitutionReport(
            id=report_item["id"],
            name=req.name,
            location=req.location,
            date_analyzed=report_item["date_analyzed"],
            status="processing"
        )

    @staticmethod
    def update_institution(id: str, data: dict) -> Optional[InstitutionReport]:
        # Handle complex updates for nested tables
        main_fields = ["status", "overallScore", "campusScore", "complianceScore", "academicScore"]
        update_data = {k: v for k, v in data.items() if k in main_fields}
        
        if update_data:
            # Map camelCase to snake_case if necessary, though currently schemas match
            supabase_admin.table("analysis_reports").update(update_data).eq("id", id).execute()
            
        # Handle nested analysis data updates
        if "campusAnalysis" in data:
            c = data["campusAnalysis"]
            supabase_admin.table("campus_analysis").upsert({
                "report_id": id,
                "infrastructure_score": c.get("infrastructure_quality_score"),
                "maintenance_issues": c.get("maintenance_issues"),
                "safety_hazards": c.get("safety_hazards"),
                "compliance_flags": c.get("compliance_flags")
            }).execute()
            
        if "documentAnalysis" in data:
            d = data["documentAnalysis"]
            supabase_admin.table("document_analysis").upsert({
                "report_id": id,
                "authenticity_score": d.get("authenticity_score"),
                "detected_issues": d.get("detected_issues"),
                "missing_documents": d.get("missing_documents"),
                "accreditation_validation": d.get("accreditation_validation")
            }).execute()
            
        if "performanceAnalysis" in data:
            p = data["performanceAnalysis"]
            p_res = supabase_admin.table("performance_analysis").upsert({
                "report_id": id,
                "top_courses": p.get("top_performing_courses"),
                "low_courses": p.get("low_performing_courses"),
                "recommendations": p.get("improvement_recommendations")
            }).execute()
            p_id = p_res.data[0]["id"]
            
            # Handle list updates (simple clear and re-insert for dummy logic)
            if "subject_performance" in p:
                supabase_admin.table("subject_performance").delete().eq("performance_id", p_id).execute()
                supabase_admin.table("subject_performance").insert([
                    {"performance_id": p_id, **s} for s in p["subject_performance"]
                ]).execute()
                
            if "class_wise_analysis" in p:
                supabase_admin.table("class_wise_performance").delete().eq("performance_id", p_id).execute()
                supabase_admin.table("class_wise_performance").insert([
                    {"performance_id": p_id, "class_name": c["class"], "average_score": c["average"]} 
                    for c in p["class_wise_analysis"]
                ]).execute()

        return APILogic.get_institution(id)
