"""
Archetype Registry for Radius AI v9.
Defines the mapping between strategic slide topics and specialized UI components.
"""
from enum import Enum
from typing import List, Dict, Any

class SlideArchetype(Enum):
    TITLE = "title_v9"
    EXECUTIVE_SUMMARY = "exec_summary_v9"
    MARKET_INTEL = "market_intel_v9"
    COMPETITOR_MATRIX = "competitor_matrix_v9"
    GEO_LOCAL_INSIGHT = "geo_local_v9"
    AEO_FLOW = "aeo_flow_v9"
    TECHNICAL_AUDIT = "technical_audit_v9"
    STRATEGY_ROADMAP = "strategy_roadmap_v9"
    CALL_TO_ACTION = "cta_v9"

# Mapping logic: Which archetype to use based on slide title/content
ARCHETYPE_RULES = {
    "Sun City": SlideArchetype.TITLE,
    "Executive Summary": SlideArchetype.EXECUTIVE_SUMMARY,
    "Market Intelligence": SlideArchetype.MARKET_INTEL,
    "Competitive": SlideArchetype.COMPETITOR_MATRIX,
    "GEO": SlideArchetype.GEO_LOCAL_INSIGHT,
    "AEO": SlideArchetype.AEO_FLOW,
    "Technical": SlideArchetype.TECHNICAL_AUDIT,
    "Roadmap": SlideArchetype.STRATEGY_ROADMAP,
    "Partnership": SlideArchetype.CALL_TO_ACTION,
    "Next Steps": SlideArchetype.CALL_TO_ACTION
}

def get_archetype(title: str) -> str:
    for key, archetype in ARCHETYPE_RULES.items():
        if key.lower() in title.lower():
            return archetype.value
    return "generic_v9"
