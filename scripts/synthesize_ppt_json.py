import os
import json
import sys
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(root_dir, ".env"), override=False)

class Slide(BaseModel):
    title: str
    subtitle: Optional[str] = ""
    bullets: List[str] = Field(default_factory=list)
    quote: Optional[str] = ""
    visual_type: Optional[str] = Field(None, description="One of: 'radar', 'pyramid', 'funnel', 'matrix', 'image'")
    visual_data: Optional[List[str]] = Field(default_factory=list, description="Data for the visual. List of 5 integers (strings) for radar, 3 labels for pyramid, 4 for funnel, or 1 image path for image.")
    layout: str = Field("bullets", description="Layout choice: 'title', 'bullets', 'split', 'chart', 'quote'")

class PresentationData(BaseModel):
    presentation_title: str
    slides: List[Slide]

def synthesize_ppt_json(session_dir, company_name):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    # Load all audit data
    # Load all audit data with graceful fallbacks
    def load_json_safe(filename, default=None):
        path = os.path.join(session_dir, filename)
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return default if default is not None else {}

    ba = load_json_safe("business_analysis.json")
    mi = load_json_safe("market_intelligence.json")
    au = load_json_safe("audit_findings.json")
    na = load_json_safe("strategy_narrative.json")
    
    if not ba and not na:
        print(" [!] Critical Data Missing: Cannot synthesize PPT without Business Analysis or Strategy Narrative.")
        return

    # High-fidelity model for structured strategic output
    model_name = "gpt-4o"
    
    prompt = f"""
    You are an elite Lead Strategist at Traffic Radius. 
    Your task is to synthesize the definitive 15-Slide MASTER PRESENTATION for {company_name}.
    
    TONAL & CONTENT RULES (CRITICAL):
    1. AGENCY-GRADE DETAIL: Each slide must be dense with strategic insight. 
       - 'bullets': Generate 5-7 HIGHLY DETAILED, long-form bullet points (25+ words each).
       - 'subtitle': Generate a powerful, 2-sentence executive summary for the slide header.
    2. NO NUMERIC TIMELINES: ALWAYS use 'Phase 1: Activation', 'Phase 2: Acceleration', 'Phase 3: Authority'.
    3. NO PROJECTED REVENUE: NEVER give specific '$' projections. Use qualitative competitive impact.

    MANDATORY VISUALS (CSS DIAGRAMS):
    You MUST provide 'visual_type' and 'visual_data' for every slide (except 'title' layout):
    - 'radar': 'visual_data' = [SEO, AEO, GEO, UI, Trust] (5 integers as strings, 0-100).
    - 'funnel': 'visual_data' = [Step 1, Step 2, Step 3, Step 4] (4 descriptive labels).
    - 'pyramid': 'visual_data' = [Top Layer, Middle Layer, Bottom Layer] (3 labels).
    - 'matrix': 'visual_data' = [Quad 1, Quad 2, Quad 3, Quad 4, ActiveIndex] (4 labels + 1 index '0'-'3').
    - 'image': 'visual_data' = ['homepage_screenshot.png'] (Use for UI/CRO slides).
    
    MANDATORY SLIDE STRUCTURE (STRICT):
    - Slide 1: **COVER SLIDE** (Layout: 'title').
    - Slide 2: **EXECUTIVE SUMMARY** (Layout: 'bullets', visual_type: 'radar').
    - Slide 3: **STRATEGIC ROADMAP** (Layout: 'bullets', visual_type: 'pyramid').
    - Slides 4-14: Strategic Deep-Dives. Mix 'funnel', 'matrix', 'radar'. Use 'image' (homepage_screenshot.png) for CRO.
    - Slide 15: **PARTNERSHIP & NEXT STEPS** (Layout: 'bullets').
    
    --- DATA CONTEXT ---
    BUSINESS: {json.dumps(ba, indent=2)[:3000]}
    STRATEGY: {json.dumps(na, indent=2)[:4000]}
    
    GENERATE ALL 15 SLIDES. ENSURE VISUAL DIVERSITY VIA CSS DIAGRAMS. NO EMPTY SLIDES.
    """
    
    print(f"Synthesizing 15-Slide Master Deck via {model_name}...")
    completion = client.beta.chat.completions.parse(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a Senior Growth Architect. Your output must be elite, professional, and dense with strategic value."},
            {"role": "user", "content": prompt}
        ],
        response_format=PresentationData,
        temperature=0.4
    )
    
    slides = completion.choices[0].message.parsed.slides
    data = [s.model_dump() for s in slides]
    
    out_path = os.path.join(session_dir, "ppt_slides_data.json")
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f" [+] PPT JSON synthesized: {out_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python synthesize_ppt_json.py <session_dir> <company_name>")
        sys.exit(1)
    synthesize_ppt_json(sys.argv[1], sys.argv[2])
