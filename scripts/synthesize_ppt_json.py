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
    visual: Optional[str] = Field(None, description="Filename of a chart or visual asset.")
    layout: str = Field("bullets", description="Layout choice: 'title', 'bullets', 'split', 'chart', 'quote'")

class PresentationData(BaseModel):
    presentation_title: str
    slides: List[Slide]

def synthesize_ppt_json(session_dir, company_name):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    # Load all audit data
    try:
        with open(os.path.join(session_dir, "business_analysis.json")) as f: ba = json.load(f)
        with open(os.path.join(session_dir, "market_intelligence.json")) as f: mi = json.load(f)
        with open(os.path.join(session_dir, "audit_findings.json")) as f: au = json.load(f)
        with open(os.path.join(session_dir, "strategy_narrative.json")) as f: na = json.load(f)
    except Exception as e:
        print(f" [!] Data Loading Error: {e}")
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
    You MUST select one of these 'visual_type' options for every slide (except 'title' layout):
    - 'radar': Use for Audit Scorecards. 'visual_data' = list of 5 scores [SEO, AEO, GEO, UI, Trust] (0-100).
    - 'funnel': Use for Traffic & Conversion flows. 
    - 'pyramid': Use for Strategy Architecture (SEO/AEO/GEO layers).
    - 'matrix': Use for Competitive Positioning.
    - 'image': Use ONLY for 'homepage_screenshot.png' (for UI/CRO slides).
    
    MANDATORY SLIDE STRUCTURE (STRICT):
    - Slide 1: **COVER SLIDE** (Layout: 'title'). Title: '{company_name} Strategic Growth Audit'. Subtitle: 'Proprietary Growth Architecture for Market Dominance'.
    - Slide 2: **EXECUTIVE SUMMARY** (Layout: 'bullets', Visual: 'radar'). Title: 'The Opportunity Landscape'. Subtitle: 'Synthesis of current market inefficiencies vs future authority.'.
    - Slide 3: **STRATEGIC ROADMAP** (Layout: 'bullets', Visual: 'pyramid'). Title: 'Phased Acceleration Framework'. Subtitle: 'Building the foundation for sustainable market leadership.'.
    - Slides 4-14: Strategic Deep-Dives. Mix layouts ('split', 'chart') and visuals ('funnel', 'matrix', 'radar'). Use 'image' (homepage_screenshot.png) sparingly for CRO.
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
