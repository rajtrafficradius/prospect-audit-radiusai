import os
import json
import sys
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from dotenv import load_dotenv

# Load environment variables
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(root_dir, ".env"), override=False)

sys.path.append(root_dir)
from src.archetypes import get_archetype

class Slide(BaseModel):
    title: str
    subtitle: Optional[str] = ""
    bullets: List[str] = Field(default_factory=list, description="Max 4 items, max 15 words each.")
    takeaway: str = Field(..., description="A bold, 1-sentence strategic takeaway.")
    quote: Optional[str] = ""
    visual_type: Optional[str] = Field(None, description="One of: 'radar', 'pyramid', 'funnel', 'architecture', 'comparison', 'matrix'")
    visual_data: Optional[List[str]] = Field(default_factory=list, description="Data for the visual. List of strings/values.")
    layout: str = Field("split", description="Layout choice: 'split', 'title', 'quote'")
    archetype: Optional[str] = None

class PresentationData(BaseModel):
    presentation_title: str
    slides: List[Slide]

def synthesize_ppt_json(session_dir, company_name):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    def load_json_safe(filename, default=None):
        path = os.path.join(session_dir, filename)
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return default if default is not None else {}

    ba = load_json_safe("business_analysis.json")
    na = load_json_safe("strategy_narrative.json")
    au = load_json_safe("audit_findings.json")

    model_name = "gpt-4o"
    
    prompt = f"""
    You are an elite Growth Architect at Traffic Radius. 
    Synthesize a 15-Slide EXECUTIVE STRATEGY for {company_name}.
    
    TONAL & CONTENT RULES (CRITICAL):
    1. EXECUTIVE BREVITY: This is for a CEO. No paragraphs.
       - 'bullets': Max 4 points. Max 15 words per point. Use punchy, execution-style language.
       - 'takeaway': One bold, high-impact sentence that summarizes the "So What?" of the slide.
    2. NARRATIVE FLOW: 
       - Cover/Hook → Challenge → Evidence (Audit) → Strategy (SEO/GEO/AEO) → ROI/Outcome.
    3. EXCLUSIVELY ORGANIC: 100% Organic strategy. Exclude all Paid/Ads/PPC.

    V14 VISUAL FRAMEWORKS:
    Every slide (except title) MUST have a 'visual_type':
    - 'funnel': [Awareness, Consideration, Answer, Conversion] (4 labels).
    - 'architecture': [Foundation, Visibility, Authority] (3 layers).
    - 'radar': [SEO, AEO, GEO, Trust, Speed] (5 scores 0-100).
    - 'comparison': [Current State, Target State] (2 descriptive states).
    - 'matrix': [Low Impact, High Noise, Strategic Core, Growth Lever, 2] (4 quad names + ActiveIndex).
    
    --- DATA CONTEXT ---
    BUSINESS: {json.dumps(ba, indent=2)}
    STRATEGY: {json.dumps(na, indent=2)}
    AUDIT: {json.dumps(au, indent=2)}
    """
    
    print(f"Synthesizing v14 Executive Deck via {model_name}...")
    completion = client.beta.chat.completions.parse(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a Senior Growth Architect. Output must be punchy, visual, and high-impact. Avoid all long-form text."},
            {"role": "user", "content": prompt}
        ],
        response_format=PresentationData,
        temperature=0.3
    )
    
    slides = completion.choices[0].message.parsed.slides
    
    # Post-process for V9 Archetypes
    for slide in slides:
        slide.archetype = get_archetype(slide.title)
        
        # Specific Logic for metric_grid mapping
        if slide.archetype == "market_intel_v9":
            # Map the 5 values from radar/general list to the metric grid
            v = slide.visual_data or ["0"] * 5
            slide.visual_data = {
                "val1": str(v[0]), "lbl1": "Authority",
                "val2": str(v[1]) + "%", "lbl2": "AEO Score",
                "val3": str(v[2]), "lbl3": "GEO Citations"
            }
        elif slide.archetype == "competitor_matrix_v9":
            pass

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
