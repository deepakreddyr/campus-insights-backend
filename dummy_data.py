from typing import List, Dict, Any

# Current user context
CURRENT_USER = {
    "id": "user-1",
    "email": "demo@example.com",
    "name": "Demo User",
    "role": "admin"
}

# Initial Institutions data from existing frontend state
INSTITUTIONS = [
    {
        "id": "demo-1",
        "name": "Delhi Technical University",
        "location": "New Delhi, India",
        "dateAnalyzed": "2026-02-15",
        "status": "completed",
        "overallScore": 82,
        "campusScore": 78,
        "complianceScore": 88,
        "academicScore": 80,
        "campusAnalysis": {
            "infrastructure_quality_score": 78,
            "maintenance_issues": ["Minor paint peeling in Block C", "Water cooler needs servicing"],
            "safety_hazards": ["Fire extinguisher expired in Lab 3"],
            "compliance_flags": ["All safety exits properly marked"],
        },
        "documentAnalysis": {
            "authenticity_score": 92,
            "detected_issues": ["Certificate #45 has unclear stamp"],
            "missing_documents": ["Updated NAAC report"],
            "accreditation_validation": "Valid until 2027",
        },
        "performanceAnalysis": {
            "top_performing_courses": ["Computer Science", "Electronics"],
            "low_performing_courses": ["Civil Engineering"],
            "subject_performance": [
                {"subject": "Mathematics", "score": 75},
                {"subject": "Physics", "score": 82},
                {"subject": "Chemistry", "score": 68},
                {"subject": "Computer Science", "score": 90},
                {"subject": "English", "score": 72},
            ],
            "improvement_recommendations": ["Increase lab hours for Civil Engineering", "Add remedial classes for Chemistry"],
            "class_wise_analysis": [
                {"class": "1st Year", "average": 72},
                {"class": "2nd Year", "average": 76},
                {"class": "3rd Year", "average": 80},
                {"class": "4th Year", "average": 84},
            ],
        },
    },
    {
        "id": "demo-2",
        "name": "Mumbai Institute of Management",
        "location": "Mumbai, India",
        "dateAnalyzed": "2026-03-01",
        "status": "processing",
        "overallScore": None,
        "campusScore": 85,
    },
]
