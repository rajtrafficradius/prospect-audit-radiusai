import os
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

class QualityWin(BaseModel):
    title: str = Field(description="The title of the quick win.")
    description: str = Field(description="Detailed explanation of what needs to be fixed and why.")

class ImpactMatrixItem(BaseModel):
    opportunity: str = Field(description="The specific opportunity or action.")
    expected_outcome: str = Field(description="The expected business outcome.")

class StrategyPillar(BaseModel):
    overview: str = Field(description="A massively detailed, 300-word deep dive into this strategic pillar.")
    key_initiatives: List[str] = Field(description="A list of 4 specific, actionable tactical initiatives (bullet points).")
    impact_matrix: List[ImpactMatrixItem] = Field(description="A list of 3 items detailing the opportunity and its expected outcome.")

class ContentGuidance(BaseModel):
    topic: str = Field(description="The primary topic or cluster.")
    rationale: str = Field(description="A detailed 200-word explanation of why this topic is important based on the data.")
    target_audience_intent: str = Field(description="Detailed analysis of what the searcher wants.")
    recommended_schemas: List[str] = Field(description="List of 3 specific schema types to implement (e.g., FAQPage, HowTo).")
    sub_topics: List[str] = Field(description="List of 4 specific long-tail keywords or sub-topics to cover as H2s.")

class StrategyNarrative(BaseModel):
    executive_summary: str = Field(
        description="A highly customized, aggressive 4-paragraph executive summary detailing the prospect's current position, the massive missed opportunity in the search landscape, and the core value proposition of our agency's intervention."
    )
    company_profile: str = Field(
        description="A highly detailed, 500-word analysis of the prospect's business model, primary services, target audience, and unique value proposition based on the extracted business data."
    )
    digital_maturity_assessment: str = Field(
        description="A highly detailed, 500-word qualitative summary of the prospect's current digital presence, content assets, UI/UX feel, and online visibility across all three search layers (SEO, AEO, GEO)."
    )
    competitive_landscape_analysis: str = Field(
        description="A detailed, 3-paragraph narrative analyzing the competitor data provided in extreme depth, explaining how the prospect is losing traffic value to these specific competitors and how an AEO/GEO approach will outflank them."
    )
    seo_quick_wins: List[QualityWin] = Field(
        description="List of 3 highly specific, actionable quick wins derived from the technical audit data."
    )
    content_strategy_roadmap: List[ContentGuidance] = Field(
        description="List of 3 gigantic, highly specific content clusters/topics to attack based on the keyword data and AEO/GEO gaps."
    )
    integrated_strategy_technical: StrategyPillar = Field(
        description="Pillar 1: Technical Foundation & AI Readiness. What technical changes are required to dominate Search, AEO schemas, and LLM citations."
    )
    integrated_strategy_content: StrategyPillar = Field(
        description="Pillar 2: Content & Answer Optimization. How to structure content to seize Featured Snippets, PAA boxes, and ChatGPT engine responses."
    )
    integrated_strategy_authority: StrategyPillar = Field(
        description="Pillar 3: Authority & Entity Building. Digital PR, backlink strategies, and entity identity reinforcement to win GEO algorithms."
    )

def synthesize_strategy(business_data: dict, market_data: dict, audit_data: dict, rag_db=None) -> dict:
    """
    Uses GPT-4o to synthesize the raw JSON data into a cohesive,
    highly personalized narrative for the final Strategy DOCX.
    """
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    rag_context = ""
    if rag_db is not None:
        try:
            primary_services = business_data.get("primary_services", ["products and services"])
            query = f"What specific details, products, policies, or service offerings are mentioned on the website related to: {', '.join(primary_services)}?"
            results = rag_db.query_knowledge_base(query, top_k=5)
            
            if results:
                rag_context = "--- DEEP SITE KNOWLEDGE (RAG CRAWL) ---\n"
                rag_context += "Use these exact quotes and URLs from the prospect's deep site content to ground your strategy recommendations:\n"
                for res in results:
                    rag_context += f"URL: {res['url']}\nContent: {res['text']}\n\n"
        except Exception as e:
            print(f"RAG Context generation failed: {e}")

    prompt = f"""
    You are an elite, aggressive Senior SEO/AEO Strategist at TrafficRadius.
    You are preparing a final strategy document for a prospect. 
    Review the following raw data extracted from their website, their technical audit, and their SEMrush market intelligence.
    
    Translate this data into a highly bespoke, hard-hitting, extremely detailed long-form narrative.
    Do not use generic fluff. Use the exact competitor names, exact keyword volumes, and exact technical failures found in the data.
    If 'Deep Site Knowledge' is provided, use it to point out highly specific pages or content gaps on their site.
    Make the prospect feel the urgency of the lost opportunity and the brilliance of the proposed AEO/GEO strategy.
    
    CRITICAL INSTRUCTION: Do NOT write short paragraphs. You must write extremely detailed, long-form content. Flesh out every single point with rationale, impact, and strategic foresight. Give it the depth of a premium $10,000 consulting report.
    
    --- BUSINESS DATA ---
    {json.dumps(business_data, indent=2)}
    
    --- MARKET INTELLIGENCE ---
    {json.dumps(market_data, indent=2)}
    
    --- TECHNICAL AUDIT FINDINGS ---
    {json.dumps(audit_data, indent=2)}
    
    {rag_context}
    """
    
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a Senior Technical SEO & Digital Strategist."},
            {"role": "user", "content": prompt}
        ],
        response_format=StrategyNarrative,
        temperature=0.7
    )
    
    return completion.choices[0].message.parsed.model_dump()

if __name__ == "__main__":
    # Local dry-run testing
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    
    # Load dummy data or previous run data
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    with open(os.path.join(output_dir, "business_analysis.json"), "r") as f:
        b_data = json.load(f)
    with open(os.path.join(output_dir, "market_intelligence.json"), "r") as f:
        m_data = json.load(f)
    with open(os.path.join(output_dir, "audit_findings.json"), "r") as f:
        a_data = json.load(f)
        
    # We pass None for local testing unless we want to initialize RAG here too
    result = synthesize_strategy(b_data, m_data, a_data, rag_db=None)
    
    out_path = os.path.join(output_dir, "strategy_narrative.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Narrative synthesized and saved to {out_path}")
