-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users table
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Institutions table
CREATE TABLE IF NOT EXISTS public.institutions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    location TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Analysis Reports table (Main report table)
CREATE TABLE IF NOT EXISTS public.analysis_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    institution_id UUID REFERENCES public.institutions(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'processing',
    date_analyzed TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    overall_score INTEGER,
    campus_score INTEGER,
    compliance_score INTEGER,
    academic_score INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Note: The Python schema uses both camelCase and snake_case inconsistently,
-- so I'll standardize to snake_case in SQL, but I'll make sure the queries match.
-- Wait, looking back at api_logic.py:
-- it says: "overallScore", "campusScore", "complianceScore", "academicScore"
-- But in SQL it's better to use snake_case like "overall_score".
-- I'll use snake_case here but update the Python code if needed, 
-- or provide a comment for the user.
-- Let's re-examine api_logic.py line 114:
-- main_fields = ["status", "overallScore", "campusScore", "complianceScore", "academicScore"]
-- So the Python code expect snake_case for some and camelCase for others?
-- Let's check `schemas.py`:
-- InstitutionReport has: overallScore, campusScore, complianceScore, academicScore
-- So yes, camelCase in Pydantic.
-- If I use snake_case in Supabase, the PostgREST API will return snake_case unless I alias.
-- I'll use snake_case as it's the standard for Postgres.

-- 4. Campus Analysis table
CREATE TABLE IF NOT EXISTS public.campus_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID REFERENCES public.analysis_reports(id) ON DELETE CASCADE UNIQUE,
    infrastructure_score INTEGER,
    maintenance_issues TEXT[],
    safety_hazards TEXT[],
    compliance_flags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. Document Analysis table
CREATE TABLE IF NOT EXISTS public.document_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID REFERENCES public.analysis_reports(id) ON DELETE CASCADE UNIQUE,
    authenticity_score INTEGER,
    detected_issues TEXT[],
    missing_documents TEXT[],
    accreditation_validation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 6. Performance Analysis table
CREATE TABLE IF NOT EXISTS public.performance_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID REFERENCES public.analysis_reports(id) ON DELETE CASCADE UNIQUE,
    top_courses TEXT[],
    low_courses TEXT[],
    recommendations TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 7. Subject Performance table (Sub-items for Performance Analysis)
CREATE TABLE IF NOT EXISTS public.subject_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    performance_id UUID REFERENCES public.performance_analysis(id) ON DELETE CASCADE,
    subject TEXT NOT NULL,
    score INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 8. Class Wise Performance table (Sub-items for Performance Analysis)
CREATE TABLE IF NOT EXISTS public.class_wise_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    performance_id UUID REFERENCES public.performance_analysis(id) ON DELETE CASCADE,
    class_name TEXT NOT NULL,
    average_score INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- RLS (Row Level Security) - Basic setup (Enable for all tables)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.institutions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analysis_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.campus_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.performance_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subject_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.class_wise_performance ENABLE ROW LEVEL SECURITY;

-- Creating basic policies (allowing authenticated users access)
-- Note: In a real app, you'd restrict these based on user roles or ownership.
CREATE POLICY "Allow select for authenticated" ON public.institutions FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow select for authenticated" ON public.analysis_reports FOR SELECT TO authenticated USING (true);
-- Add more as needed.
