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
    visual: Optional[str] = Field(None, description="Filename of a chart or visual asset, e.g. 'charts/integrated_scorecard.png'")

class PresentationData(BaseModel):
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
    model_name = "gpt-4o-2024-08-06"
    
    prompt = f"""
    You are an elite Lead Strategist at Traffic Radius. 
    Your task is to synthesize the definitive MASTER PRESENTATION for {company_name}.
    
    TONAL & CONTENT RULES (CRITICAL):
    1. AGENCY-GRADE DETAIL: Each slide must be dense with strategic insight. 
       - 'bullets': Generate 5-7 HIGHLY DETAILED, long-form bullet points (25+ words each).
       - 'subtitle': Generate a powerful, 2-sentence executive summary for the slide header.
    2. NO NUMERIC TIMELINES: NEVER use '90 Day', 'Month 1', or specific day-counts.
       - ALWAYS use 'Phase 1: Activation', 'Phase 2: Acceleration', 'Phase 3: Authority'.
    3. NO PROJECTED NUMBERS: NEVER give specific revenue or traffic projections (e.g. '$500k ROI'). 
       - ALWAYS use competitive impact descriptors (e.g. 'Massive Market Shift', 'Transactional Equity Growth').
    4. POSITIVE & COMMERCIAL: The tone must be exciting and focus on massive opportunities.
    
    --- DATA CONTEXT ---
    BUSINESS: {json.dumps(ba, indent=2)[:2000]}
    MARKET: {json.dumps(mi, indent=2)[:2000]}
    AUDIT: {json.dumps(au, indent=2)[:2000]}
    NARRATIVE: {json.dumps(na, indent=2)[:4000]}
    
    --- AVAILABLE VISUAL ASSETS ---
    - charts/search_demand_by_cluster.png (Use for SEO/Market)
    - charts/competitive_landscape.png (Use for Competitors)
    - charts/integrated_health_score.png (Use for Audit/Score)
    - charts/aeo_readiness_radar.png (Use for AEO/GEO)
    - charts/backlink_authority_gap.png (Use for Authority)
    - output/homepage_screenshot.png (Use for CRO)
    
    GENERATE ALL 15 SLIDES.
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
