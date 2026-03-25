import os
import json
import sys
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(root_dir, ".env"))

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

    prompt = f"""
    You are an elite, Senior Strategic Partner at TrafficRadius. 
    Design a 15-Slide Master Presentation for {company_name}.
    Your goal is to be POSITIVE, EMPOWERING, and COMMERCIAL.
    Use the raw audit data to build a narrative of growth and market dominance.

    SLIDE STRUCTURE REQUIRED:
    1. Cover (Headline)
    2. The Mission (Core business purpose)
    3. The Revenue Opportunity (Linking search to dollars)
    4. Market Performance (Current visibility stats)
    5. Competitive Dominance (Who are the rivals?)
    6. Growth Architecture (3-Layer Strategy)
    7. Technical Core (Lighthouse/Scorecard results)
    8. AEO Focus (Answer Engines like ChatGPT)
    9. GEO Logic (Generative Engine citations)
    10. UX Vision (CRO assessment)
    11. Content Mastery (The money clusters)
    12. Entity Authority (E-A-T signals)
    13. Phase 1 Roadmap (Immediate Growth)
    14. Phase 2 Roadmap (Market Leadership)
    15. Investment Impact (Final Summary)

    AVAILABLE VISUAL ASSETS (Use these filenames only in the 'visual' field):
    --- Dynamic Research Charts (in 'charts/' directory) ---
    - charts/search_demand_by_cluster.png
    - charts/competitive_landscape.png
    - charts/traffic_value_opportunity.png
    - charts/integrated_scorecard.png
    - charts/layer_distribution.png
    - charts/three_layer_overview.png

    --- Strategic Architecture Diagrams (global assets) ---
    - static/ppt_assets/layer_architecture.png (Best for slide 6)

    DATA:
    --- Business ---
    {json.dumps(ba, indent=2)}
    --- Market ---
    {json.dumps(mi, indent=2)}
    --- Audit ---
    {json.dumps(au, indent=2)}
    --- Strategy ---
    {json.dumps(na, indent=2)}

    Return exactly 15 slides. For each slide, choose the most relevant visual asset from the list above. 
    If none fit, use an empty string. Output exactly 15 slides in the JSON format requested.
    """

    print("Synthesizing 15-Slide Master Presentation JSON...")
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an elite business strategist. You create world-class, revenue-focused presentations."},
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
