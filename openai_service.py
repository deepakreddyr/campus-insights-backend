import os
import json
import base64
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class OpenAIService:
    @staticmethod
    def encode_image(image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode('utf-8')

    @staticmethod
    def analyze_campus(image_contents: List[bytes]) -> Dict:
        """
        Analyze campus images for infrastructure quality, maintenance, and safety issues.
        """
        base64_images = [OpenAIService.encode_image(img) for img in image_contents]
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": (
                            "You are an expert institutional inspector. Analyze these images of a campus and provide a "
                            "detailed inspection report in JSON format. The JSON should have these keys:\n"
                            "1. infrastructure_score: (integer 0-100)\n"
                            "2. maintenance_issues: (list of strings describing cracks, paint issues, outdated furniture, etc.)\n"
                            "3. safety_hazards: (list of strings describing missing extinguishers, blocked exits, wire hazards, etc.)\n"
                            "4. compliance_flags: (list of strings describing positive compliance items seen, e.g. 'cctv detected', 'clean water station')\n"
                            "Return ONLY the JSON."
                        )
                    },
                    *[
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}}
                        for img in base64_images
                    ]
                ],
            }
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=1000,
        )

        return json.loads(response.choices[0].message.content)

    @staticmethod
    def _detect_file_type(content: bytes) -> str:
        """Detect file type from magic bytes."""
        if content[:4] == b'%PDF':
            return 'pdf'
        if content[:8] in (b'\x89PNG\r\n\x1a\n',):
            return 'png'
        if content[:3] == b'\xff\xd8\xff':
            return 'jpeg'
        if content[:6] in (b'GIF87a', b'GIF89a'):
            return 'gif'
        if content[:4] == b'RIFF' and content[8:12] == b'WEBP':
            return 'webp'
        # Default to treating as text
        return 'text'

    @staticmethod
    def _extract_pdf_text(content: bytes) -> str:
        """Extract text from PDF bytes."""
        try:
            from pypdf import PdfReader
            import io
            reader = PdfReader(io.BytesIO(content))
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text.strip() or "(No readable text found in PDF)"
        except Exception as e:
            return f"(Failed to extract PDF text: {e})"

    @staticmethod
    def analyze_documents(doc_files: List[bytes]) -> Dict:
        """
        Analyze institutional documents. Supports images (Vision) and PDFs/text files.
        - Images (PNG, JPG, GIF, WEBP) → GPT-4o Vision
        - PDFs / text files → text extracted and sent to GPT-4o-mini
        """
        image_bytes_list = []
        text_contents = []

        for content in doc_files:
            file_type = OpenAIService._detect_file_type(content)
            if file_type in ('png', 'jpeg', 'gif', 'webp'):
                image_bytes_list.append(content)
            elif file_type == 'pdf':
                extracted = OpenAIService._extract_pdf_text(content)
                text_contents.append(extracted)
            else:
                # Try to decode as utf-8 text (txt, csv, etc.)
                try:
                    text_contents.append(content.decode('utf-8', errors='ignore'))
                except Exception:
                    text_contents.append("(Unreadable binary file)")

        if image_bytes_list:
            # Use Vision API for image-based documents
            base64_images = [OpenAIService.encode_image(img) for img in image_bytes_list]
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "You are an expert auditor. Analyze these institutional documents "
                                "(certificates, accreditations, etc.) and provide a verification "
                                "report in JSON format with these keys:\n"
                                "1. authenticity_score: (integer 0-100)\n"
                                "2. detected_issues: (list of strings)\n"
                                "3. missing_documents: (list of strings)\n"
                                "4. accreditation_validation: (string summary)\n"
                                "Return ONLY the JSON."
                            )
                        },
                        *[
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}}
                            for img in base64_images
                        ]
                    ],
                }
            ]
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                response_format={"type": "json_object"},
                max_tokens=1000,
            )
        else:
            # Use text API for PDFs and text files
            combined_text = "\n---\n".join(text_contents) if text_contents else "No document content provided."
            prompt = (
                "You are an expert auditor. Analyze the following institutional document text "
                "(extracted from PDF/doc files) and provide a verification report in JSON format "
                "with these keys:\n"
                "1. authenticity_score: (integer 0-100)\n"
                "2. detected_issues: (list of strings, e.g. date mismatches, missing seals)\n"
                "3. missing_documents: (list of strings for likely missing docs)\n"
                "4. accreditation_validation: (string summary of accreditation status)\n"
                "Document Text:\n" + combined_text + "\nReturn ONLY the JSON."
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )

        return json.loads(response.choices[0].message.content)

    @staticmethod
    def analyze_performance(performance_data: str) -> Dict:
        """
        Analyze student performance data and provide recommendations.
        """
        prompt = (
            "Analyze the following student performance data (marks, attendance, course distribution). "
            "Identify trends, top/low performing areas, and provide improvement recommendations.\n\n"
            "Data:\n" + performance_data + "\n\n"
            "Provide a JSON report with keys:\n"
            "1. academicScore: (integer 0-100)\n"
            "2. top_courses: (list of strings)\n"
            "3. low_courses: (list of strings)\n"
            "4. subject_performance: (list of objects with 'subject' and 'score')\n"
            "5. recommendations: (list of strings)\n"
            "6. class_wise_analysis: (list of objects with 'class' and 'average')\n"
            "Return ONLY the JSON."
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        return json.loads(response.choices[0].message.content)
